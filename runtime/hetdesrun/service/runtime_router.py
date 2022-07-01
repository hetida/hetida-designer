# -*- coding: utf-8 -*-
from typing import Optional, Dict
import traceback
import logging

from fastapi import APIRouter

from fastapi.encoders import jsonable_encoder


from hetdesrun import VERSION

from hetdesrun.component.code import update_code, check_parameter_names
from hetdesrun.component.load import check_importability
from hetdesrun.runtime.engine.plain.parsing import (
    parse_workflow_input,
    WorkflowParsingException,
)

from hetdesrun.datatypes import NamedDataTypedValue

from hetdesrun.models.base import VersionInfo
from hetdesrun.models.run import WorkflowExecutionInput, WorkflowExecutionResult
from hetdesrun.models.code import (
    CodeBody,
    GeneratedCode,
    CodeCheckResult,
    ComponentInfo,
)

from hetdesrun.runtime.context import execution_context

from hetdesrun.runtime import RuntimeExecutionError
from hetdesrun.runtime.engine.plain import workflow_execution_plain

from hetdesrun.runtime.engine.plain.workflow import obtain_all_nodes

from hetdesrun.wiring import (
    resolve_and_load_data_from_wiring,
    resolve_and_send_data_from_wiring,
)

from hetdesrun.adapters import AdapterHandlingException

from hetdesrun.utils import model_to_pretty_json_str

from hetdesrun.webservice.auth_dependency import get_auth_deps


logger = logging.getLogger(__name__)


runtime_router = APIRouter(tags=["runtime"])


@runtime_router.post(
    "/runtime",
    response_model=WorkflowExecutionResult,
    dependencies=get_auth_deps(),
)
# pylint: disable=R0911
async def runtime_service(
    runtime_input: WorkflowExecutionInput,
) -> WorkflowExecutionResult:
    logger.info(
        "WORKFLOW EXECUTION INPUT JSON:\n%s",
        model_to_pretty_json_str(runtime_input),
    )

    execution_context.set(runtime_input.configuration)

    # Parse Workflow
    try:
        parsed_wf = parse_workflow_input(
            runtime_input.workflow, runtime_input.components, runtime_input.code_modules
        )
    except WorkflowParsingException as e:
        logger.info(
            "Workflow Parsing Exception during workflow execution", exc_info=True
        )
        return WorkflowExecutionResult(
            result="failure",
            error=str(e),
            traceback=traceback.format_exc(),
            output_results_by_output_name={},
            job_id=runtime_input.job_id,
        )

    # Load data
    try:
        loaded_data = await resolve_and_load_data_from_wiring(
            runtime_input.workflow_wiring
        )
    except AdapterHandlingException as exc:
        logger.info("Adapter Handling Exception during data loading", exc_info=True)
        return WorkflowExecutionResult(
            result="failure",
            error=str(exc),
            traceback=traceback.format_exc(),
            output_results_by_output_name={},
            job_id=runtime_input.job_id,
        )

    wf_inputs_by_name = {inp.name: inp for inp in runtime_input.workflow.inputs}

    constant_providing_data = [
        NamedDataTypedValue(
            name=inp_name, value=loaded_value, type=wf_inputs_by_name[inp_name].type
        )
        for (inp_name, loaded_value) in loaded_data.items()
    ]

    # Provide data as constants
    parsed_wf.add_constant_providing_node(
        constant_providing_data, id_suffix="dynamic_data"
    )

    # run workflow

    all_nodes = obtain_all_nodes(parsed_wf)
    try:
        workflow_result = await workflow_execution_plain(parsed_wf)

        # make sure every computation node result is requested at least once
        # to ensure that every node is run, even if in a part of the graph not leading
        # to a final output. This is necessary for example for the Store Model component.
        for computation_node in all_nodes:

            res = await computation_node.result  # pylint: disable=unused-variable
    except WorkflowParsingException as e:
        logger.info(
            "Workflow Parsing Exception during workflow execution", exc_info=True
        )
        return WorkflowExecutionResult(
            result="failure",
            error=str(e),
            traceback=traceback.format_exc(),
            output_results_by_output_name={},
            job_id=runtime_input.job_id,
        )

    except RuntimeExecutionError as e:
        logger.info(
            "Exception during workflow execution in instance %s of component %s",
            e.currently_executed_node_instance,
            e.currently_executed_component,
            exc_info=True,
        )
        return WorkflowExecutionResult(
            result="failure",
            error=str(e),
            traceback=traceback.format_exc(),
            output_results_by_output_name={},
            job_id=runtime_input.job_id,
        )

    if runtime_input.configuration.return_individual_node_results:
        # prepare individual results
        all_results_str = "\n".join(
            [
                str(x.operator_hierarchical_id) + " " + str(await x.result)
                for x in all_nodes
            ]
        )

        logger.info(
            "Execution Results:\n%s",
            all_results_str
            if len(all_results_str) <= 100
            else (all_results_str[:50] + " ... " + all_results_str[-50:]),
        )

        node_results: Optional[str] = all_results_str
    else:
        node_results = None

    # Send data via wiring to sinks and gather data for direct returning
    try:
        direct_return_data: dict = await resolve_and_send_data_from_wiring(
            runtime_input.workflow_wiring, workflow_result
        )
    except AdapterHandlingException as exc:
        logger.info(
            (
                "Adapter Handling Exception during data sending. "
                "Sending data to external sources may be partly done."
            ),
            exc_info=True,
        )
        return WorkflowExecutionResult(
            result="failure",
            error=str(exc),
            traceback=traceback.format_exc(),
            output_results_by_output_name={},
            job_id=runtime_input.job_id,
        )

    wf_exec_result = WorkflowExecutionResult(
        result="ok",
        node_results=node_results,
        output_results_by_output_name=direct_return_data,
        job_id=runtime_input.job_id,
    )

    logger.info("Workflow Execution Result Pydantic Object: \n%s", wf_exec_result)

    # catch arbitrary serialisation errors
    # (because user can produce arbitrary non-serializable objects)
    try:
        jsonable_encoder(wf_exec_result)
    except Exception as e:  # pylint: disable=broad-except
        logger.info(
            "Exception during workflow execution response serialisation: %s",
            str(e),
            exc_info=True,
        )
        return WorkflowExecutionResult(
            result="failure",
            error=f"Exception during workflow execution response serialisation: {str(e)}",
            traceback=traceback.format_exc(),
            output_results_by_output_id={},
            output_results_by_output_name={},
            job_id=runtime_input.job_id,
        )

    logger.info("Workflow Execution Result serialized successfully.")

    # TODO: avoid double serialization
    return wf_exec_result


@runtime_router.get("/info", response_model=VersionInfo)
async def info_service() -> dict:
    """Version Info Endpoint

    Unauthorized, may be used for readiness probes.
    """
    return {"version": VERSION}


@runtime_router.post(
    "/codegen",
    response_model=GeneratedCode,
    dependencies=get_auth_deps(),
)
async def codegen_service(
    codegen_input: CodeBody,
) -> GeneratedCode:
    """Service for generating and updating code stubs"""
    logger.info("CODEGEN INPUT JSON:\n%s", model_to_pretty_json_str(codegen_input))
    return GeneratedCode(
        code=update_code(
            existing_code=codegen_input.code,
            component_info=ComponentInfo.from_code_body(codegen_input),
        )
    )


@runtime_router.post(
    "/codecheck",
    response_model=CodeCheckResult,
    dependencies=get_auth_deps(),
)
async def codecheck_service(codecheck_input: CodeBody) -> CodeCheckResult:
    """Service for checking code of components"""

    logger.info("CODECHECK INPUT JSON:\n%s", model_to_pretty_json_str(codecheck_input))

    return_dict: Dict[str, Optional[str]] = {}

    result, possible_exception = check_importability(
        codecheck_input.code, codecheck_input.function_name
    )

    inputs_outputs_okay = check_parameter_names(
        [i.name for i in codecheck_input.inputs]
        + [o.name for o in codecheck_input.outputs]
    )

    return_dict = {"result": "ok" if result and inputs_outputs_okay else "failure"}

    if not result:
        return_dict["error"] = (
            str(possible_exception) if possible_exception is not None else None
        )
        return_dict["traceback"] = (
            str(possible_exception.__traceback__)
            if possible_exception is not None
            else None
        )
    elif not inputs_outputs_okay:
        return_dict[
            "error"
        ] = "Inputs/Outputs contain names not satisfying Python identifier rules"

    return CodeCheckResult(**return_dict)

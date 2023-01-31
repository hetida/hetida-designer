import traceback

from fastapi.encoders import jsonable_encoder

from hetdesrun.adapters import AdapterHandlingException
from hetdesrun.datatypes import NamedDataTypedValue
from hetdesrun.models.run import (
    PerformanceMeasuredStep,
    WorkflowExecutionInput,
    WorkflowExecutionResult,
)
from hetdesrun.runtime import RuntimeExecutionError, runtime_logger
from hetdesrun.runtime.configuration import execution_config
from hetdesrun.runtime.engine.plain import workflow_execution_plain
from hetdesrun.runtime.engine.plain.parsing import (
    WorkflowParsingException,
    parse_workflow_input,
)
from hetdesrun.runtime.engine.plain.workflow import obtain_all_nodes
from hetdesrun.runtime.exceptions import WorkflowInputDataValidationError
from hetdesrun.runtime.logging import execution_context_filter, job_id_context_filter
from hetdesrun.utils import model_to_pretty_json_str
from hetdesrun.wiring import (
    resolve_and_load_data_from_wiring,
    resolve_and_send_data_from_wiring,
)

runtime_logger.addFilter(job_id_context_filter)


async def runtime_service(  # pylint: disable=too-many-return-statements,too-many-statements
    runtime_input: WorkflowExecutionInput,
) -> WorkflowExecutionResult:
    """Running stuff with appropriate error handling, serializing etc.

    This function is used by the runtime endpoint
    """

    runtime_service_measured_step = PerformanceMeasuredStep.create_and_begin(
        "runtime_service"
    )

    execution_config.set(runtime_input.configuration)
    execution_context_filter.bind_context(
        currently_executed_job_id=runtime_input.job_id
    )
    job_id_context_filter.bind_context(currently_executed_job_id=runtime_input.job_id)

    runtime_logger.info(
        "WORKFLOW EXECUTION INPUT JSON:\n%s",
        model_to_pretty_json_str(runtime_input),
    )

    # Parse Workflow
    try:
        parsed_wf = parse_workflow_input(
            runtime_input.workflow, runtime_input.components, runtime_input.code_modules
        )
    except (WorkflowParsingException, WorkflowInputDataValidationError) as e:
        runtime_logger.info(
            "Workflow Parsing Exception during workflow execution",
            exc_info=True,
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
        load_data_measured_step = PerformanceMeasuredStep.create_and_begin("load_data")

        loaded_data = await resolve_and_load_data_from_wiring(
            runtime_input.workflow_wiring
        )

        load_data_measured_step.stop()
    except AdapterHandlingException as exc:
        runtime_logger.info(
            "Adapter Handling Exception during data loading",
            exc_info=True,
        )
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
    try:
        parsed_wf.add_constant_providing_node(
            constant_providing_data, id_suffix="dynamic_data"
        )
    except WorkflowInputDataValidationError as exc:
        runtime_logger.info(
            "Input Data Validation Error during data provision",
            exc_info=True,
        )
        return WorkflowExecutionResult(
            result="failure",
            error=str(exc),
            traceback=traceback.format_exc(),
            output_results_by_output_name={},
            job_id=runtime_input.job_id,
        )

    # run workflow

    all_nodes = obtain_all_nodes(parsed_wf)

    pure_execution_measured_step = PerformanceMeasuredStep.create_and_begin(
        "pure_execution"
    )

    try:
        workflow_result = await workflow_execution_plain(parsed_wf)

        # make sure every computation node result is requested at least once
        # to ensure that every node is run, even if in a part of the graph not leading
        # to a final output. This is necessary for example for the Store Model component.
        for computation_node in all_nodes:
            # pylint: disable=unused-variable
            _res = (
                await computation_node.result
                if not (
                    computation_node.has_only_plot_outputs is True
                    and runtime_input.configuration.run_pure_plot_operators is False
                )
                else {}
            )

        pure_execution_measured_step.stop()

    except WorkflowParsingException as e:
        runtime_logger.info(
            "Workflow Parsing Exception during workflow execution",
            exc_info=True,
        )
        return WorkflowExecutionResult(
            result="failure",
            error=str(e),
            traceback=traceback.format_exc(),
            output_results_by_output_name={},
            job_id=runtime_input.job_id,
        )

    except RuntimeExecutionError as e:
        runtime_logger.info(
            "Runtime Execution Error during workflow execution",
            exc_info=True,
        )
        return WorkflowExecutionResult(
            result="failure",
            error=(
                "Exception during execution!\n"
                f"                  tr type: {e.currently_executed_transformation_type},"
                f" tr id: {e.currently_executed_transformation_id},"
                f" tr name: {e.currently_executed_transformation_name},"
                f" tr tag: {e.currently_executed_transformation_tag},\n"
                f"                  op id(s): {e.currently_executed_hierarchical_operator_id},\n"
                f"                  op name(s): {e.currently_executed_hierarchical_operator_name}\n"
                f"                  reason: {e}"
            ),
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

        runtime_logger.info(
            "Execution Results:\n%s",
            all_results_str
            if len(all_results_str) <= 100
            else (all_results_str[:50] + " ... " + all_results_str[-50:]),
        )

        node_results: str | None = all_results_str
    else:
        node_results = None

    # Send data via wiring to sinks and gather data for direct returning
    try:
        send_data_measured_step = PerformanceMeasuredStep.create_and_begin("send_data")

        direct_return_data: dict = await resolve_and_send_data_from_wiring(
            runtime_input.workflow_wiring, workflow_result
        )

        send_data_measured_step.stop()

    except AdapterHandlingException as exc:
        runtime_logger.info(
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

    # attach measured steps
    wf_exec_result.measured_steps.pure_execution = pure_execution_measured_step
    wf_exec_result.measured_steps.load_data = load_data_measured_step
    wf_exec_result.measured_steps.send_data = send_data_measured_step

    runtime_logger.info(
        "Workflow Execution Result Pydantic Object: \n%s",
        wf_exec_result,
    )

    # catch arbitrary serialisation errors
    # (because user can produce arbitrary non-serializable objects)
    try:
        jsonable_encoder(wf_exec_result)
    except Exception as e:  # pylint: disable=broad-except  # noqa: BLE001
        runtime_logger.info(
            "Exception during workflow execution response serialisation: %s",
            str(e),
            exc_info=True,
        )
        return WorkflowExecutionResult(
            result="failure",
            error=(
                f"Exception during workflow execution response serialisation: {str(e)}"
            ),
            traceback=traceback.format_exc(),
            output_results_by_output_id={},
            output_results_by_output_name={},
            job_id=runtime_input.job_id,
        )

    runtime_logger.info("Workflow Execution Result serialized successfully.")

    runtime_service_measured_step.stop()

    wf_exec_result.measured_steps.runtime_service_handling = (
        runtime_service_measured_step
    )

    # TODO: avoid double serialization
    return wf_exec_result

import resource

from pydantic import ValidationError

from hdutils import parsing_not_identical
from hetdesrun.adapters import AdapterHandlingException
from hetdesrun.datatypes import NamedDataTypedValue
from hetdesrun.models.run import (
    PerformanceMeasuredStep,
    ProcessStage,
    RuntimeMemoryInfo,
    UnitTestResults,
    WorkflowExecutionInput,
    WorkflowExecutionResult,
)
from hetdesrun.runtime import (
    ComponentException,
    RuntimeExecutionError,
    UnexpectedComponentException,
    runtime_logger,
)
from hetdesrun.runtime.configuration import execution_config
from hetdesrun.runtime.context import set_runtime_exec_context
from hetdesrun.runtime.engine.plain import workflow_execution_plain
from hetdesrun.runtime.engine.plain.parsing import (
    WorkflowParsingException,
    parse_workflow_input,
)
from hetdesrun.runtime.engine.plain.workflow import Workflow, obtain_all_nodes
from hetdesrun.runtime.exceptions import WorkflowInputDataValidationError
from hetdesrun.runtime.logging import execution_context_filter, job_id_context_filter
from hetdesrun.runtime.reporting import get_data_info
from hetdesrun.runtime.unittesting import unittest_code
from hetdesrun.utils import model_to_pretty_json_str
from hetdesrun.webservice.config import get_config
from hetdesrun.wiring import (
    resolve_and_load_data_from_wiring,
    resolve_and_send_data_from_wiring,
)

runtime_logger.addFilter(job_id_context_filter)


def prepare_runtime_context_bindings(runtime_input: WorkflowExecutionInput) -> None:
    execution_config.set(runtime_input.configuration)
    execution_context_filter.bind_context(currently_executed_job_id=runtime_input.job_id)
    execution_context_filter.bind_context(
        current_code_modules=runtime_input.code_modules,
        current_components=runtime_input.components,
    )
    execution_context_filter.bind_context(plot_target_settings=runtime_input.plot_target_settings)
    set_runtime_exec_context(runtime_input.runtime_execution_context)

    job_id_context_filter.bind_context(
        currently_executed_job_id=runtime_input.job_id,
        root_trafo_id=runtime_input.trafo_id,
    )


async def runtime_service(  # noqa: PLR0911, PLR0912, PLR0915
    runtime_input: WorkflowExecutionInput,
) -> WorkflowExecutionResult:
    """Running stuff with appropriate error handling, serializing, performance measurement etc.

    This function is used by the runtime endpoint, called via a http request from the backend.
    If the service is both backend and runtime, this function will be called directly.
    """

    runtime_service_measured_step = PerformanceMeasuredStep.create_and_begin("RUNTIME_SERVICE")

    with PerformanceMeasuredStep(
        name="RUNTIME_SERVICE_START"
    ) as runtime_service_start_and_wf_parsing_step:
        prepare_runtime_context_bindings(runtime_input)

        # maps to data_types
        inp_name_to_datatype_map = {
            wf_input.name: wf_input.type for wf_input in runtime_input.workflow.inputs
        }
        outp_name_to_datatype_map = {
            wf_output.name: wf_output.type for wf_output in runtime_input.workflow.outputs
        }

        # Logging at runtime service start
        runtime_logger.info(
            ("Starting runtime service execution for: %s (%s) with uuid %s. job id: %s"),
            runtime_input.workflow.tr_name,
            runtime_input.workflow.tr_tag,
            runtime_input.trafo_id,
            runtime_input.job_id,
        )

        if get_config().full_execution_input_logging:
            runtime_logger.debug(
                "FULL WORKFLOW EXECUTION INPUT JSON:\n%s",
                model_to_pretty_json_str(runtime_input),
            )

        memory_at_runtime_service_start_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        runtime_logger.debug(
            "Memory usage at runtime service start (kb): %s (job_id: %s, trafo: %s (%s))",
            str(memory_at_runtime_service_start_kb),
            str(runtime_input.job_id),
            runtime_input.workflow.tr_name,
            runtime_input.workflow.tr_tag,
        )

        currently_executed_process_stage = ProcessStage.PARSING_WORKFLOW

        with PerformanceMeasuredStep(
            name="RUNTIME_SERVICE_PURE_WF_PARSING"
        ) as runtime_service_pure_wf_parsing_step:
            try:
                parsed_wf = parse_workflow_input(
                    runtime_input.workflow, runtime_input.components, runtime_input.code_modules
                )
            except WorkflowParsingException as exc:
                runtime_logger.info(
                    "Workflow Parsing Exception during workflow execution",
                    exc_info=True,
                )
                return WorkflowExecutionResult.from_exception(
                    exc,
                    currently_executed_process_stage,
                    runtime_input.job_id,
                    tr_name=runtime_input.workflow.tr_name,
                    tr_tag=runtime_input.workflow.tr_tag,
                    tr_id=runtime_input.workflow.tr_id,
                )
            except WorkflowInputDataValidationError as exc:
                runtime_logger.info(
                    "Workflow Input Data Validation Exception during workflow execution",
                    exc_info=True,
                )
                return WorkflowExecutionResult.from_exception(
                    exc,
                    currently_executed_process_stage,
                    runtime_input.job_id,
                    tr_name=runtime_input.workflow.tr_name,
                    tr_tag=runtime_input.workflow.tr_tag,
                    tr_id=runtime_input.workflow.tr_id,
                )

    # Load data
    currently_executed_process_stage = ProcessStage.LOADING_DATA_FROM_ADAPTERS

    with PerformanceMeasuredStep(
        name=currently_executed_process_stage.value
    ) as load_data_measured_step:
        try:
            loaded_data = await resolve_and_load_data_from_wiring(runtime_input.workflow_wiring)

        except AdapterHandlingException as exc:
            runtime_logger.info(
                "Adapter Handling Exception during data loading",
                exc_info=True,
            )
            return WorkflowExecutionResult.from_exception(
                exc,
                currently_executed_process_stage,
                runtime_input.job_id,
                tr_name=runtime_input.workflow.tr_name,
                tr_tag=runtime_input.workflow.tr_tag,
                tr_id=runtime_input.workflow.tr_id,
            )

    # Provide data as constants

    currently_executed_process_stage = ProcessStage.PARSE_AND_PROVIDE_DATA_AS_CONSTANTS

    with PerformanceMeasuredStep(
        name="constant_providing_and_preps"
    ) as runtime_service_constant_providing_and_preps_step:
        wf_inputs_by_name = {inp.name: inp for inp in runtime_input.workflow.inputs}

        constant_providing_data = [
            NamedDataTypedValue(
                name=inp_name, value=loaded_value, type=wf_inputs_by_name[inp_name].type
            )
            for (inp_name, loaded_value) in loaded_data.items()
        ]

        currently_executed_process_stage = ProcessStage.PARSING_LOADED_DATA
        try:
            # The `add_constant_providing_node` method also ensures that ultimately the corresponding
            # ComputationNode knows that the input values are to be obtained from this node.
            # Where applicable, the information from the previous addition of the node with the
            # id_suffix "workflow_default_values" is overwritten.

            # Note that optional inputs are considered nullable (i.e. None may arrive).
            # This also activates parsing strings "null" as None (even for string inputs)

            parsed_non_optional_data = parsed_wf.add_constant_providing_node(
                [x for x in constant_providing_data if not wf_inputs_by_name[x["name"]].default],
                id_suffix="dynamic_data",
            )
            parsed_optional_data = parsed_wf.add_constant_providing_node(
                [x for x in constant_providing_data if wf_inputs_by_name[x["name"]].default],
                optional=True,
                id_suffix="dynamic_data_optional",
            )
        except WorkflowInputDataValidationError as exc:
            runtime_logger.info(
                "Input Data Validation Error during data provision",
                exc_info=True,
            )
            return WorkflowExecutionResult.from_exception(
                exc,
                currently_executed_process_stage,
                runtime_input.job_id,
                tr_name=runtime_input.workflow.tr_name,
                tr_tag=runtime_input.workflow.tr_tag,
                tr_id=runtime_input.workflow.tr_id,
            )

        try:
            data_infos = {
                **get_data_info(parsed_non_optional_data, inp_name_to_datatype_map),
                **get_data_info(parsed_optional_data, inp_name_to_datatype_map, optional=True),
            }
        except AdapterHandlingException as exc:
            return WorkflowExecutionResult.from_exception(
                exc,
                currently_executed_process_stage,
                runtime_input.job_id,
                tr_name=runtime_input.workflow.tr_name,
                tr_tag=runtime_input.workflow.tr_tag,
                tr_id=runtime_input.workflow.tr_id,
            )

    # run workflow
    currently_executed_process_stage = ProcessStage.EXECUTING_COMPONENT_CODE

    all_nodes = obtain_all_nodes(parsed_wf)

    try:
        with PerformanceMeasuredStep(
            name=currently_executed_process_stage.value
        ) as pure_execution_measured_step:
            workflow_result = await workflow_execution_plain(parsed_wf)

            # make sure every computation node result is requested at least once
            # to ensure that every node is run, even if in a part of the graph not leading
            # to a final output. This is necessary for example for the Store Model component.
            for computation_node in all_nodes:
                _res = (
                    await computation_node.result
                    if not (
                        computation_node.has_only_plot_outputs is True
                        and runtime_input.configuration.run_pure_plot_operators is False
                    )
                    else {}
                )

    except (ComponentException, UnexpectedComponentException) as exc:
        runtime_logger.info(
            "Component Error during workflow execution",
            exc_info=True,
        )
        return WorkflowExecutionResult.from_exception(
            exc,
            currently_executed_process_stage,
            runtime_input.job_id,
            tr_name=runtime_input.workflow.tr_name,
            tr_tag=runtime_input.workflow.tr_tag,
            tr_id=runtime_input.workflow.tr_id,
            cause=exc.__cause__,
        )

    except RuntimeExecutionError as exc:
        runtime_logger.info(
            "Runtime Execution Error during workflow execution",
            exc_info=True,
        )
        return WorkflowExecutionResult.from_exception(
            exc,
            currently_executed_process_stage,
            runtime_input.job_id,
            tr_name=runtime_input.workflow.tr_name,
            tr_tag=runtime_input.workflow.tr_tag,
            tr_id=runtime_input.workflow.tr_id,
            cause=exc,
        )

    if runtime_input.configuration.return_individual_node_results:
        # prepare individual results
        all_results_str = "\n".join(
            [str(x.operator_hierarchical_id) + " " + str(await x.result) for x in all_nodes]
        )

        runtime_logger.info(
            "Execution Results:\n%s",
            (
                all_results_str
                if len(all_results_str) <= 100
                else (all_results_str[:50] + " ... " + all_results_str[-50:])
            ),
        )

        node_results: str | None = all_results_str
    else:
        node_results = None

    # Ensure result objects have type corresponding to workflow output and are serializable

    # Note: None is always implicitly allowed for every output, so outputs are implicitely nullable.
    #    It is up to adapter implementations to handle None / null values. E.g. the direct provisioning
    #    adapter simply returns them.
    currently_executed_process_stage = ProcessStage.ENSURE_RESULT_PARSABLE_AND_SERIALIZABLE

    try:
        not_identical_result_data_python_types = parsing_not_identical(
            workflow_result, outp_name_to_datatype_map, nullable=True
        )
    except ValidationError as exc:
        runtime_logger.info(
            ("Error during parsing results to ensure serializability of workflow result data:\n"),
            exc_info=True,
        )

        return WorkflowExecutionResult.from_exception(
            exc,
            currently_executed_process_stage,
            runtime_input.job_id,
            tr_name=runtime_input.workflow.tr_name,
            tr_tag=runtime_input.workflow.tr_tag,
            tr_id=runtime_input.workflow.tr_id,
        )

    if len(not_identical_result_data_python_types) > 0:
        msg = f"Uncorrect types for outputs: {str(not_identical_result_data_python_types)}"
        runtime_logger.info(msg)
        return WorkflowExecutionResult.from_exception(
            ValueError(msg),
            currently_executed_process_stage,
            runtime_input.job_id,
            tr_name=runtime_input.workflow.tr_name,
            tr_tag=runtime_input.workflow.tr_tag,
            tr_id=runtime_input.workflow.tr_id,
        )

    result_data_infos = get_data_info(workflow_result, outp_name_to_datatype_map, optional=True)

    # Send data via wiring to sinks and gather data for direct returning
    currently_executed_process_stage = ProcessStage.SENDING_DATA_TO_ADAPTERS
    try:
        with PerformanceMeasuredStep(
            name=currently_executed_process_stage.value
        ) as send_data_measured_step:
            direct_return_data: dict = await resolve_and_send_data_from_wiring(
                runtime_input.workflow_wiring, workflow_result
            )

    except AdapterHandlingException as exc:
        runtime_logger.info(
            (
                "Adapter Handling Exception during data sending. "
                "Sending data to external sources may be partly done."
            ),
            exc_info=True,
        )
        return WorkflowExecutionResult.from_exception(
            exc,
            currently_executed_process_stage,
            runtime_input.job_id,
            tr_name=runtime_input.workflow.tr_name,
            tr_tag=runtime_input.workflow.tr_tag,
            tr_id=runtime_input.workflow.tr_id,
        )

    currently_executed_process_stage = ProcessStage.ENCODING_RESULTS_TO_JSON

    try:
        wf_exec_result = WorkflowExecutionResult(
            result="ok",
            node_results=node_results,
            output_types_by_output_name=outp_name_to_datatype_map,
            output_results_by_output_name=direct_return_data,
            job_id=runtime_input.job_id,
            tr_name=runtime_input.workflow.tr_name,
            tr_tag=runtime_input.workflow.tr_tag,
            tr_id=runtime_input.workflow.tr_id,
        )
    except ValidationError as exc:  # noqa: BLE001
        runtime_logger.info(
            "Pydantic Validation error during workflow execution result parsing/validation: %s",
            str(exc),
            exc_info=True,
        )
        return WorkflowExecutionResult.from_exception(
            exc,
            currently_executed_process_stage,
            runtime_input.job_id,
            tr_name=runtime_input.workflow.tr_name,
            tr_tag=runtime_input.workflow.tr_tag,
            tr_id=runtime_input.workflow.tr_id,
        )

    # attach measured steps
    wf_exec_result.measured_steps.pure_execution = pure_execution_measured_step
    wf_exec_result.measured_steps.load_data = load_data_measured_step
    wf_exec_result.measured_steps.send_data = send_data_measured_step
    wf_exec_result.measured_steps.start_and_wf_parsing = runtime_service_start_and_wf_parsing_step
    wf_exec_result.measured_steps.pure_wf_parsing = runtime_service_pure_wf_parsing_step
    wf_exec_result.measured_steps.constant_providing_and_preps = (
        runtime_service_constant_providing_and_preps_step
    )

    wf_exec_result.measured_steps.loaded_data_info = data_infos
    wf_exec_result.measured_steps.result_data_info = result_data_infos

    runtime_service_measured_step.stop()

    memory_at_runtime_service_end_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    memory_diff_runtime_service_end_minus_start_kb = (
        memory_at_runtime_service_end_kb - memory_at_runtime_service_start_kb
    )
    runtime_logger.debug(
        (
            "Memory usage at runtime service end (success), diff to start (kb, kb):"
            " %s, %s (job_id: %s, trafo: %s (%s))"
        ),
        str(memory_at_runtime_service_end_kb),
        str(memory_diff_runtime_service_end_minus_start_kb),
        str(runtime_input.job_id),
        runtime_input.workflow.tr_name,
        runtime_input.workflow.tr_tag,
    )

    wf_exec_result.measured_steps.runtime_memory_info = RuntimeMemoryInfo(
        kb_at_runtime_start=memory_at_runtime_service_start_kb,
        kb_at_runtime_end=memory_at_runtime_service_end_kb,
        kb_diff_end_minus_start=memory_diff_runtime_service_end_minus_start_kb,
    )

    wf_exec_result.measured_steps.runtime_service_handling = runtime_service_measured_step

    return wf_exec_result


async def unittest_service(component_code: str) -> UnitTestResults:
    return unittest_code(component_code=component_code)

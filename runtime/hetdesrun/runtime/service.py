import resource
from collections import deque
from copy import deepcopy
from typing import cast

import logfire
from pydantic import ValidationError

from hdutils import DataType, parsing_not_identical
from hetdesrun.adapters import AdapterHandlingException
from hetdesrun.component.load import prepare_component_import_context
from hetdesrun.datatypes import NamedDataTypedValue
from hetdesrun.models.run import (
    AllMeasuredSteps,
    ProcessStage,
    RuntimeMemoryInfo,
    UnitTestPayload,
    UnitTestResults,
    WorkflowExecutionInput,
    WorkflowExecutionResult,
)
from hetdesrun.reference_context import set_reproducibility_reference_context
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
from hetdesrun.runtime.engine.plain.workflow import obtain_all_nodes
from hetdesrun.runtime.exceptions import WorkflowInputDataValidationError
from hetdesrun.runtime.logging import (
    _get_execution_context,
    execution_context_filter,
    job_id_context_filter,
    logrecord_to_simplified_log_record,
)
from hetdesrun.runtime.reporting import get_data_info
from hetdesrun.runtime.unittesting import unittest_code
from hetdesrun.utils import model_to_pretty_json_str
from hetdesrun.webservice.config import get_config
from hetdesrun.wiring import (
    resolve_and_load_data_from_wiring,
    resolve_and_send_data_from_wiring,
)

runtime_logger.addFilter(job_id_context_filter)


def prepare_runtime_context_bindings(
    runtime_input: WorkflowExecutionInput, share_component_logs: bool = False
) -> None:
    # make reproducibility reference available during runtime execution
    set_reproducibility_reference_context(runtime_input.reproducibility_reference)

    execution_config.set(runtime_input.configuration)
    component_logs = execution_context_filter.get_value("gathered_component_code_logs")

    # since contextvars are shallo-copied into subtasks, reset them explicitely:
    execution_context_filter.clear_context()
    execution_context_filter.bind_context(currently_executed_job_id=runtime_input.job_id)

    prepare_component_import_context(runtime_input.code_modules, runtime_input.components)
    execution_context_filter.bind_context(
        plot_target_settings=runtime_input.runtime_execution_context.plot_target_settings
    )
    execution_context_filter.bind_context(
        gathered_component_code_logs=component_logs if share_component_logs else []
    )
    set_runtime_exec_context(runtime_input.runtime_execution_context)

    # since contextvars are shallo-copied into subtasks, reset them explicitely:
    job_id_context_filter.clear_context()
    job_id_context_filter.bind_context(
        currently_executed_job_id=runtime_input.job_id,
        root_trafo_id=runtime_input.trafo_id,
    )


def handle_runtime_exec_result_logging(
    wf_exec_result: WorkflowExecutionResult, enforce_result_logging: bool = False
) -> WorkflowExecutionResult:
    # backend always logs the result. We only want to log in the runtime if
    # runtime and backend are separate or in case of component adapter execution
    # (i.e. explicitly enforced)
    if enforce_result_logging or not get_config().is_backend_service:
        runtime_logger.info(
            "Execution Result Response",
            extra={
                "execution_result_response": wf_exec_result.model_dump(
                    mode="json",
                    exclude={"output_results_by_output_name"}
                    if not get_config().log_direct_provisioning_outputs
                    else None,
                )
            },
        )
    return wf_exec_result


def enrich_with_component_code_logs(
    wf_exec_result: WorkflowExecutionResult,
) -> WorkflowExecutionResult:
    exec_context = _get_execution_context()
    if "gathered_component_code_logs" not in exec_context:
        wf_exec_result.gathered_component_code_logs = deque(
            maxlen=get_config().user_component_code_logs_max_len
        )
    else:
        wf_exec_result.gathered_component_code_logs = deque(
            [
                logrecord_to_simplified_log_record(record)
                for record in exec_context["gathered_component_code_logs"]
            ],
            maxlen=get_config().user_component_code_logs_max_len,
        )
    return wf_exec_result


async def runtime_service(  # noqa: PLR0911, PLR0912, PLR0915
    runtime_input: WorkflowExecutionInput,
    enforce_result_logging: bool = False,
    share_component_logs: bool = False,
) -> WorkflowExecutionResult:
    return enrich_with_component_code_logs(
        handle_runtime_exec_result_logging(
            await runtime_service_handling(
                runtime_input, share_component_logs=share_component_logs
            ),
            enforce_result_logging=enforce_result_logging,
        )
    )


async def runtime_service_handling(  # noqa: PLR0911, PLR0912, PLR0915
    runtime_input: WorkflowExecutionInput, share_component_logs: bool = False
) -> WorkflowExecutionResult:
    """Running stuff with appropriate error handling, serializing, performance measurement etc.

    This function is used by the runtime endpoint, called via a http request from the backend.
    If the service is both backend and runtime, this function will be called directly.
    """

    measured_steps = AllMeasuredSteps()

    with logfire.span("RUNTIME_SERVICE"):
        measured_steps.runtime_service_handling.begin()

        with logfire.span("RUNTIME_SERVICE_PURE_WF_PARSING"), measured_steps.start_and_wf_parsing:
            prepare_runtime_context_bindings(
                runtime_input, share_component_logs=share_component_logs
            )

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
                    "FULL RUNTIME WORKFLOW EXECUTION INPUT JSON:\n%s",
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

            with logfire.span("pure_wf_parsing"), measured_steps.pure_wf_parsing:
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
                        measured_steps=measured_steps,
                        mem_info=RuntimeMemoryInfo.complete_now(memory_at_runtime_service_start_kb),
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
                        measured_steps=measured_steps,
                        mem_info=RuntimeMemoryInfo.complete_now(memory_at_runtime_service_start_kb),
                    )

        # Load data
        currently_executed_process_stage = ProcessStage.LOADING_DATA_FROM_ADAPTERS

        with logfire.span("LOADING_DATA_FROM_ADAPTERS"), measured_steps.load_data:
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
                    measured_steps=measured_steps,
                    mem_info=RuntimeMemoryInfo.complete_now(memory_at_runtime_service_start_kb),
                )

        # Provide data as constants

        currently_executed_process_stage = ProcessStage.PARSE_AND_PROVIDE_DATA_AS_CONSTANTS

        with (
            logfire.span("constant_providing_and_preps"),
            measured_steps.constant_providing_and_preps,
        ):
            wf_inputs_by_name = {inp.name: inp for inp in runtime_input.workflow.inputs}

            constant_providing_data = [
                NamedDataTypedValue(
                    name=inp_name, value=loaded_value, type=wf_inputs_by_name[inp_name].type
                )
                for (inp_name, loaded_value) in loaded_data.items()
            ]

            currently_executed_process_stage = ProcessStage.PARSING_LOADED_DATA
            try:
                # The `add_constant_providing_node` method also ensures that ultimately the
                # corresponding ComputationNode knows that the input values are to be obtained from
                # this node.
                # Where applicable, the information from the previous addition of the node with the
                # id_suffix "workflow_default_values" is overwritten.

                # Note that optional inputs are considered nullable (i.e. None may arrive).
                # This also activates parsing strings "null" as None (even for string inputs)

                parsed_non_optional_data = parsed_wf.add_constant_providing_node(
                    [
                        x
                        for x in constant_providing_data
                        if not wf_inputs_by_name[x["name"]].default
                    ],
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
                    measured_steps=measured_steps,
                    mem_info=RuntimeMemoryInfo.complete_now(memory_at_runtime_service_start_kb),
                )

            try:
                measured_steps.loaded_data_info = {
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
                    measured_steps=measured_steps,
                    mem_info=RuntimeMemoryInfo.complete_now(memory_at_runtime_service_start_kb),
                )

        # run workflow
        currently_executed_process_stage = ProcessStage.EXECUTING_COMPONENT_CODE

        all_nodes = obtain_all_nodes(parsed_wf)

        try:
            with logfire.span("EXECUTING_COMPONENT_CODE"), measured_steps.pure_execution:
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
                measured_steps=measured_steps,
                mem_info=RuntimeMemoryInfo.complete_now(memory_at_runtime_service_start_kb),
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
                measured_steps=measured_steps,
                mem_info=RuntimeMemoryInfo.complete_now(memory_at_runtime_service_start_kb),
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

        # Note: None is always implicitly allowed for every output, so outputs are implicitely
        #    nullable.
        #    It is up to adapter implementations to handle None / null values. E.g. the
        #    direct provisioning adapter simply returns them.
        currently_executed_process_stage = ProcessStage.ENSURE_RESULT_PARSABLE_AND_SERIALIZABLE

        try:
            not_identical_result_data_python_types = parsing_not_identical(
                workflow_result, outp_name_to_datatype_map, nullable=True
            )
        except ValidationError as exc:
            runtime_logger.info(
                (
                    "Error during parsing results to ensure serializability of "
                    "workflow result data:\n"
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
                measured_steps=measured_steps,
                mem_info=RuntimeMemoryInfo.complete_now(memory_at_runtime_service_start_kb),
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
                measured_steps=measured_steps,
                mem_info=RuntimeMemoryInfo.complete_now(memory_at_runtime_service_start_kb),
            )

        measured_steps.result_data_info = get_data_info(
            workflow_result,
            cast(dict[str | None, DataType], outp_name_to_datatype_map),
            optional=True,
        )

        # Send data via wiring to sinks and gather data for direct returning
        currently_executed_process_stage = ProcessStage.SENDING_DATA_TO_ADAPTERS
        try:
            with logfire.span("SENDING_DATA_TO_ADAPTERS"), measured_steps.send_data:
                direct_return_data: dict = await resolve_and_send_data_from_wiring(
                    runtime_input.workflow_wiring, workflow_result, runtime_input.workflow.outputs
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
                measured_steps=measured_steps,
                mem_info=RuntimeMemoryInfo.complete_now(memory_at_runtime_service_start_kb),
            )

        currently_executed_process_stage = ProcessStage.ENCODING_RESULTS_TO_JSON

        plot_adapter_corrected_outp_name_to_datatype_map = deepcopy(outp_name_to_datatype_map)

        for outp_wiring in runtime_input.workflow_wiring.output_wirings:
            if outp_wiring.adapter_id == "plot":
                plot_adapter_corrected_outp_name_to_datatype_map[
                    outp_wiring.workflow_output_name
                ] = DataType.PlotlyJson

        try:
            wf_exec_result = WorkflowExecutionResult(
                result="ok",
                node_results=node_results,
                output_types_by_output_name=plot_adapter_corrected_outp_name_to_datatype_map,
                output_results_by_output_name=direct_return_data,
                job_id=runtime_input.job_id,
                tr_name=runtime_input.workflow.tr_name,
                tr_tag=runtime_input.workflow.tr_tag,
                tr_id=runtime_input.workflow.tr_id,
                measured_steps=measured_steps,
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
                measured_steps=measured_steps,
                mem_info=RuntimeMemoryInfo.complete_now(memory_at_runtime_service_start_kb),
            )

        measured_steps.runtime_service_handling.stop()

    mem_info = RuntimeMemoryInfo.complete_now(memory_at_runtime_service_start_kb)

    runtime_logger.debug(
        (
            "Memory usage at runtime service end (success), diff to start (kb, kb):"
            " %s, %s (job_id: %s, trafo: %s (%s))"
        ),
        str(mem_info.kb_at_runtime_end),
        str(mem_info.kb_diff_end_minus_start),
        str(runtime_input.job_id),
        runtime_input.workflow.tr_name,
        runtime_input.workflow.tr_tag,
    )

    wf_exec_result.measured_steps.runtime_memory_info = mem_info

    return wf_exec_result


async def unittest_service(unittest_payload: UnitTestPayload) -> UnitTestResults:
    return unittest_code(
        component_code=unittest_payload.component_code,
        code_modules=unittest_payload.code_modules,
        components=unittest_payload.components,
    )

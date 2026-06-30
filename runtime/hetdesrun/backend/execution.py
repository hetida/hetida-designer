"""Handle execution of transformation revisions."""

import datetime
import logging
import os
from copy import deepcopy
from posixpath import join as posix_urljoin
from uuid import UUID, uuid4

import httpx
import logfire
import msgspec
from pydantic import ValidationError

from hdutils import DataType
from hetdesrun.adapters.component_adapter.validate import (
    validate_sink_trafos_for_component_adapter,
    validate_source_trafos_for_component_adapter,
)
from hetdesrun.adapters.exceptions import AdapterHandlingException
from hetdesrun.adapters.virtual_structure_adapter.resolve_wirings import (
    resolve_virtual_structure_wirings,
)
from hetdesrun.backend.models.info import ExecutionResponseFrontendDto
from hetdesrun.backend.runtime_http_client import get_runtime_http_client
from hetdesrun.component.code_utils import CodeParsingException
from hetdesrun.models.component import ComponentNode
from hetdesrun.models.execution import ExecByIdInput
from hetdesrun.models.run import (
    ConfigurationInput,
    PerformanceMeasuredStep,
    ProcessStage,
    WorkflowExecutionInfo,
    WorkflowExecutionInput,
    WorkflowExecutionResult,
)
from hetdesrun.models.wiring import InputWiring, WorkflowWiring
from hetdesrun.models.workflow import WorkflowNode
from hetdesrun.persistence.dbservice.exceptions import DBIntegrityError, DBNotFoundError
from hetdesrun.persistence.dbservice.revision import (
    get_all_nested_transformation_revisions,
    read_component_imports_recursively,
    read_multiple_transformation_revisions_by_id_with_possible_caching,
    read_single_transformation_revision_with_caching,
)
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.persistence.models.workflow import WorkflowContent
from hetdesrun.reference_context import (
    get_deepcopy_of_reproducibility_reference_context,
    set_reproducibility_reference_context,
)
from hetdesrun.runtime.logging import execution_context_filter
from hetdesrun.runtime.service import runtime_service
from hetdesrun.utils import Type
from hetdesrun.webservice.auth_dependency import get_auth_headers
from hetdesrun.webservice.auth_outgoing import ServiceAuthenticationError
from hetdesrun.webservice.config import get_config
from hetdesrun.webservice.runtime_engine_url import get_runtime_engine_url

logger = logging.getLogger(__name__)
logger.addFilter(execution_context_filter)

UNEXPECTED_RUNTIME_FAILURE_HELP_MESSAGE = """
An "unexpected" error happened while the transformation was executed in
an external runtime service, which lead to no proper response from or
connection loss to the runtime service worker process.

Often such errors
* are caused by what the executed trafo actually does, like using too much memory
* are triggered by a resulting termination of the runtime service worker process,
  e.g. by the server management process, the operating system or the container runtime
  which enforces compliance with resource limits or timeouts.

It is advised to carefully examine whether
* too much data is loaded
* too much data is generated / being output (especially for direct_provisioning outputs!)
* too much memory is used
* cpus are used / blocked for too long
etc. by the executed transformation revision together with the requested wiring.
"""


class TrafoExecutionError(Exception):
    pass


class TrafoExecutionInputValidationError(TrafoExecutionError):
    pass


class TrafoExecutionNotFoundError(TrafoExecutionError):
    pass


class TrafoExecutionComponentImportsLoadingError(TrafoExecutionError):
    """Errors that hapen when loading all imported components recursively"""


class TrafoExecutionComponentImportCycleError(TrafoExecutionError):
    """During resolving component imports a cycle has been detected"""


class TrafoExecutionComponentAdapterComponentsNotFound(TrafoExecutionError):
    """Raised when component sources/sinks cannot be found or validated by the backend

    The backend looks up wired component adapter source / sink components
    when preparing the execution input for the runtime. This is necessary to provide them
    / their code to the runtime.

    Not finding referred components (or failed validating them as proper/suitable
    component adapter sources/sinks) cannot be a AdapterHandlingException, as those
    are thrown and handled by the runtime (and converted to an appropriate error in
    the execution result).

    Hence we need a separate error for this early failure and capture it in the backend's
    trafo execution handling routine.
    """


class TrafoExecutionRuntimeConnectionError(TrafoExecutionError):
    pass


class TrafoExecutionRuntimeHttpStatusError(TrafoExecutionError):
    """Handles the case that external runtime service throws 4xx or 5xx http error"""


class TrafoExecutionRuntimeUnexpectedFailure(TrafoExecutionError):
    """Unexpected error resulting in termination of runtime worker process or similar"""


class TrafoExecutionResultValidationError(TrafoExecutionError):
    pass


def get_direct_child_trafos_by_operator_id(
    tr_workflow: TransformationRevision, all_nested_tr: dict[UUID, TransformationRevision]
) -> dict[UUID, TransformationRevision]:
    """Obtain only the direct children by operator id

    all_nested_tr contains trafos by their id, at least of tr_workflow but
    possibly of a higher workflow which at some depth contains an operator
    with tr_workflow as transformation revision.
    """
    if tr_workflow.type != Type.WORKFLOW:
        raise ValueError("Trafo Revision must be of type WORKFLOW to obtain child trafos.")

    assert isinstance(  # noqa: S101
        tr_workflow.content, WorkflowContent
    )  # hint for mypy

    direct_child_trafos_by_operator_id: dict[UUID, TransformationRevision] = {}
    for operator in tr_workflow.content.operators:
        if operator.transformation_id in all_nested_tr:
            direct_child_trafos_by_operator_id[operator.id] = all_nested_tr[
                operator.transformation_id
            ]
        else:
            raise DBIntegrityError(
                f"trafo {operator.transformation_id} for operator {operator.id} of"
                f" transformation revision {tr_workflow.id}"
                " not contained in result of get_all_nested_transformation_revisions"
            )

    return direct_child_trafos_by_operator_id


def collect_child_nodes(
    workflow: WorkflowContent,
    direct_child_trafos_by_operator_id: dict[UUID, TransformationRevision],
    all_nested_tr: dict[UUID, TransformationRevision],
) -> list[ComponentNode | WorkflowNode]:
    """Recursively build up subnodes

    Returns list of direct subnodes of the WorkflowContent as proper subnodes,
    i.e. each including its own subnodes as well and so on.
    """
    sub_nodes: list[ComponentNode | WorkflowNode] = []

    for operator in workflow.operators:
        if operator.type == Type.COMPONENT:
            sub_nodes.append(
                direct_child_trafos_by_operator_id[operator.id].to_component_node(
                    operator.id, operator.name
                )
            )
        if operator.type == Type.WORKFLOW:
            current_workflow_tr = direct_child_trafos_by_operator_id[operator.id]
            assert isinstance(  # noqa: S101
                current_workflow_tr.content, WorkflowContent
            )  # hint for mypy
            current_child_trafos_by_operator_id = get_direct_child_trafos_by_operator_id(
                current_workflow_tr, all_nested_tr
            )

            sub_nodes.append(
                current_workflow_tr.content.to_workflow_node(
                    transformation_id=all_nested_tr[operator.transformation_id].id,
                    transformation_name=all_nested_tr[operator.transformation_id].name,
                    transformation_tag=all_nested_tr[operator.transformation_id].version_tag,
                    operator_id=operator.id,
                    operator_name=operator.name,
                    sub_nodes=collect_child_nodes(
                        current_workflow_tr.content,
                        current_child_trafos_by_operator_id,
                        all_nested_tr,
                    ),
                )
            )

    return sub_nodes


def nested_nodes(
    tr_workflow: TransformationRevision,
    all_nested_tr: dict[UUID, TransformationRevision],
) -> list[ComponentNode | WorkflowNode]:
    """Get direct subnodes which contain their own subnodes recursively"""
    if tr_workflow.type != Type.WORKFLOW:
        raise ValueError

    assert isinstance(  # noqa: S101
        tr_workflow.content, WorkflowContent
    )  # hint for mypy

    direct_child_trafos_by_operator_id = get_direct_child_trafos_by_operator_id(
        tr_workflow, all_nested_tr
    )

    return collect_child_nodes(
        tr_workflow.content, direct_child_trafos_by_operator_id, all_nested_tr
    )


def get_component_ids_from_component_adapter_wirings(
    wiring: WorkflowWiring,
) -> tuple[list[UUID], list[UUID]]:
    comp_ids_from_inp_wirings = [
        UUID(inp_wiring.ref_id if inp_wiring.ref_key is None else inp_wiring.ref_key)
        for inp_wiring in wiring.input_wirings
        if inp_wiring.adapter_id == "component-adapter"
    ]
    comp_ids_from_outp_wirings = [
        UUID(outp_wiring.ref_id if outp_wiring.ref_key is None else outp_wiring.ref_key)
        for outp_wiring in wiring.output_wirings
        if outp_wiring.adapter_id == "component-adapter"
    ]

    return comp_ids_from_inp_wirings, comp_ids_from_outp_wirings


def load_componen_adapter_wirings_components(
    wiring: WorkflowWiring,
) -> list[TransformationRevision]:
    # Obtain component adapter component ids from wiring
    (
        component_adapter_component_ids_from_input_wirings,
        component_adapter_component_ids_from_output_wirings,
    ) = get_component_ids_from_component_adapter_wirings(wiring) if wiring is not None else ([], [])

    # Load component adapter components
    try:
        component_adapter_source_components = list(
            read_multiple_transformation_revisions_by_id_with_possible_caching(
                component_adapter_component_ids_from_input_wirings
            ).values()
        )
    except DBNotFoundError as e:
        raise TrafoExecutionComponentAdapterComponentsNotFound(
            "Failed to load referenced components for component adapter input wirings from db."
        ) from e

    try:
        component_adapter_sink_components = list(
            read_multiple_transformation_revisions_by_id_with_possible_caching(
                component_adapter_component_ids_from_output_wirings
            ).values()
        )
    except DBNotFoundError as e:
        raise TrafoExecutionComponentAdapterComponentsNotFound(
            "Failed to load referenced components for component adapter output wirings from db."
        ) from e

    # Validate component adapter components

    try:
        validate_source_trafos_for_component_adapter(component_adapter_source_components)
    except ValueError as e:
        raise TrafoExecutionComponentAdapterComponentsNotFound(
            "Failed to validate referenced components for component adapter input wirings"
        ) from e

    try:
        validate_sink_trafos_for_component_adapter(component_adapter_sink_components)
    except ValueError as e:
        raise TrafoExecutionComponentAdapterComponentsNotFound(
            "Failed to validate referenced components for component adapter output wirings"
        ) from e

    component_adapter_components = (
        component_adapter_source_components + component_adapter_sink_components
    )

    return component_adapter_components


def prepare_execution_input(exec_by_id_input: ExecByIdInput) -> WorkflowExecutionInput:
    """Loads trafo revision and prepares execution input from it.

    Loads the trafo revision specified by id and prepares
    an workflow execution input object which can be executed by the runtime
    -- either code or by calling runtime rest endpoint for running
    workflows.

    Note that trafo revisions of type components will be wrapped in
    an ad-hoc workflow structure for execution.
    """

    # Load and prepare trafo to execute, convert to workflow_node

    try:
        transformation_revision = read_single_transformation_revision_with_caching(
            exec_by_id_input.id
        )
        logger.debug(
            "found possibly cached transformation revision with id %s",
            str(exec_by_id_input.id),
        )
    except DBNotFoundError as e:
        raise TrafoExecutionNotFoundError() from e

    if transformation_revision.type == Type.COMPONENT:
        tr_workflow = transformation_revision.wrap_component_in_tr_workflow()
        assert isinstance(  # noqa: S101
            tr_workflow.content, WorkflowContent
        )  # hint for mypy
        nested_transformations = {
            tr_workflow.content.operators[0].transformation_id: transformation_revision
        }
    else:
        tr_workflow = transformation_revision
        nested_transformations = get_all_nested_transformation_revisions(tr_workflow)

    nested_components = {
        tr.id: tr for tr in nested_transformations.values() if tr.type == Type.COMPONENT
    }
    with logfire.span("convert transformation to workflow node"):
        workflow_node = tr_workflow.to_workflow_node(
            operator_id=uuid4(),
            sub_nodes=nested_nodes(tr_workflow, nested_transformations),
        )

    # Handle wiring fallback to test_wiring

    if exec_by_id_input.wiring is None:
        logger.warning("Since no wiring was provided, fall back to test_wiring!")
        wiring_to_use = transformation_revision.test_wiring

    else:
        wiring_to_use = exec_by_id_input.wiring

    # Load component adapter components
    with logfire.span("Load component adapter wiring components"):
        component_adapter_components = load_componen_adapter_wirings_components(wiring_to_use)

    with logfire.span("Resolve and load component imports"):
        # Resolve and load component imports, i.e. components importing components
        try:
            all_imported_components_dict = read_component_imports_recursively(
                list(nested_components.values()) + component_adapter_components
            )
        except DBNotFoundError as e:
            raise TrafoExecutionNotFoundError() from e
        except CodeParsingException as e:
            raise TrafoExecutionComponentImportsLoadingError() from e

    with logfire.span("Gather all components"):
        # Gather all components
        all_components_dict: dict[UUID, TransformationRevision] = {}

        for comp in nested_components.values():
            all_components_dict[comp.id] = comp

        for comp in component_adapter_components:
            all_components_dict[comp.id] = comp

        for comp in all_imported_components_dict.values():
            all_components_dict[comp.id] = comp

    # Build WorkflowExecutionInput and validate everything in combination
    with logfire.span("WorkflowExecutionInput assembling"):
        try:
            execution_input = WorkflowExecutionInput(
                code_modules=list({comp.to_code_module() for comp in all_components_dict.values()}),
                # convert to uniques without using set, since ComponentRevision is not hashable:
                components=list(
                    {
                        (c_rev := comp.to_component_revision()).uuid: c_rev
                        for comp in all_components_dict.values()
                    }.values()
                ),
                workflow=workflow_node,
                configuration=ConfigurationInput(
                    name=str(tr_workflow.id),
                    run_pure_plot_operators=exec_by_id_input.run_pure_plot_operators,
                ),
                workflow_wiring=wiring_to_use,
                job_id=exec_by_id_input.job_id,
                trafo_id=exec_by_id_input.id,
                runtime_execution_context=exec_by_id_input.runtime_execution_context,
                reproducibility_reference=exec_by_id_input.resolved_reproducibility_references,
            )
        except ValidationError as e:
            raise TrafoExecutionInputValidationError(e) from e

    return execution_input


def add_runtime_request_response_reaction_times(
    start_in_backend: datetime.datetime,
    exec_result: ExecutionResponseFrontendDto | WorkflowExecutionResult,
    response_received_time: datetime.datetime | None = None,
) -> None:
    if exec_result.measured_steps.runtime_sending_response_start.start is not None:
        exec_result.measured_steps.runtime_sending_response_start.stop(end=response_received_time)
    if exec_result.measured_steps.backend_calling_runtime_request_start.end is not None:
        exec_result.measured_steps.backend_calling_runtime_request_start.start = start_in_backend
        exec_result.measured_steps.backend_calling_runtime_request_start.duration = (
            exec_result.measured_steps.backend_calling_runtime_request_start.end
            - exec_result.measured_steps.backend_calling_runtime_request_start.start
        )


async def run_execution_input(  # noqa: PLR0915
    execution_input: WorkflowExecutionInput, scheduling_internal: bool = False
) -> ExecutionResponseFrontendDto:
    """Runs the provided execution input

    Depending on configuration this either calls a function or queries the
    external runtime service endpoint (if this instance is not considered to
    act as runtime service).

    Raises subtypes of TrafoExecutionError on errors.
    """
    with logfire.span(
        "run_execution_input", job_id=execution_input.job_id, trafo_id=execution_input.trafo_id
    ):
        run_execution_input_measured_step = PerformanceMeasuredStep.create_and_begin(
            "run_execution_input"
        )
        execution_result: WorkflowExecutionResult

        if get_config().is_runtime_service:
            start_calling_runtime = datetime.datetime.now(datetime.timezone.utc)

            execution_result = await runtime_service(execution_input)

            # measure request / response delays
            add_runtime_request_response_reaction_times(start_calling_runtime, execution_result)
            execution_response = ExecutionResponseFrontendDto.model_construct(
                **dict(execution_result)
            )

        else:
            with logfire.span("Internal Authentication handling"):
                try:
                    headers = await get_auth_headers(
                        external=False, scheduling_internal=scheduling_internal
                    )
                except ServiceAuthenticationError as e:
                    msg = (
                        "Failed to get auth headers for internal runtime execution request."
                        f" Error was:\n{str(e)}"
                    )
                    logger.info(msg)
                    raise TrafoExecutionRuntimeConnectionError(msg) from e

            headers["Accept-Encoding"] = "gzip"
            headers["Content-Type"] = "application/json"

            client = get_runtime_http_client()  # get runtime async httpx client

            url = posix_urljoin(get_runtime_engine_url(), "runtime")
            try:
                with logfire.span("pure_runtime_request"):
                    pure_runtime_request_step = PerformanceMeasuredStep.create_and_begin(
                        "pure_runtime_request"
                    )
                    start_calling_runtime = datetime.datetime.now(datetime.timezone.utc)
                    response = await client.post(
                        url,
                        headers=headers,
                        content=execution_input.model_dump_json(),
                        timeout=None,
                    )
                    response.raise_for_status()
                    response_received_time = datetime.datetime.now(datetime.timezone.utc)
                    logger.debug(
                        "Runtime response content encoding: %s",
                        str(response.headers.get("content-encoding", "n/a")),
                    )

                    pure_runtime_request_step.stop()
            except httpx.HTTPStatusError as e:
                # 4xx and 5xx
                msg = (
                    "HTTPStatusError during runtime execution request for job"
                    f" {execution_input.job_id}: {str(e)}"
                )
                logger.error(msg)
                raise TrafoExecutionRuntimeHttpStatusError(msg) from e

            except httpx.HTTPError as e:
                # handle "unexpected" errors, that
                # * are probably caused by what the executed trafo actually does, like
                #   using too much memory
                # * lead to a temrminated runtime worker process or a state, where the
                #   the runtime cannot properly send a response any more.
                #
                # In this case we do not want to send a Http 500 error back but an actual
                # structured error response that allows the user to review and handle situations
                # probably triggered by their code / workflow or the amount of data
                # requested or produced.
                #
                # Note: Can e.g. be triggered by running os._exit(1) in component code. But a
                # test would of course require separated backend and runtime services and a
                # runtime process management.
                msg = f"Failed runtime execution request to hd runtime endpoint ({url}):\n{str(e)}"
                logger.warning(msg)

                trafo_failure_exc = TrafoExecutionRuntimeUnexpectedFailure(msg)
                trafo_failure_exc.__cause__ = e
                trafo_failure_exc.__traceback__ = e.__traceback__

                wf_exec_info = WorkflowExecutionInfo.from_exception(
                    exception=trafo_failure_exc,
                    process_stage=ProcessStage.UNKNOWN,
                    job_id=execution_input.job_id,
                    tr_name=execution_input.workflow.tr_name,
                    tr_tag=execution_input.workflow.tr_tag,
                    tr_id=execution_input.trafo_id,
                    cause=None,
                    measured_steps=None,
                    mem_info=None,
                )

                wf_exec_info_error = wf_exec_info.error
                assert wf_exec_info_error is not None  # for mypy # noqa: S101

                wf_exec_info_error.message = (
                    UNEXPECTED_RUNTIME_FAILURE_HELP_MESSAGE + f"\n\nThe actual error was:\n{str(e)}"
                )
                execution_response = ExecutionResponseFrontendDto(
                    **(wf_exec_info.model_dump()),
                    result="failure",
                    resolved_reproducibility_references=get_deepcopy_of_reproducibility_reference_context(),
                )

                return execution_response
            try:
                with logfire.span("runtime_request_response_parsing"):
                    runtime_request_response_parsing_step = (
                        PerformanceMeasuredStep.create_and_begin("runtime_request_response_parsing")
                    )

                    json_obj = msgspec.json.decode(
                        response.content
                    )  # use msgspec for json parsing speed instead of response.json()
                    execution_response = ExecutionResponseFrontendDto.model_validate(
                        json_obj, context={"result_validation": False}
                    )
                    add_runtime_request_response_reaction_times(
                        start_calling_runtime,
                        execution_response,
                        response_received_time=response_received_time,
                    )

                    runtime_request_response_parsing_step.stop()

            except ValidationError as e:
                msg = (
                    f"Could not validate hd runtime result object. Exception:\n{str(e)}"
                    f"\nJson Object is:\n{str(json_obj)}"
                )
                logger.info(msg)
                raise TrafoExecutionResultValidationError(msg) from e
            execution_response.measured_steps.runtime_request_response_parsing = (
                runtime_request_response_parsing_step
            )
            execution_response.measured_steps.pure_runtime_request = pure_runtime_request_step

        run_execution_input_measured_step.stop()
    execution_response.measured_steps.run_execution_input = run_execution_input_measured_step

    plot_wired_output_names = {
        outp_wiring.workflow_output_name
        for outp_wiring in execution_input.workflow_wiring.output_wirings
        if outp_wiring.adapter_id == "plot"
    }

    plot_wiring_corrected_output_types_by_output_name = deepcopy(
        execution_response.output_types_by_output_name
    )

    for outp_name in execution_response.output_types_by_output_name:
        if outp_name in plot_wired_output_names:
            plot_wiring_corrected_output_types_by_output_name[outp_name] = DataType.PlotlyJson

    execution_response.output_types_by_output_name = (
        plot_wiring_corrected_output_types_by_output_name
    )

    logger.info(
        "Execution Result Response",
        extra={
            "execution_result_response": execution_response.model_dump(
                mode="json",
                exclude={"output_results_by_output_name"}
                if not get_config().log_direct_provisioning_outputs
                else None,
                context={"naive_result_serialization": not get_config().is_runtime_service},
            )
        },
    )
    return execution_response


def possibly_truncate_filter_value_str(inp_wiring: InputWiring) -> InputWiring:
    """Truncates too long direct_provisioning value filters

    Mutates InputWiring and returns it.
    """
    if (
        inp_wiring.adapter_id in {"direct_provisioning", 1}
        and "value" in inp_wiring.filters
        and isinstance(inp_wiring.filters["value"], str)
        and len(inp_wiring.filters["value"]) > 201
    ):
        inp_wiring.filters["value"] = (
            inp_wiring.filters["value"][:100]
            + f"... ({str(len(inp_wiring.filters['value']) - 200)} characters omitted) ..."
            + inp_wiring.filters["value"][-100:]
        )

    return inp_wiring


def exec_by_id_input_to_stub(exec_by_id_input: ExecByIdInput) -> ExecByIdInput:
    exec_by_id_input_stub = exec_by_id_input.model_copy(deep=True)

    if exec_by_id_input_stub.wiring is None:
        return exec_by_id_input_stub

    exec_by_id_input_stub.wiring.input_wirings = [
        possibly_truncate_filter_value_str(inp_wiring)
        for inp_wiring in exec_by_id_input_stub.wiring.input_wirings
    ]

    return exec_by_id_input_stub


async def execute_transformation_revision(
    exec_by_id_input: ExecByIdInput, scheduling_internal: bool = False
) -> ExecutionResponseFrontendDto:
    """Execute transformation revision

    raises subtypes of TrafoExecutionError on errors.
    """

    if exec_by_id_input.job_id is None:
        exec_by_id_input.job_id = uuid4()

    if get_config().full_backend_exec_input_logging:
        logger.debug(
            "ExecByIdInput:", extra={"exec_by_id_input": exec_by_id_input.model_dump(mode="json")}
        )
    else:
        logger.debug(
            "ExecByIdInput Stub",
            extra={
                "exec_by_id_input_stub": exec_by_id_input_to_stub(exec_by_id_input).model_dump(
                    mode="json"
                )
            },
        )

    execution_context_filter.bind_context(
        job_id=exec_by_id_input.job_id,
        runtime_execution_context=exec_by_id_input.runtime_execution_context,
    )

    # Set the reproducibility reference context to the provided reference of the exec object
    repr_reference = deepcopy(exec_by_id_input.resolved_reproducibility_references)
    set_reproducibility_reference_context(repr_reference)

    # Resolve virtual wirings if necessary
    if exec_by_id_input.wiring:
        try:
            with logfire.span("resolve_virtual_wirings_if_contained"):
                resolve_wirings_measured_step = PerformanceMeasuredStep.create_and_begin(
                    "resolve_virtual_wirings_if_contained"
                )

                resolve_virtual_structure_wirings(exec_by_id_input.wiring)  # modifies wiring!

                if get_config().log_resolved_virtual_structure_wirings:
                    logger.debug(
                        "Resolved virtual structure wirings: \n%s",
                        exec_by_id_input.wiring,
                    )

                resolve_wirings_measured_step.stop()
        except AdapterHandlingException as exc:
            logger.info(
                "Adapter Handling Exception during the resolution of the virtual wirings",
                exc_info=True,
            )
            logger.info(
                "Reproducibility reference contents at time of wiring resolution: %s",
                get_deepcopy_of_reproducibility_reference_context().model_dump(),
            )
            raise TrafoExecutionError() from exc

    # prepare execution input
    with logfire.span("prepare_execution_input"):
        prep_exec_input_measured_step = PerformanceMeasuredStep.create_and_begin(
            "prepare_execution_input"
        )

        execution_input = prepare_execution_input(exec_by_id_input)

        prep_exec_input_measured_step.stop()

    exec_resp_frontend_dto = await run_execution_input(
        execution_input, scheduling_internal=scheduling_internal
    )
    exec_resp_frontend_dto.measured_steps.prepare_execution_input = prep_exec_input_measured_step

    return exec_resp_frontend_dto


async def perf_measured_execute_trafo_rev(
    exec_by_id: ExecByIdInput, scheduling_internal: bool = False
) -> ExecutionResponseFrontendDto:
    """Wraps execution with performance measuring

    Propagates all exceptions (expected: TrafoExecutionError and subclasses).
    """
    with logfire.span("internal_full"):
        internal_full_measured_step = PerformanceMeasuredStep.create_and_begin("internal_full")

        # following line may raise exceptions (TrafoExecutionError and subclasses):
        exec_response = await execute_transformation_revision(
            exec_by_id, scheduling_internal=scheduling_internal
        )

        internal_full_measured_step.stop()
    exec_response.measured_steps.internal_full = internal_full_measured_step
    if get_config().advanced_performance_measurement_active:
        exec_response.process_id = os.getpid()

    if get_config().log_execution_performance_info:
        logger.info(
            "Measured steps for job %s on process with PID %s:\n%s",
            str(exec_response.job_id),
            str(exec_response.process_id),
            str(exec_response.measured_steps),
        )

    return exec_response

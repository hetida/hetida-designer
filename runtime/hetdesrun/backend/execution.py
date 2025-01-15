"""Handle execution of transformation revisions."""

import json
import logging
import os
from copy import deepcopy
from posixpath import join as posix_urljoin
from uuid import UUID, uuid4

import httpx
from pydantic import ValidationError

from hetdesrun.adapters.exceptions import AdapterHandlingException
from hetdesrun.adapters.virtual_structure_adapter.resolve_wirings import (
    resolve_virtual_structure_wirings,
)
from hetdesrun.backend.models.info import ExecutionResponseFrontendDto
from hetdesrun.models.component import ComponentNode
from hetdesrun.models.execution import ExecByIdInput
from hetdesrun.models.run import (
    ConfigurationInput,
    PerformanceMeasuredStep,
    WorkflowExecutionInput,
    WorkflowExecutionResult,
)
from hetdesrun.models.workflow import WorkflowNode
from hetdesrun.persistence.dbservice.exceptions import DBIntegrityError, DBNotFoundError
from hetdesrun.persistence.dbservice.revision import (
    get_all_nested_transformation_revisions,
    read_single_transformation_revision,
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

logger = logging.getLogger(__name__)
logger.addFilter(execution_context_filter)


class TrafoExecutionError(Exception):
    pass


class TrafoExecutionInputValidationError(TrafoExecutionError):
    pass


class TrafoExecutionNotFoundError(TrafoExecutionError):
    pass


class TrafoExecutionRuntimeConnectionError(TrafoExecutionError):
    pass


class TrafoExecutionResultValidationError(TrafoExecutionError):
    pass


def nested_nodes(
    tr_workflow: TransformationRevision,
    all_nested_tr: dict[UUID, TransformationRevision],
) -> list[ComponentNode | WorkflowNode]:
    if tr_workflow.type != Type.WORKFLOW:
        raise ValueError

    assert isinstance(  # noqa: S101
        tr_workflow.content, WorkflowContent
    )  # hint for mypy
    ancestor_operator_ids = [operator.id for operator in tr_workflow.content.operators]
    ancestor_children: dict[UUID, TransformationRevision] = {}
    for operator_id in ancestor_operator_ids:
        if operator_id in all_nested_tr:
            ancestor_children[operator_id] = all_nested_tr[operator_id]
        else:
            raise DBIntegrityError(
                f"operator {operator_id} of transformation revision {tr_workflow.id} "
                f"not contained in result of get_all_nested_transformation_revisions"
            )

    def children_nodes(
        workflow: WorkflowContent, tr_operators: dict[UUID, TransformationRevision]
    ) -> list[ComponentNode | WorkflowNode]:
        sub_nodes: list[ComponentNode | WorkflowNode] = []

        for operator in workflow.operators:
            if operator.type == Type.COMPONENT:
                sub_nodes.append(
                    tr_operators[operator.id].to_component_node(operator.id, operator.name)
                )
            if operator.type == Type.WORKFLOW:
                tr_workflow = tr_operators[operator.id]
                assert isinstance(  # noqa: S101
                    tr_workflow.content, WorkflowContent
                )  # hint for mypy
                operator_ids = [operator.id for operator in tr_workflow.content.operators]
                tr_children = {
                    id_: all_nested_tr[id_] for id_ in operator_ids if id_ in all_nested_tr
                }
                sub_nodes.append(
                    tr_workflow.content.to_workflow_node(
                        transformation_id=all_nested_tr[operator.id].id,
                        transformation_name=all_nested_tr[operator.id].name,
                        transformation_tag=all_nested_tr[operator.id].version_tag,
                        operator_id=operator.id,
                        operator_name=operator.name,
                        sub_nodes=children_nodes(tr_workflow.content, tr_children),
                    )
                )

        return sub_nodes

    return children_nodes(tr_workflow.content, ancestor_children)


def prepare_execution_input(exec_by_id_input: ExecByIdInput) -> WorkflowExecutionInput:
    """Loads trafo revision and prepares execution input from it.

    Loads the trafo revision specified by id and prepares
    an workflow execution input object which can be executed by the runtime
    -- either code or by calling runtime rest endpoint for running
    workflows.

    Note that trafo revisions of type components will be wrapped in
    an ad-hoc workflow structure for execution.
    """
    try:
        if get_config().enable_caching_for_non_draft_trafos_for_execution:
            transformation_revision = read_single_transformation_revision_with_caching(
                exec_by_id_input.id
            )
            logger.info(
                "found possibly cached transformation revision with id %s",
                str(exec_by_id_input.id),
            )
        else:
            transformation_revision = read_single_transformation_revision(exec_by_id_input.id)
            logger.info("found transformation revision with id %s", str(exec_by_id_input.id))
    except DBNotFoundError as e:
        raise TrafoExecutionNotFoundError() from e

    if transformation_revision.type == Type.COMPONENT:
        tr_workflow = transformation_revision.wrap_component_in_tr_workflow()
        assert isinstance(  # noqa: S101
            tr_workflow.content, WorkflowContent
        )  # hint for mypy
        nested_transformations = {tr_workflow.content.operators[0].id: transformation_revision}
    else:
        tr_workflow = transformation_revision
        nested_transformations = get_all_nested_transformation_revisions(tr_workflow)

    nested_components = {
        tr.id: tr for tr in nested_transformations.values() if tr.type == Type.COMPONENT
    }
    workflow_node = tr_workflow.to_workflow_node(
        operator_id=uuid4(),
        sub_nodes=nested_nodes(tr_workflow, nested_transformations),
    )

    try:
        execution_input = WorkflowExecutionInput(
            code_modules=[
                tr_component.to_code_module() for tr_component in nested_components.values()
            ],
            components=[
                component.to_component_revision() for component in nested_components.values()
            ],
            workflow=workflow_node,
            configuration=ConfigurationInput(
                name=str(tr_workflow.id),
                run_pure_plot_operators=exec_by_id_input.run_pure_plot_operators,
            ),
            workflow_wiring=(
                exec_by_id_input.wiring
                if exec_by_id_input.wiring is not None
                else transformation_revision.test_wiring
            ),
            job_id=exec_by_id_input.job_id,
            trafo_id=exec_by_id_input.id,
        )
    except ValidationError as e:
        raise TrafoExecutionInputValidationError(e) from e

    return execution_input


async def run_execution_input(
    execution_input: WorkflowExecutionInput,
) -> ExecutionResponseFrontendDto:
    """Runs the provided execution input

    Depending on configuration this either calls a function or queries the
    external runtime service endpoint (if this instance is not considered to
    act as runtime service).

    Raises subtypes of TrafoExecutionError on errors.
    """
    run_execution_input_measured_step = PerformanceMeasuredStep.create_and_begin(
        "run_execution_input"
    )

    output_types = {output.name: output.type for output in execution_input.workflow.outputs}

    execution_result: WorkflowExecutionResult

    if get_config().is_runtime_service:
        execution_result = await runtime_service(execution_input)
    else:
        try:
            headers = await get_auth_headers(external=False)
        except ServiceAuthenticationError as e:
            msg = (
                "Failed to get auth headers for internal runtime execution request."
                f" Error was:\n{str(e)}"
            )
            logger.info(msg)
            raise TrafoExecutionRuntimeConnectionError(msg) from e

        async with httpx.AsyncClient(
            verify=get_config().hd_runtime_verify_certs,
            timeout=get_config().external_request_timeout,
        ) as client:
            url = posix_urljoin(get_config().hd_runtime_engine_url, "runtime")
            try:
                response = await client.post(
                    url,
                    headers=headers,
                    json=json.loads(execution_input.json()),  # TODO: avoid double serialization.
                    # see https://github.com/samuelcolvin/pydantic/issues/1409 and
                    # https://github.com/samuelcolvin/pydantic/issues/1409#issuecomment-877175194
                    timeout=None,
                )
            except httpx.HTTPError as e:
                # handles both request errors (connection problems)
                # and 4xx and 5xx errors. See https://www.python-httpx.org/exceptions/
                msg = f"Failure connecting to hd runtime endpoint ({url}):\n{str(e)}"
                logger.info(msg)
                raise TrafoExecutionRuntimeConnectionError(msg) from e
            try:
                json_obj = response.json()
                execution_result = WorkflowExecutionResult(**json_obj)
            except ValidationError as e:
                msg = (
                    f"Could not validate hd runtime result object. Exception:\n{str(e)}"
                    f"\nJson Object is:\n{str(json_obj)}"
                )
                logger.info(msg)
                raise TrafoExecutionResultValidationError(msg) from e

    execution_response = ExecutionResponseFrontendDto(
        **execution_result.dict(),
        output_types_by_output_name=output_types,
    )

    run_execution_input_measured_step.stop()

    execution_response.measured_steps.run_execution_input = run_execution_input_measured_step
    return execution_response


async def execute_transformation_revision(
    exec_by_id_input: ExecByIdInput,
) -> ExecutionResponseFrontendDto:
    """Execute transformation revision

    raises subtypes of TrafoExecutionError on errors.
    """

    if exec_by_id_input.job_id is None:
        exec_by_id_input.job_id = uuid4()

    execution_context_filter.bind_context(job_id=exec_by_id_input.job_id)

    # Set the reproducibility reference context to the provided reference of the exec object
    repr_reference = deepcopy(exec_by_id_input.resolved_reproducibility_references)
    set_reproducibility_reference_context(repr_reference)

    # Resolve virtual wirings if necessary
    if exec_by_id_input.wiring:
        try:
            resolve_wirings_measured_step = PerformanceMeasuredStep.create_and_begin(
                "resolve_virtual_wirings_if_contained"
            )
            resolve_virtual_structure_wirings(exec_by_id_input.wiring)
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
                get_deepcopy_of_reproducibility_reference_context().dict(),
            )
            raise TrafoExecutionError() from exc

    # prepare execution input
    prep_exec_input_measured_step = PerformanceMeasuredStep.create_and_begin(
        "prepare_execution_input"
    )

    execution_input = prepare_execution_input(exec_by_id_input)

    prep_exec_input_measured_step.stop()

    exec_resp_frontend_dto = await run_execution_input(execution_input)
    exec_resp_frontend_dto.measured_steps.prepare_execution_input = prep_exec_input_measured_step

    return exec_resp_frontend_dto


async def perf_measured_execute_trafo_rev(
    exec_by_id: ExecByIdInput,
) -> ExecutionResponseFrontendDto:
    """Wraps execution with performance measuring

    Propagates all exceptions (expected: TrafoExecutionError and subclasses).
    """
    internal_full_measured_step = PerformanceMeasuredStep.create_and_begin("internal_full")

    # following line may raise exceptions (TrafoExecutionError and subclasses):
    exec_response = await execute_transformation_revision(exec_by_id)

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

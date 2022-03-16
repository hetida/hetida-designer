from typing import List, Dict, Union
import logging

from uuid import UUID, uuid4

from posixpath import join as posix_urljoin
import httpx
from fastapi import APIRouter, Path, Query, status, HTTPException

from pydantic import ValidationError

from hetdesrun.utils import Type, State, get_auth_headers

from hetdesrun.webservice.config import runtime_config
from hetdesrun.service.runtime_router import runtime_service

from hetdesrun.models.run import (
    ConfigurationInput,
    WorkflowExecutionInput,
    WorkflowExecutionResult,
)

from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.persistence.models.workflow import WorkflowContent

from hetdesrun.persistence.dbservice.revision import (
    read_single_transformation_revision,
    store_single_transformation_revision,
    select_multiple_transformation_revisions,
    update_or_create_single_transformation_revision,
    get_all_nested_transformation_revisions,
)

from hetdesrun.persistence.dbservice.exceptions import DBNotFoundError, DBIntegrityError

from hetdesrun.models.wiring import WorkflowWiring
from hetdesrun.backend.models.info import ExecutionResponseFrontendDto

from hetdesrun.models.workflow import WorkflowNode
from hetdesrun.models.component import ComponentNode
from hetdesrun.models.code import CodeBody
from hetdesrun.component.code import update_code

logger = logging.getLogger(__name__)


transformation_router = APIRouter(
    prefix="/transformations",
    tags=["transformations"],
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized"},
        status.HTTP_403_FORBIDDEN: {"description": "Forbidden"},
        status.HTTP_404_NOT_FOUND: {"description": "Not Found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"},
    },
)


def generate_code(codegen_input: CodeBody) -> str:
    code: str = update_code(
        existing_code=codegen_input.code,
        input_type_dict={c.name: c.type for c in codegen_input.inputs},
        output_type_dict={c.name: c.type for c in codegen_input.outputs},
        component_name=codegen_input.name,
        description=codegen_input.description,
        category=codegen_input.category,
        uuid=codegen_input.uuid,
        group_id=codegen_input.group_id,
        tag=codegen_input.tag,
    )

    return code


def nested_nodes(
    tr_workflow: TransformationRevision,
    all_nested_tr: Dict[UUID, TransformationRevision],
) -> List[Union[ComponentNode, WorkflowNode]]:
    if tr_workflow.type != Type.WORKFLOW:
        raise ValueError

    assert isinstance(tr_workflow.content, WorkflowContent)  # hint for mypy
    ancestor_operator_ids = [operator.id for operator in tr_workflow.content.operators]
    ancestor_children: Dict[UUID, TransformationRevision] = {}
    for operator_id in ancestor_operator_ids:
        if operator_id in all_nested_tr:
            ancestor_children[operator_id] = all_nested_tr[operator_id]
        else:
            raise DBIntegrityError(
                f"operator {operator_id} of transformation revision {tr_workflow.id} "
                f"not contained in result of get_all_nested_transformation_revisions"
            )

    def children_nodes(
        workflow: WorkflowContent, tr_operators: Dict[UUID, TransformationRevision]
    ) -> List[Union[ComponentNode, WorkflowNode]]:
        sub_nodes: List[Union[ComponentNode, WorkflowNode]] = []

        for operator in workflow.operators:
            if operator.type == Type.COMPONENT:
                sub_nodes.append(
                    tr_operators[operator.id].to_component_node(
                        operator.id, operator.name
                    )
                )
            if operator.type == Type.WORKFLOW:
                tr_workflow = tr_operators[operator.id]
                assert isinstance(tr_workflow.content, WorkflowContent)  # hint for mypy
                operator_ids = [
                    operator.id for operator in tr_workflow.content.operators
                ]
                tr_children = {
                    id: all_nested_tr[id] for id in operator_ids if id in all_nested_tr
                }
                sub_nodes.append(
                    tr_workflow.content.to_workflow_node(
                        operator.id,
                        operator.name,
                        children_nodes(tr_workflow.content, tr_children),
                    )
                )

        return sub_nodes

    return children_nodes(tr_workflow.content, ancestor_children)


def contains_deprecated(transformation_id: UUID) -> bool:
    logger.info(
        "check if transformation revision %s contains deprecated operators",
        str(transformation_id),
    )
    transformation_revision = read_single_transformation_revision(transformation_id)

    if transformation_revision.type is not Type.WORKFLOW:
        msg = f"transformation revision {id} is not a workflow!"
        logger.error(msg)
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=msg)

    assert isinstance(transformation_revision.content, WorkflowContent)  # hint for mypy

    is_disabled = []
    for operator in transformation_revision.content.operators:
        logger.info(
            "operator with transformation id %s has status %s",
            str(operator.transformation_id),
            operator.state,
        )
        is_disabled.append(operator.state == State.DISABLED)

    return any(is_disabled)


@transformation_router.post(
    "/",
    response_model=TransformationRevision,
    response_model_exclude_none=True,  # needed because:
    # frontend handles attributes with value null in a different way than missing attributes
    summary="Creates a transformation revision.",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "description": "Successfully created the transformation revision"
        }
    },
)
async def create_transformation_revision(
    transformation_revision: TransformationRevision,
) -> TransformationRevision:
    """Store a transformation revision in the data base."""
    logger.info("create transformation revision %s", transformation_revision.id)

    if transformation_revision.type == Type.COMPONENT:
        logger.debug("transformation revision has type %s", Type.COMPONENT)
        transformation_revision.content = generate_code(
            transformation_revision.to_code_body()
        )
        logger.debug("generated code:\n%s", transformation_revision.content)

    try:
        store_single_transformation_revision(transformation_revision)
        logger.info("created transformation revision")
    except DBIntegrityError as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e

    try:
        persisted_transformation_revision = read_single_transformation_revision(
            transformation_revision.id
        )
    except DBNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e

    logger.debug(persisted_transformation_revision.json())

    return persisted_transformation_revision


@transformation_router.get(
    "/",
    response_model=List[TransformationRevision],
    response_model_exclude_none=True,  # needed because:
    # frontend handles attributes with value null in a different way than missing attributes
    summary="Returns combined list of all transformation revisions (components and workflows)",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "Successfully got all transformation revisions"
        }
    },
)
async def get_all_transformation_revisions() -> List[TransformationRevision]:
    """Get all transformation revisions from the data base.

    Used by frontend for initial loading of all transformations to populate the sidebar.
    """

    logger.info("get all transformation revisions")

    try:
        transformation_revision_list = select_multiple_transformation_revisions()
    except DBIntegrityError as e:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"At least one entry in the DB is no valid transformation revision:\n{str(e)}",
        ) from e

    return transformation_revision_list


@transformation_router.get(
    "/{id}",
    response_model=TransformationRevision,
    response_model_exclude_none=True,  # needed because:
    # frontend handles attributes with value null in a different way than missing attributes
    summary="Returns the transformation revision with the given id.",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "Successfully got the transformation revision"
        }
    },
)
async def get_transformation_revision_by_id(
    # pylint: disable=W0622
    id: UUID = Path(
        ...,
        example=UUID("123e4567-e89b-12d3-a456-426614174000"),
    ),
) -> TransformationRevision:

    logger.info("get transformation revision %s", id)

    try:
        transformation_revision = read_single_transformation_revision(id)
        logger.info("found transformation revision with id %s", id)
    except DBNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e

    logger.debug(transformation_revision.json())

    return transformation_revision


@transformation_router.put(
    "/{id}",
    response_model=TransformationRevision,
    response_model_exclude_none=True,  # needed because:
    # frontend handles attributes with value null in a different way than missing attributes
    summary="Updates basic attributes of a component or workflow.",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "description": "Successfully updated the transformation revision"
        }
    },
)
async def update_transformation_revision(
    # pylint: disable=W0622
    id: UUID,
    updated_transformation_revision: TransformationRevision,
    allow_overwrite_released: bool = Query(
        False, description="Only set to True for deployment"
    ),
) -> TransformationRevision:
    """Update or store a transformation revision in the data base.

    If no DB entry with the provided id is found, it will be created.

    Updating a transformation revision is only possible if it is in state DRAFT
    or to change the state from RELEASED to DISABLED.

    Unset attributes of the json sent in the request body will be set to default values,
    possibly changing the attribute saved in the DB.
    """

    logger.info("update transformation revision %s", id)

    if id != updated_transformation_revision.id:
        msg = (
            f"The id {id} does not match the id of the provided "
            f"transformation revision DTO {updated_transformation_revision.id}"
        )
        logger.error(msg)
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=msg)

    existing_operator_ids: List[UUID] = []

    try:
        existing_transformation_revision = read_single_transformation_revision(
            id, log_error=False
        )
        logger.info("found transformation revision %s", id)

        if (
            existing_transformation_revision.type
            != updated_transformation_revision.type
        ):
            msg = (
                f"The type ({updated_transformation_revision.type}) of the "
                f"provided transformation revision does not\n"
                f"match the type ({existing_transformation_revision.type}) "
                f"of the stored transformation revision {id}!"
            )
            logger.error(msg)
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail=msg)

        if existing_transformation_revision.state == State.DISABLED:
            msg = f"cannot modify deprecated transformation revision {id}"
            logger.error(msg)
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail=msg)

        if existing_transformation_revision.state == State.RELEASED:
            if updated_transformation_revision.state == State.DISABLED:
                logger.info("deprecate transformation revision %s", id)
                # make sure no other changes are made
                updated_transformation_revision = TransformationRevision(
                    **existing_transformation_revision.dict()
                )
                updated_transformation_revision.deprecate()
            elif not allow_overwrite_released:
                msg = f"cannot modify released component {id}"
                logger.error(msg)
                raise HTTPException(status.HTTP_403_FORBIDDEN, detail=msg)

        if updated_transformation_revision.type == Type.COMPONENT:
            updated_transformation_revision.content = generate_code(
                updated_transformation_revision.to_code_body()
            )
        else:
            assert isinstance(
                existing_transformation_revision.content, WorkflowContent
            )  # hint for mypy

            for operator in existing_transformation_revision.content.operators:
                existing_operator_ids.append(operator.id)

        if (
            updated_transformation_revision.state == State.RELEASED
            # avoid updating release date in case overwrite is allowed
            and existing_transformation_revision.state != State.RELEASED
        ):
            logger.info("release transformation revision %s", id)
            updated_transformation_revision.release()

    except DBNotFoundError:
        # base/example workflow deployment needs to be able to put
        # with an id and either create or update the transformation revision
        pass

    if updated_transformation_revision.type == Type.WORKFLOW:
        assert isinstance(
            updated_transformation_revision.content, WorkflowContent
        )  # hint for mypy
        for operator in updated_transformation_revision.content.operators:
            if (
                operator.type == Type.WORKFLOW
                and operator.id not in existing_operator_ids
            ):
                operator.state = (
                    State.DISABLED
                    if contains_deprecated(operator.transformation_id)
                    else operator.state
                )

    try:
        persisted_transformation_revision = (
            update_or_create_single_transformation_revision(
                updated_transformation_revision
            )
        )
        logger.info("updated transformation revision %s", id)
    except DBIntegrityError as e:
        logger.error(
            "integrity error in DB when trying to access entry for id %s\n%s", id, e
        )
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e
    except DBNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e

    logger.debug(persisted_transformation_revision.json())

    return persisted_transformation_revision


@transformation_router.post(
    "/{id}/execute",
    response_model=ExecutionResponseFrontendDto,
    response_model_exclude_none=True,  # needed because:
    # frontend handles attributes with value null in a different way than missing attributes
    summary="Executes a transformation revision",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "Successfully executed the transformation revision"
        }
    },
)
async def execute_transformation_revision(
    # pylint: disable=W0622
    id: UUID,
    wiring: WorkflowWiring,
    run_pure_plot_operators: bool = Query(
        False, description="Set to True by frontent requests to generate plots"
    ),
) -> ExecutionResponseFrontendDto:
    """Execute a transformation revision.

    The transformation will be loaded from the DB and executed with the wiring sent in the request
    body.

    The test wiring will not be updated.
    """

    try:
        transformation_revision = read_single_transformation_revision(id)
        logger.info("found transformation revision with id %s", id)
    except DBNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e

    if transformation_revision.type == Type.COMPONENT:
        tr_workflow = transformation_revision.wrap_component_in_tr_workflow()
    else:
        tr_workflow = transformation_revision

    nested_transformations = get_all_nested_transformation_revisions(tr_workflow)
    nested_components = {
        tr.id: tr for tr in nested_transformations.values() if tr.type == Type.COMPONENT
    }
    workflow_node = tr_workflow.to_workflow_node(
        uuid4(), nested_nodes(tr_workflow, nested_transformations)
    )

    execution_input = WorkflowExecutionInput(
        code_modules=[
            tr_component.to_code_module() for tr_component in nested_components.values()
        ],
        components=[
            component.to_component_revision()
            for component in nested_components.values()
        ],
        workflow=workflow_node,
        configuration=ConfigurationInput(
            name=str(tr_workflow.id),
            run_pure_plot_operators=run_pure_plot_operators,
        ),
        workflow_wiring=wiring,
    )

    output_types = {
        output.name: output.type for output in execution_input.workflow.outputs
    }

    execution_result: WorkflowExecutionResult

    if runtime_config.is_runtime_service:
        execution_result = await runtime_service(execution_input)
    else:
        headers = get_auth_headers()

        async with httpx.AsyncClient(
            verify=runtime_config.hd_runtime_verify_certs
        ) as client:
            url = posix_urljoin(runtime_config.hd_runtime_engine_url, "runtime")
            try:
                response = await client.post(
                    url,
                    headers=headers,  # TODO: authentication
                )
            except httpx.HTTPError as e:
                msg = f"Failure connecting to hd runtime endpoint ({url}):\n{e}"
                logger.info(msg)
                # do not explictly re-raise to avoid displaying authentication details
                # pylint: disable=raise-missing-from
                raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=msg)
            try:
                json_obj = response.json()
                execution_result = WorkflowExecutionResult(**json_obj)
            except ValidationError as e:
                msg = (
                    f"Could not validate hd runtime result object. Exception:\n{str(e)}"
                    f"\nJson Object is:\n{str(json_obj)}"
                )
                logger.info(msg)
                raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=msg) from e

    execution_response = ExecutionResponseFrontendDto(
        error=execution_result.error,
        output_results_by_output_name=execution_result.output_results_by_output_name,
        output_types_by_output_name=output_types,
        result=execution_result.result,
        traceback=execution_result.traceback,
    )

    return execution_response

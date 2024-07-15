import logging
from uuid import UUID

from fastapi import HTTPException, Path, status
from pydantic import ValidationError

from hetdesrun.backend.execution import ExecByIdInput
from hetdesrun.backend.models.info import ExecutionResponseFrontendDto
from hetdesrun.backend.models.wiring import WiringFrontendDto
from hetdesrun.backend.models.workflow import WorkflowRevisionFrontendDto
from hetdesrun.backend.service.transformation_router import (
    handle_trafo_revision_execution_request,
)
from hetdesrun.persistence.dbservice.exceptions import DBIntegrityError, DBNotFoundError
from hetdesrun.persistence.dbservice.revision import (
    delete_single_transformation_revision,
    get_multiple_transformation_revisions,
    read_single_transformation_revision,
    store_single_transformation_revision,
    update_or_create_single_transformation_revision,
)
from hetdesrun.persistence.models.exceptions import ModelConstraintViolation
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.trafoutils.filter.params import FilterParams
from hetdesrun.utils import Type
from hetdesrun.webservice.router import HandleTrailingSlashAPIRouter

logger = logging.getLogger(__name__)


workflow_router = HandleTrailingSlashAPIRouter(
    prefix="/workflows",
    tags=["workflows"],
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized"},
        status.HTTP_404_NOT_FOUND: {"description": "Workflow not found"},
        status.HTTP_409_CONFLICT: {"description": "Conflict"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"},
    },
)


@workflow_router.post(
    "",
    response_model=WorkflowRevisionFrontendDto,
    response_model_exclude_none=True,  # needed because:
    # frontend handles attributes with value null in a different way than missing attributes
    summary="Creates a new workflow.",
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_201_CREATED: {"description": "Successfully created the workflow"}},
    deprecated=True,
)
async def create_workflow_revision(
    workflow_dto: WorkflowRevisionFrontendDto,
) -> WorkflowRevisionFrontendDto:
    """Store a transformation revision of type workflow in the data base.

    This endpoint is deprecated and will be removed soon,
    use POST /api/transformations/ instead.
    """

    logger.info("create a new workflow")

    try:
        transformation_revision = workflow_dto.to_transformation_revision(
            documentation=(
                "# New Component/Workflow\n"
                "## Description\n"
                "## Inputs\n"
                "## Outputs\n"
                "## Details\n"
                "## Examples\n"
            )
        )
    except ValidationError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e

    try:
        store_single_transformation_revision(transformation_revision)
        logger.info("created new workflow")
    except DBIntegrityError as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e

    try:
        persisted_transformation_revision = read_single_transformation_revision(
            transformation_revision.id
        )
    except DBNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e

    persisted_workflow_dto = WorkflowRevisionFrontendDto.from_transformation_revision(
        persisted_transformation_revision
    )
    logger.debug(persisted_workflow_dto.json())

    return persisted_workflow_dto


@workflow_router.get(
    "",
    response_model=list[WorkflowRevisionFrontendDto],
    response_model_exclude_none=True,  # needed because:
    # frontend handles attributes with value null in a different way than missing attributes
    summary="Returns a list of all workflows",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_200_OK: {"description": "Successfully got list of workflows"}},
    deprecated=True,
)
async def get_all_workflow_revisions() -> list[WorkflowRevisionFrontendDto]:
    """Get all transformation revisions of type workflow from the data base.

    This endpoint is deprecated and will be removed soon,
    use GET /api/transformations/{id} instead.
    """

    logger.info("get all workflows")

    transformation_revision_list = get_multiple_transformation_revisions(
        FilterParams(type=Type.WORKFLOW, include_dependencies=False)
    )

    logger.info("got all workflows")

    workflow_dto_list = [
        WorkflowRevisionFrontendDto.from_transformation_revision(tr)
        for tr in transformation_revision_list
    ]

    return workflow_dto_list


@workflow_router.get(
    "/{id}",
    response_model=WorkflowRevisionFrontendDto,
    response_model_exclude_none=True,  # needed because:
    # frontend handles attributes with value null in a different way than missing attributes
    summary="Returns the workflow with the given id.",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_200_OK: {"description": "Successfully got the workflow"}},
    deprecated=True,
)
async def get_workflow_revision_by_id(
    id: UUID = Path(  # noqa: A002
        ...,
        examples=[UUID("123e4567-e89b-12d3-a456-426614174000")],
    ),
) -> WorkflowRevisionFrontendDto:
    """Get a single transformation revision of type workflow from the data base.

    This endpoint is deprecated and will be removed soon,
    use GET /api/transformations/{id} instead.
    """

    logger.info("get workflow %s", id)

    try:
        transformation_revision = read_single_transformation_revision(id)
        logger.info("found workflow with id %s", id)
    except DBNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e

    if transformation_revision.type != Type.WORKFLOW:
        msg = f"DB entry for id {id} does not have type {Type.WORKFLOW}"
        logger.error(msg)
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=msg)

    workflow_dto = WorkflowRevisionFrontendDto.from_transformation_revision(transformation_revision)
    logger.debug(workflow_dto.json())

    return workflow_dto


@workflow_router.put(
    "/{id}",
    response_model=WorkflowRevisionFrontendDto,
    response_model_exclude_none=True,  # needed because:
    # frontend handles attributes with value null in a different way than missing attributes
    summary="Updates a workflow.",
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_201_CREATED: {"description": "Successfully updated the workflow"}},
    deprecated=True,
)
async def update_workflow_revision(
    id: UUID,  # noqa: A002
    updated_workflow_dto: WorkflowRevisionFrontendDto,
) -> WorkflowRevisionFrontendDto:
    """Update or store a transformation revision of type workflow in the data base.

    If no DB entry with the provided id is found, it will be created.

    Updating a transformation revision is only possible if it is in state DRAFT
    or to change the state from RELEASED to DISABLED.

    This endpoint is deprecated and will be removed soon,
    use PUT /api/transformations/{id} instead.
    """

    logger.info("update workflow %s", id)

    if id != updated_workflow_dto.id:
        msg = (
            "The id {id} does not match "
            f"the id of the provided workflow revision DTO {updated_workflow_dto.id}"
        )
        logger.error(msg)
        raise HTTPException(status.HTTP_409_CONFLICT, detail=msg)

    try:
        updated_transformation_revision = updated_workflow_dto.to_transformation_revision()
    except ValidationError as e:
        logger.error("The following validation error occured:\n%s", str(e))
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e

    existing_transformation_revision: TransformationRevision | None = None

    try:
        existing_transformation_revision = read_single_transformation_revision(id, log_error=False)
        logger.info("found transformation revision %s", id)
    except DBNotFoundError:
        # base/example workflow deployment needs to be able to put
        # with an id and either create or update the workflow revision
        pass

    if existing_transformation_revision is not None:
        updated_transformation_revision.documentation = (
            existing_transformation_revision.documentation
        )
        updated_transformation_revision.test_wiring = existing_transformation_revision.test_wiring
        updated_transformation_revision.released_timestamp = (
            existing_transformation_revision.released_timestamp
        )

    try:
        persisted_transformation_revision = update_or_create_single_transformation_revision(
            updated_transformation_revision
        )
        logger.info("updated workflow %s", id)
    except DBIntegrityError as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e
    except DBNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except ModelConstraintViolation as e:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(e)) from e

    persisted_workflow_dto = WorkflowRevisionFrontendDto.from_transformation_revision(
        persisted_transformation_revision
    )
    logger.debug(persisted_workflow_dto.json())

    return persisted_workflow_dto


@workflow_router.delete(
    "/{id}",
    summary="Deletes a workflow.",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {"description": "Successfully deleted the workflow"},
        status.HTTP_409_CONFLICT: {"description": "Workflow is already released"},
    },
    deprecated=True,
)
async def delete_workflow_revision(
    id: UUID,  # noqa: A002
) -> None:
    """Delete a transformation revision of type workflow from the data base.

    Deleting a transformation revision is only possible if it is in state DRAFT.

    This endpoint is deprecated and will be removed soon,
    use DELETE /api/transformations/{id} instead.
    """

    logger.info("delete workflow %s", id)

    try:
        delete_single_transformation_revision(id, type=Type.WORKFLOW)
        logger.info("deleted workflow %s", id)

    except ModelConstraintViolation as e:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(e)) from e

    except DBNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@workflow_router.post(
    "/{id}/execute",
    response_model=ExecutionResponseFrontendDto,
    summary="Executes a new workflow.",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_200_OK: {"description": "Successfully executed the workflow"}},
    deprecated=True,
)
async def execute_workflow_revision(
    id: UUID,  # noqa: A002
    wiring_dto: WiringFrontendDto,
    run_pure_plot_operators: bool = False,
    job_id: UUID | None = None,
) -> ExecutionResponseFrontendDto:
    """Execute a transformation revision of type workflow.

    This endpoint is deprecated and will be removed soon,
    use POST /api/transformations/execute instead which uses a new model for the payload.
    """
    if job_id is None:
        exec_by_id = ExecByIdInput(
            id=id,
            wiring=wiring_dto.to_wiring(),
            run_pure_plot_operators=run_pure_plot_operators,
        )
    else:
        exec_by_id = ExecByIdInput(
            id=id,
            wiring=wiring_dto.to_wiring(),
            run_pure_plot_operators=run_pure_plot_operators,
            job_id=job_id,
        )

    return await handle_trafo_revision_execution_request(exec_by_id)


@workflow_router.post(
    "/{id}/wirings",
    response_model=WorkflowRevisionFrontendDto,
    response_model_exclude_none=True,  # needed because:
    # frontend handles attributes with value null in a different way than missing attributes
    summary="Binds a wiring to the workflow.",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "OK"},
        status.HTTP_204_NO_CONTENT: {"description": "Successfully bound the workflow"},
        status.HTTP_409_CONFLICT: {"description": "Wiring is already bound"},
    },
    deprecated=True,
)
async def bind_wiring_to_workflow_revision(
    id: UUID,  # noqa: A002
    wiring_dto: WiringFrontendDto,
) -> WorkflowRevisionFrontendDto:
    """Store or update the test wiring of a transformation revision of type workflow.

    This endpoint is deprecated and will be removed soon,
    use PUT /api/transformations/{id} instead.
    """

    logger.info("bind wiring to workflow %s", id)

    try:
        transformation_revision = read_single_transformation_revision(id)
        logger.info("found workflow with id %s", id)
    except DBNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e

    if transformation_revision.type != Type.WORKFLOW:
        msg = f"DB entry for id {id} does not have type {Type.WORKFLOW}"
        logger.error(msg)
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=msg)

    wiring = wiring_dto.to_wiring()
    transformation_revision.test_wiring = wiring

    try:
        persisted_transformation_revision = update_or_create_single_transformation_revision(
            transformation_revision
        )
        logger.info("bound wiring to workflow %s", id)
    except DBIntegrityError as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e
    except DBNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except ModelConstraintViolation as e:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(e)) from e

    persisted_workflow_dto = WorkflowRevisionFrontendDto.from_transformation_revision(
        persisted_transformation_revision
    )
    logger.debug(persisted_workflow_dto.json())

    return persisted_workflow_dto

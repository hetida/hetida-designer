import logging
from typing import Optional

from uuid import UUID, uuid4
from fastapi import APIRouter, Path, status, HTTPException

from pydantic import ValidationError

from hetdesrun.utils import Type

from hetdesrun.backend.execution import ExecByIdInput
from hetdesrun.backend.service.transformation_router import (
    generate_code,
    check_modifiability,
    update_content,
    if_applicable_release_or_deprecate,
    handle_trafo_revision_execution_request,
)
from hetdesrun.backend.models.component import ComponentRevisionFrontendDto
from hetdesrun.backend.models.wiring import WiringFrontendDto
from hetdesrun.backend.models.info import ExecutionResponseFrontendDto

from hetdesrun.persistence.dbservice.revision import (
    delete_single_transformation_revision,
    read_single_transformation_revision,
    store_single_transformation_revision,
    update_or_create_single_transformation_revision,
)
from hetdesrun.persistence.dbservice.exceptions import (
    DBTypeError,
    DBBadRequestError,
    DBNotFoundError,
    DBIntegrityError,
)
from hetdesrun.persistence.models.transformation import TransformationRevision

logger = logging.getLogger(__name__)


component_router = APIRouter(
    prefix="/components",
    tags=["components"],
    responses={  # are these only used for display in the Swagger UI?
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized"},
        status.HTTP_403_FORBIDDEN: {"description": "Forbidden"},
        status.HTTP_404_NOT_FOUND: {"description": "Component not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"},
    },
)


@component_router.post(
    "/",
    response_model=ComponentRevisionFrontendDto,
    response_model_exclude_none=True,  # needed because:
    # frontend handles attributes with value null in a different way than missing attributes
    summary="Creates a new component.",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {"description": "Successfully created the component"}
    },
    deprecated=True,
)
async def create_component_revision(
    component_dto: ComponentRevisionFrontendDto,
) -> ComponentRevisionFrontendDto:
    """Store a transformation revision of type component in the data base.

    This endpoint is deprecated and will be removed soon,
    use POST /api/transformations/ instead.
    """

    logger.info("create new component")

    try:
        transformation_revision = component_dto.to_transformation_revision(
            documentation=(
                "\n"
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

    logger.debug("generate code")
    transformation_revision.content = generate_code(transformation_revision)
    logger.debug("generated code:\n%s", component_dto.code)

    try:
        store_single_transformation_revision(transformation_revision)
        logger.info("created new component")
    except DBIntegrityError as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e

    persisted_transformation_revision = read_single_transformation_revision(
        transformation_revision.id
    )

    persisted_component_dto = ComponentRevisionFrontendDto.from_transformation_revision(
        persisted_transformation_revision
    )
    logger.debug(persisted_component_dto.json())

    return persisted_component_dto


@component_router.get(
    "/{id}",
    response_model=ComponentRevisionFrontendDto,
    response_model_exclude_none=True,  # needed because:
    # frontend handles attributes with value null in a different way than missing attributes
    summary="Returns the component with the given id.",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_200_OK: {"description": "Successfully got the component"}},
    deprecated=True,
)
async def get_component_revision_by_id(
    # pylint: disable=redefined-builtin
    id: UUID = Path(
        ...,
        example=UUID("123e4567-e89b-12d3-a456-426614174000"),
    ),
) -> ComponentRevisionFrontendDto:
    """Get a single transformation revision of type component from the data base.

    This endpoint is deprecated and will be removed soon,
    use GET /api/transformations/{id} instead.
    """

    logger.info("get component %s", id)

    try:
        transformation_revision = read_single_transformation_revision(id)
        logger.info("found component with id %s", id)
    except DBNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e

    if transformation_revision.type != Type.COMPONENT:
        msg = f"DB entry for id {id} does not have type {Type.COMPONENT}"
        logger.error(msg)
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=msg)

    component_dto = ComponentRevisionFrontendDto.from_transformation_revision(
        transformation_revision
    )
    logger.debug(component_dto.json())

    return component_dto


@component_router.put(
    "/{id}",
    response_model=ComponentRevisionFrontendDto,
    response_model_exclude_none=True,  # needed because:
    # frontend handles attributes with value null in a different way than missing attributes
    summary="Updates a component.",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {"description": "Successfully updated the component"}
    },
    deprecated=True,
)
async def update_component_revision(
    # pylint: disable=redefined-builtin
    id: UUID,
    updated_component_dto: ComponentRevisionFrontendDto,
) -> ComponentRevisionFrontendDto:
    """Update or store a transformation revision of type component in the data base.

    If no DB entry with the provided id is found, it will be created.

    Updating a transformation revision is only possible if it is in state DRAFT
    or to change the state from RELEASED to DISABLED.

    This endpoint is deprecated and will be removed soon,
    use PUT /api/transformations/{id} instead.
    """

    logger.info("update component %s", id)

    if id != updated_component_dto.id:
        msg = (
            f"The id {id} does not match "
            f"the id of the component revision DTO {updated_component_dto.id}"
        )
        logger.error(msg)
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=msg)

    try:
        updated_transformation_revision = (
            updated_component_dto.to_transformation_revision()
        )
    except ValidationError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e

    existing_transformation_revision: Optional[TransformationRevision] = None

    try:
        existing_transformation_revision = read_single_transformation_revision(
            id, log_error=False
        )
        logger.info("found transformation revision %s", id)

        check_modifiability(
            existing_transformation_revision, updated_transformation_revision
        )
    except DBNotFoundError:
        # base/example workflow deployment needs to be able to put
        # with an id and either create or update the component revision
        pass

    if existing_transformation_revision is not None:
        updated_transformation_revision.documentation = (
            existing_transformation_revision.documentation
        )
        updated_transformation_revision.test_wiring = (
            existing_transformation_revision.test_wiring
        )

    updated_transformation_revision = update_content(
        existing_transformation_revision, updated_transformation_revision
    )

    updated_transformation_revision = if_applicable_release_or_deprecate(
        existing_transformation_revision, updated_transformation_revision
    )

    try:
        persisted_transformation_revision = (
            update_or_create_single_transformation_revision(
                updated_transformation_revision
            )
        )
        logger.info("updated component %s", id)
    except DBIntegrityError as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e
    except DBNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e

    persisted_component_dto = ComponentRevisionFrontendDto.from_transformation_revision(
        persisted_transformation_revision
    )
    logger.debug(persisted_component_dto.json())

    return persisted_component_dto


@component_router.delete(
    "/{id}",
    summary="Deletes a component.",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "Successfully deleted the component"
        },
        status.HTTP_403_FORBIDDEN: {"description": "Component is already released"},
    },
    deprecated=True,
)
async def delete_component_revision(
    # pylint: disable=redefined-builtin
    id: UUID,
) -> None:
    """Delete a transformation revision of type component from the data base.

    Deleting a transformation revision is only possible if it is in state DRAFT.

    This endpoint is deprecated and will be removed soon,
    use DELETE /api/transformations/{id} instead.
    """

    logger.info("delete component %s", id)

    try:
        delete_single_transformation_revision(id, type=Type.COMPONENT)
        logger.info("deleted component %s", id)

    except DBTypeError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e

    except DBBadRequestError as e:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=str(e)) from e

    except DBNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@component_router.post(
    "/{id}/execute",
    response_model=ExecutionResponseFrontendDto,
    response_model_exclude_none=True,  # needed because:
    # frontend handles attributes with value null in a different way than missing attributes
    summary="Executes a new component.",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "Successfully executed the component"}
    },
    deprecated=True,
)
async def execute_component_revision(
    # pylint: disable=redefined-builtin
    id: UUID,
    wiring_dto: WiringFrontendDto,
    run_pure_plot_operators: bool = False,
    job_id: Optional[UUID] = None,
) -> ExecutionResponseFrontendDto:
    """Execute a transformation revision of type component.

    This endpoint is deprecated and will be removed soon,
    use POST /api/transformations/{id}/execute instead.
    """
    if job_id is None:
        job_id = uuid4()

    exec_by_id = ExecByIdInput(
        id=id,
        wiring=wiring_dto.to_workflow_wiring(),
        run_pure_plot_operators=run_pure_plot_operators,
        job_id=job_id,
    )

    return await handle_trafo_revision_execution_request(exec_by_id)


@component_router.post(
    "/{id}/wirings",
    response_model=ComponentRevisionFrontendDto,
    response_model_exclude_none=True,  # needed because:
    # frontend handles attributes with value null in a different way than missing attributes
    summary="Binds a wiring to the component.",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "OK"},
        status.HTTP_204_NO_CONTENT: {"description": "Successfully bound the component"},
        status.HTTP_403_FORBIDDEN: {"description": "Wiring is already bound"},
    },
    deprecated=True,
)
async def bind_wiring_to_component_revision(
    # pylint: disable=redefined-builtin
    id: UUID,
    wiring_dto: WiringFrontendDto,
) -> ComponentRevisionFrontendDto:
    """Store or update the test wiring of a transformation revision of type component.

    This endpoint is deprecated and will be removed soon,
    use PUT /api/transformations/{id} instead.
    """

    logger.info("bind wiring to component %s", id)

    try:
        transformation_revision = read_single_transformation_revision(id)
        logger.info("found component with id %s", id)
    except DBNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e

    if transformation_revision.type != Type.COMPONENT:
        msg = f"DB entry for id {id} does not have type {Type.COMPONENT}"
        logger.error(msg)
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=msg)

    wiring = wiring_dto.to_wiring()
    transformation_revision.test_wiring = wiring

    try:
        persisted_transformation_revision = (
            update_or_create_single_transformation_revision(transformation_revision)
        )
        logger.info("bound wiring to component %s", id)
    except DBIntegrityError as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e
    except DBNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e

    persisted_component_dto = ComponentRevisionFrontendDto.from_transformation_revision(
        persisted_transformation_revision
    )
    logger.debug(persisted_component_dto.json())

    return persisted_component_dto

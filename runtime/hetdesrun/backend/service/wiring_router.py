import logging
from uuid import UUID

from fastapi import HTTPException, status

from hetdesrun.backend.models.wiring import WiringFrontendDto
from hetdesrun.persistence.dbservice.exceptions import DBIntegrityError, DBNotFoundError
from hetdesrun.persistence.dbservice.revision import (
    read_single_transformation_revision,
    update_or_create_single_transformation_revision,
)
from hetdesrun.webservice.router import HandleTrailingSlashAPIRouter

logger = logging.getLogger(__name__)


wiring_router = HandleTrailingSlashAPIRouter(
    prefix="/wirings",
    tags=["wirings"],
    responses={  # are these only used for display in the Swagger UI?
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized"},
        status.HTTP_403_FORBIDDEN: {"description": "Forbidden"},
        status.HTTP_404_NOT_FOUND: {"description": "Wiring not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"},
    },
)


@wiring_router.put(
    "/{id}",
    response_model=WiringFrontendDto,
    response_model_exclude_none=True,
    summary="Updates a wiring.",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_201_CREATED: {"description": "Successfully updated the wiring"}},
    deprecated=True,
)
async def update_wiring(
    id: UUID,  # noqa: A002
    updated_wiring_dto: WiringFrontendDto,
) -> WiringFrontendDto:
    """Store or update the test wiring of a transformation revision.

    WARNING: Instead of the id of the wiring use the id of the transformation revision
    as path parameter other wise the request body will be returned without storing it in the DB

    This endpoint is deprecated and will be removed soon,
    use PUT /api/transformations/{id} instead.
    """

    logger.info("update wiring %s", id)

    try:
        transformation_revision = read_single_transformation_revision(id)
    except DBNotFoundError:
        # there is no longer a separate data model for wiring
        # the wiring is saved when it is posted via the workflow/component router
        return updated_wiring_dto

    transformation_revision.test_wiring = updated_wiring_dto.to_wiring()

    try:
        persisted_transformation_revision = update_or_create_single_transformation_revision(
            transformation_revision
        )
        logger.info("updated wiring for item with id %s", id)
    except DBIntegrityError as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e

    persisted_wiring_dto = WiringFrontendDto.from_wiring(
        persisted_transformation_revision.test_wiring, transformation_revision.id
    )
    logger.debug(persisted_wiring_dto.json())

    return persisted_wiring_dto

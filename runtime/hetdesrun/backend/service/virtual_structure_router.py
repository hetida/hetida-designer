import logging
from secrets import compare_digest

from fastapi import HTTPException, Query, status

from hetdesrun.backend.service.maintenance_router import MaintenancePayload
from hetdesrun.structure.db.exceptions import (
    DBAssociationError,
    DBError,
    DBFetchError,
    DBIntegrityError,
    DBNotFoundError,
    DBUpdateError,
)
from hetdesrun.structure.db.structure_service import (
    are_structure_tables_empty,
    delete_structure,
    update_structure,
)
from hetdesrun.structure.models import CompleteStructure
from hetdesrun.webservice.config import get_config
from hetdesrun.webservice.router import HandleTrailingSlashAPIRouter

logger = logging.getLogger(__name__)


virtual_structure_router = HandleTrailingSlashAPIRouter(
    prefix="/structure",
    tags=["structure"],
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized"},
        status.HTTP_404_NOT_FOUND: {"description": "Not Found"},
        status.HTTP_409_CONFLICT: {"description": "Conflict"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"},
    },
)


@virtual_structure_router.put(
    "/update",
    summary="Updates a structure of the virtual structure adapter",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={status.HTTP_204_NO_CONTENT: {"description": "Successfully updated the structure"}},
)
async def update_structure_endpoint(
    maintenance_payload: MaintenancePayload,
    new_structure: CompleteStructure,
    delete_existing_structure: bool = Query(
        True,
        description="Determines whether a potentially existent structure in the database is deleted"
        " ,before inserting the structure provided to the endpoint",
    ),
) -> None:
    """Endpoint to update the structure of the virtual structure adapter.

    For security purposes this endpoint can only be accessed with a maintenance secret.
    """

    configured_maintenance_secret = get_config().maintenance_secret
    assert configured_maintenance_secret is not None  # for mypy # noqa: S101
    secret_str = maintenance_payload.maintenance_secret

    if not compare_digest(
        secret_str.get_secret_value(),
        configured_maintenance_secret.get_secret_value(),
    ):
        logger.error("Maintenance secret check failed")
        raise HTTPException(
            status_code=403,
            detail={"authorization_error": "maintenance secret check failed"},
        )

    logger.info("Starting to update the vst structure via the API endpoint")
    if delete_existing_structure and not are_structure_tables_empty():
        logger.info("Starting to delete existing structure")
        try:
            delete_structure()
        except (DBIntegrityError, DBError) as e:
            logger.error("Structure deletion during an update request failed: %s", e)
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e
    try:
        update_structure(new_structure)
        logger.info("The structure was successfully updated")
    except (DBIntegrityError, DBUpdateError, DBAssociationError, DBFetchError) as e:
        logger.error("Structure update request failed: %s", e)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e
    except DBNotFoundError as e:
        logger.error("Structure update request failed: %s", e)
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e

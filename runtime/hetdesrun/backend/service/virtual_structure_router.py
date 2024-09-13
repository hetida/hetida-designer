import logging

from fastapi import HTTPException, status

from hetdesrun.structure.db.exceptions import (
    DBAssociationError,
    DBFetchError,
    DBIntegrityError,
    DBNotFoundError,
    DBUpdateError,
)
from hetdesrun.structure.models import CompleteStructure
from hetdesrun.structure.structure_service import (
    delete_structure,
    update_structure,
)
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
    new_structure: CompleteStructure, delete_existing_structure: bool = True
) -> None:
    logger.info("Starting to update the vst structure via the API endpoint")
    if delete_existing_structure:
        delete_structure()
    try:
        update_structure(new_structure)
        logger.info("The structure was successfully updated")
    except DBIntegrityError as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e
    except DBNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DBUpdateError as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e
    except DBAssociationError as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e
    except DBFetchError as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e

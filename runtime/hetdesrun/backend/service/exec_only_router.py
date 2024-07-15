import logging

from fastapi import HTTPException, status

from hetdesrun.backend.execution import ExecByIdInput
from hetdesrun.backend.models.info import ExecutionResponseFrontendDto
from hetdesrun.backend.service.transformation_router import (
    handle_trafo_revision_execution_request,
)
from hetdesrun.webservice.config import get_config
from hetdesrun.webservice.router import HandleTrailingSlashAPIRouter

logger = logging.getLogger(__name__)


restricted_transformation_router = HandleTrailingSlashAPIRouter(
    prefix="/transformations",
    tags=["transformations"],
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Bad Request"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized"},
        status.HTTP_404_NOT_FOUND: {"description": "Not Found"},
        status.HTTP_409_CONFLICT: {"description": "Conflict"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"},
    },
)


@restricted_transformation_router.post(
    "/execute",
    response_model=ExecutionResponseFrontendDto,
    summary="Executes a transformation revision",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "Successfully executed the transformation revision"}
    },
)
async def restricted_execute_transformation_revision_endpoint(
    exec_by_id: ExecByIdInput,
) -> ExecutionResponseFrontendDto:
    """Execute a transformation revision in restrict_to_trafo_exec_service mode

    If allowed, the transformation will be loaded from the DB and executed with
    the wiring sent in the request body.

    The test wiring will not be updated.
    """

    if exec_by_id.id not in get_config().restrict_to_trafo_exec_service:
        msg = (
            f"Restricted execution called with a trafo id {str(exec_by_id.id)} which "
            f"is not in the configured set of allowed UUIDs. Aborting."
        )
        logger.warning(msg)
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=msg)

    logger.debug("Restricted execution called with allowed trafo id %s.", str(exec_by_id.id))

    return await handle_trafo_revision_execution_request(exec_by_id)

import logging

from fastapi import APIRouter, status

from hetdesrun import VERSION


logger = logging.getLogger(__name__)


info_router = APIRouter(
    prefix="/info",
    tags=["info"],
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized"},
        status.HTTP_403_FORBIDDEN: {"description": "Forbidden"},
        status.HTTP_404_NOT_FOUND: {"description": "Not Found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"},
    },
)


@info_router.get(
    "/",
    response_model=dict,
    summary="Returns a sign of life",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_200_OK: {"description": "Successfully got a sign of life"}},
)
async def get_info() -> dict:
    """Show readiness and provide version info."""
    logger.info("Get sign of life")
    return {"msg": "Here I am", "version": VERSION}

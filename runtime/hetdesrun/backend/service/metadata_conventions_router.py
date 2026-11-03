import logging

from fastapi import HTTPException, status
from fastapi.concurrency import run_in_threadpool

from hetdesrun.models.metadata_conventions import (
    MetadataCheckResult,
    TimeseriesDataType,
    WrappedTimeseriesData,
    check_wrapped_timeseries_data,
)
from hetdesrun.webservice.router import HandleTrailingSlashAPIRouter

logger = logging.getLogger(__name__)


metadata_conventions_router = HandleTrailingSlashAPIRouter(
    prefix="/metadata-conventions",
    tags=["metadata conventions"],
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"},
    },
)


@metadata_conventions_router.post(
    "/check/{data_type}",
    response_model=MetadataCheckResult,
    summary="Check metadata against the metadata conventions",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "Checked, the result contains the found issues"},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Request is not in the wrapped format of the data type"
        },
    },
)
async def check_metadata_conventions_endpoint(
    data_type: TimeseriesDataType, wrapped_data: WrappedTimeseriesData
) -> MetadataCheckResult:
    """Check metadata and optionally data against the metadata conventions

    Expects the metadata and optionally the data in the wrapped format of the direct provisioning
    adapter. The data is parsed like a direct provisioning input of the data type.

    Violations of the metadata conventions are reported as errors, likely mistakes, e.g. metadata
    not matching the data, as warnings. Their locations refer to the request body, e.g.
    `__metadata__.metrics[0].value_dimensions[1].column` or `__data__` if the data cannot be
    parsed.
    """
    try:
        # in a thread pool, since parsing large data would block the event loop otherwise
        result = await run_in_threadpool(check_wrapped_timeseries_data, data_type, wrapped_data)
    except ValueError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(e)) from e
    logger.info(
        "Checked %s metadata against the metadata conventions: %d issues",
        data_type,
        len(result.issues),
    )
    return result

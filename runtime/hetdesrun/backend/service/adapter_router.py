import logging

from fastapi import HTTPException, status

from hetdesrun.backend.models.adapter import AdapterFrontendDto
from hetdesrun.webservice.config import get_config
from hetdesrun.webservice.router import HandleTrailingSlashAPIRouter

logger = logging.getLogger(__name__)


adapters = get_config().hd_adapters


adapter_router = HandleTrailingSlashAPIRouter(
    prefix="/adapters",
    tags=["adapters"],
    responses={  # are these only used for display in the Swagger UI?
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized"},
        status.HTTP_404_NOT_FOUND: {"description": "Not Found"},
        status.HTTP_409_CONFLICT: {"description": "Conflict"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"},
    },
)


@adapter_router.get(
    "",
    response_model=list[AdapterFrontendDto],
    summary="Returns all adapters",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_200_OK: {"description": "Successfully got list of adapters"}},
)
async def get_all_adapters() -> list[AdapterFrontendDto]:
    """Get all adapters."""
    logger.info("get adapters")
    adapter_list: list[AdapterFrontendDto] = []

    if adapters is None or adapters == "":
        return adapter_list

    for adapter in adapters.split(","):
        adapter_properties = adapter.split("|")

        if len(adapter_properties) != 4:
            msg = (
                "Wrong adapter configuration format - must be "
                '"id|name|url|internalUrl,id2|name2|url2|internalUrl2,..."'
            )
            logger.error(msg)
            raise HTTPException(status.HTTP_409_CONFLICT, detail=msg)

        adapter_list.append(
            AdapterFrontendDto(
                id=adapter_properties[0],
                name=adapter_properties[1],
                url=adapter_properties[2],
                internalUrl=adapter_properties[3],
            )
        )

    return adapter_list

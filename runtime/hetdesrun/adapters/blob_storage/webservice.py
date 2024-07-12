"""Web service endpoints for frontend for the BLOB Storage Adapter

Note that the BLOB Storage Adapter is a General Custom Adapter, so these webendpoints
have the sole purpose to tell the frontend which data sources and sinks are available and
can be wired.

Actual data ingestion/egestion happens in the corresponding Runtime-Python-Plugin of this adapter.
"""

import logging

from fastapi import HTTPException, Query, status

from hetdesrun.adapters.blob_storage import VERSION
from hetdesrun.adapters.blob_storage.exceptions import (
    MissingHierarchyError,
    StorageAuthenticationError,
    StructureObjectNotFound,
)
from hetdesrun.adapters.blob_storage.models import (
    BlobStorageStructureSink,
    BlobStorageStructureSource,
    IdString,
    InfoResponse,
    MultipleSinksResponse,
    MultipleSourcesResponse,
    StructureResponse,
    StructureThingNode,
)
from hetdesrun.adapters.blob_storage.structure import (
    get_filtered_sinks,
    get_filtered_sources,
    get_sink_by_id,
    get_sinks_by_parent_id,
    get_source_by_id,
    get_sources_by_parent_id,
    get_thing_node_by_id,
    get_thing_nodes_by_parent_id,
)
from hetdesrun.adapters.exceptions import AdapterConnectionError
from hetdesrun.webservice.auth_dependency import get_auth_deps
from hetdesrun.webservice.router import HandleTrailingSlashAPIRouter

logger = logging.getLogger(__name__)


# Note: As CORS middleware the router employs the main FastAPI app's one
blob_storage_adapter_router = HandleTrailingSlashAPIRouter(
    prefix="/adapters/blob", tags=["blob storage adapter"]
)


@blob_storage_adapter_router.get(
    "/info",
    response_model=InfoResponse,
    # no auth for info endpoint
)
async def get_info_endpoint() -> InfoResponse:
    return InfoResponse(id="blob-storage-adapter", name="BLOB Storage Adapter", version=VERSION)


@blob_storage_adapter_router.get(
    "/structure",
    response_model=StructureResponse,
    dependencies=get_auth_deps(),
)
async def get_structure_endpoint(
    parentId: IdString | None = None,
) -> StructureResponse:
    logger.info("GET structure for parentId '%s'", parentId)
    try:
        filtered_tn_list = get_thing_nodes_by_parent_id(parentId)
        filtered_src_list = await get_sources_by_parent_id(parentId)
        filtered_snk_list = get_sinks_by_parent_id(parentId)
    except MissingHierarchyError as error:
        msg = (
            f"Could not get structure for parentId '{parentId}' "
            f"because the hierarchy json is missing:\n{error}"
        )
        logger.error(msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=msg
        ) from error
    except StorageAuthenticationError as error:
        msg = (
            f"Could not get structure for parentId '{parentId}' "
            f"because the provided BLOB storage endpoint url is invalid:\n{error}"
        )
        logger.error(msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=msg
        ) from error
    except AdapterConnectionError as error:
        msg = (
            f"Could not get structure for parentId '{parentId}' "
            f"because there have been problems connecting to the BLOB storage:\n{error}"
        )
        logger.error(msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=msg
        ) from error
    return StructureResponse(
        id="blob-storage-adapter",
        name="Blob Storage Adapter",
        thingNodes=filtered_tn_list,
        sources=filtered_src_list,
        sinks=filtered_snk_list,
    )


@blob_storage_adapter_router.get(
    "/sources",
    response_model=MultipleSourcesResponse,
    dependencies=get_auth_deps(),
)
async def get_sources_endpoint(
    filter_str: str | None = Query(None, alias="filter"),
) -> MultipleSourcesResponse:
    logger.info("GET sources for filter string '%s'", filter_str)
    try:
        found_sources = await get_filtered_sources(filter_str=filter_str)
    except MissingHierarchyError as error:
        msg = f"Could not get sources because the hierarchy json is missing:\n{error}"
        logger.error(msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=msg
        ) from error
    except StorageAuthenticationError as error:
        msg = (
            f"Could not get sources "
            f"because the provided BLOB storage endpoint url is invalid:\n{error}"
        )
        logger.error(msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=msg
        ) from error
    except AdapterConnectionError as error:
        msg = (
            f"Could not get sources "
            f"because there have been problems connecting to the BLOB storage:\n{error}"
        )
        logger.error(msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=msg
        ) from error
    return MultipleSourcesResponse(
        resultCount=len(found_sources),
        sources=found_sources,
    )


@blob_storage_adapter_router.get(
    "/sinks",
    response_model=MultipleSinksResponse,
    dependencies=get_auth_deps(),
)
async def get_sinks_endpoint(
    filter_str: str | None = Query(None, alias="filter"),
) -> MultipleSinksResponse:
    logger.info("GET sinks for filter string '%s'", filter_str)
    try:
        found_sinks = get_filtered_sinks(filter_str=filter_str)
    except MissingHierarchyError as error:
        msg = f"Could not get sinks because the hierarchy json is missing:\n{error}"
        logger.error(msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=msg
        ) from error
    return MultipleSinksResponse(
        resultCount=len(found_sinks),
        sinks=found_sinks,
    )


@blob_storage_adapter_router.get(
    "/sources/{sourceId:path}/metadata/",
    response_model=list,
    dependencies=get_auth_deps(),
)
async def get_sources_metadata(
    sourceId: IdString,  # noqa: ARG001
) -> list:
    """Get metadata attached to sources

    This adapter does not implement attached metadata. Therefore this will always result
    in an empty list!
    """
    return []


@blob_storage_adapter_router.get(
    "/sources/{sourceId:path}",
    response_model=BlobStorageStructureSource,
    dependencies=get_auth_deps(),
)
async def get_single_source(sourceId: IdString) -> BlobStorageStructureSource:
    logger.info("GET source with id '%s'", sourceId)
    try:
        source = await get_source_by_id(sourceId)
    except StructureObjectNotFound as not_found_error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not find source with id '{sourceId}'",
        ) from not_found_error
    except MissingHierarchyError as error:
        msg = (
            f"Could not get source with id '{sourceId}' "
            f"because the hierarchy json is missing:\n{error}"
        )
        logger.error(msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=msg
        ) from error
    except StorageAuthenticationError as error:
        msg = (
            f"Could not get source with id '{sourceId}' "
            f"because the provided BLOB storage endpoint url is invalid:\n{error}"
        )
        logger.error(msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=msg
        ) from error
    except AdapterConnectionError as error:
        msg = (
            f"Could not get source with id '{sourceId}' "
            f"because there have been problems connecting to the BLOB storage:\n{error}"
        )
        logger.error(msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=msg
        ) from error

    return source


@blob_storage_adapter_router.get(
    "/sinks/{sinkId:path}/metadata/",
    response_model=list,
    dependencies=get_auth_deps(),
)
async def get_sinks_metadata(
    sinkId: IdString,  # noqa: ARG001
) -> list:
    """Get metadata attached to sinks

    This adapter does not implement attached metadata. Therefore this will always result
    in an empty list!
    """
    return []


@blob_storage_adapter_router.get(
    "/sinks/{sinkId:path}",
    response_model=BlobStorageStructureSink,
    dependencies=get_auth_deps(),
)
async def get_single_sink(sinkId: IdString) -> BlobStorageStructureSink:
    logger.info("GET sink with id %s", sinkId)
    try:
        sink = get_sink_by_id(sinkId)
    except StructureObjectNotFound as not_found_error:
        msg = f"Could not find sink with id '{sinkId}'"
        logger.error(msg)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=msg,
        ) from not_found_error
    except MissingHierarchyError as error:
        msg = (
            f"Could not get sink with id '{sinkId}' "
            f"because the hierarchy json is missing:\n{error}"
        )
        logger.error(msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=msg
        ) from error

    return sink


@blob_storage_adapter_router.get(
    "/thingNodes/{thingNodeId:path}/metadata/",
    response_model=list,
    dependencies=get_auth_deps(),
)
async def get_thing_nodes_metadata(
    thingNodeId: IdString,  # noqa: ARG001
) -> list:
    """Get metadata attached to thing Nodes.

    This adapter does not implement attached metadata. Therefore this will always result
    in an empty list!
    """
    return []


@blob_storage_adapter_router.get(
    "/thingNodes/{thingNodeId:path}",
    response_model=StructureThingNode,
    dependencies=get_auth_deps(),
)
async def get_single_thingNode(
    thingNodeId: IdString,
) -> StructureThingNode:
    logger.info("GET thing node with id %s", thingNodeId)
    try:
        thing_node = get_thing_node_by_id(thingNodeId)
    except StructureObjectNotFound as not_found_error:
        msg = f"Could not find thing node with id '{thingNodeId}'"
        logger.error(msg)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=msg,
        ) from not_found_error
    except MissingHierarchyError as error:
        msg = (
            f"Could not get thing node with id '{thingNodeId}' "
            f"because the hierarchy json is missing:\n{error}"
        )
        logger.error(msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=msg
        ) from error

    return thing_node

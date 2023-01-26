"""Web service endpoints for frontend for the blob storage adapter

Note that the blob storage adapter is not a generic rest adapter, so these webendpoints
have the sole purpose to tell the frontend which data sources and sinks are available and
can be wired.

Actual data ingestion/egestion happens in the corresponding Runtime-Python-Plugin of this adapter.
"""

import logging
from typing import List, Optional

from fastapi import HTTPException, Query, status

from hetdesrun.adapters.blob_storage import VERSION
from hetdesrun.adapters.blob_storage.exceptions import (
    SinkNotFound,
    SinkNotUnique,
    SourceNotFound,
    SourceNotUnique,
    ThingNodeNotFound,
    ThingNodesNotUnique,
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
    return InfoResponse(
        id="blob-storage-adapter", name="BLOB Storage Adapter", version=VERSION
    )


@blob_storage_adapter_router.get(
    "/structure",
    response_model=StructureResponse,
    dependencies=get_auth_deps(),
)
async def get_structure_endpoint(
    parentId: Optional[IdString] = None,
) -> StructureResponse:
    logger.info("GET structure for parentId '%s'", parentId)
    return StructureResponse(
        id="blob-storage-adapter",
        name="Blob Storage Adapter",
        thingNodes=get_thing_nodes_by_parent_id(parentId),
        sources=get_sources_by_parent_id(parentId),
        sinks=get_sinks_by_parent_id(parentId),
    )


@blob_storage_adapter_router.get(
    "/sources",
    response_model=MultipleSourcesResponse,
    dependencies=get_auth_deps(),
)
async def get_sources_endpoint(
    filter_str: Optional[str] = Query(None, alias="filter")
) -> MultipleSourcesResponse:
    logger.info("GET sources for filter string '%s'", filter_str)
    found_sources = get_filtered_sources(filter_str=filter_str)
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
    filter_str: Optional[str] = Query(None, alias="filter")
) -> MultipleSinksResponse:
    logger.info("GET sinks for filter string '%s'", filter_str)
    found_sinks = get_filtered_sinks(filter_str=filter_str)
    return MultipleSinksResponse(
        resultCount=len(found_sinks),
        sinks=found_sinks,
    )


@blob_storage_adapter_router.get(
    "/sources/{sourceId:path}/metadata/",
    response_model=List,
    dependencies=get_auth_deps(),
)
async def get_sources_metadata(
    sourceId: IdString,  # pylint: disable=unused-argument
) -> List:
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
        source = get_source_by_id(sourceId)
    except SourceNotFound as not_found_error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Could not find Source with id " + sourceId,
        ) from not_found_error
    except SourceNotUnique as not_unique_error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Sink with id " + sourceId + " not unique!",
        ) from not_unique_error

    return source


@blob_storage_adapter_router.get(
    "/sinks/{sinkId:path}/metadata/",
    response_model=List,
    dependencies=get_auth_deps(),
)
async def get_sinks_metadata(
    sinkId: IdString,  # pylint: disable=unused-argument
) -> List:
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
    logger.info("GET sink with id %s",sinkId)
    try:
        sink = get_sink_by_id(sinkId)
    except SinkNotFound as not_found_error:
        msg = f"Could not find Sink with id {sinkId}"
        logger.error(msg)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=msg,
        ) from not_found_error
    except SinkNotUnique as not_unique_error:
        msg = f"Sink with id {sinkId} not unique!"
        logger.error(msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=msg,
        ) from not_unique_error

    return sink


@blob_storage_adapter_router.get(
    "/thingNodes/{thingNodeId:path}/metadata/",
    response_model=List,
    dependencies=get_auth_deps(),
)
async def get_thing_nodes_metadata(
    thingNodeId: IdString,  # pylint: disable=unused-argument
) -> List:
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
    except ThingNodeNotFound as not_found_error:
        msg = f"Could not find ThingNode with id {thingNodeId}"
        logger.error(msg)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=msg,
        ) from not_found_error
    except ThingNodesNotUnique as not_unique_error:
        msg = f"ThingNode with id " + thingNodeId + " not unique!"
        logger.error(msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=msg,
        ) from not_unique_error

    return thing_node

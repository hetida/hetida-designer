"""Web service endpoints for frontend for the blob storate adapter

Note that the blob storage adapter is not a generic rest adapter, so these webendpoints
have the sole purpose to tell the frontend which data sources and sinks are available and
can be wired.

Actual data ingestion/egestion happens in the corresponding Runtime-Python-Plugin of this adapter.
"""


from typing import List, Optional

from fastapi import HTTPException, Query

from hetdesrun.adapters.blob_storage import VERSION
from hetdesrun.adapters.blob_storage.models import (
    BlobStorageStructureSink,
    BlobStorageStructureSource,
    InfoResponse,
    MultipleSinksResponse,
    MultipleSourcesResponse,
    StructureResponse,
    StructureThingNode,
)
from hetdesrun.adapters.blob_storage.structure import (
    get_sink_by_id,
    get_sinks,
    get_source_by_id,
    get_sources,
    get_structure,
    get_thing_node_by_id,
)
from hetdesrun.adapters.local_file.utils import from_url_representation
from hetdesrun.webservice.auth_dependency import get_auth_deps
from hetdesrun.webservice.router import HandleTrailingSlashAPIRouter

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
async def get_structure_endpoint(parentId: Optional[str] = None) -> StructureResponse:
    return get_structure(parent_id=parentId)


@blob_storage_adapter_router.get(
    "/sources",
    response_model=MultipleSourcesResponse,
    dependencies=get_auth_deps(),
)
async def get_sources_endpoint(
    filter_str: Optional[str] = Query(None, alias="filter")
) -> MultipleSourcesResponse:
    found_sources = get_sources(filter_str=filter_str)
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
    found_sinks = get_sinks(filter_str=filter_str)
    return MultipleSinksResponse(
        resultCount=len(found_sinks),
        sinks=found_sinks,
    )


@blob_storage_adapter_router.get(
    "/sources/{sourceId}/metadata/",
    response_model=List,
    dependencies=get_auth_deps(),
)
async def get_sources_metadata(
    sourceId: str,  # pylint: disable=unused-argument
) -> List:
    """Get metadata attached to sources

    This adapter does not implement metadata. Therefore this will always result
    in an empty list!
    """
    return []


@blob_storage_adapter_router.get(
    "/sources/{sourceId:path}",
    response_model=BlobStorageStructureSource,
    dependencies=get_auth_deps(),
)
async def get_single_source(sourceId: str) -> BlobStorageStructureSource:
    possible_source = get_source_by_id(sourceId)

    if possible_source is None:
        raise HTTPException(
            status_code=404,
            detail="Could not find loadable local file at path "
            + from_url_representation(sourceId)
            + " or path not in configured local_dirs",
        )

    return possible_source


@blob_storage_adapter_router.get(
    "/sinks/{sinkId}/metadata/",
    response_model=List,
    dependencies=get_auth_deps(),
)
async def get_sinks_metadata(sinkId: str) -> List:  # pylint: disable=unused-argument
    """Get metadata attached to sinks

    This adapter does not implement metadata. Therefore this will always result
    in an empty list!
    """
    return []


@blob_storage_adapter_router.get(
    "/sinks/{sinkId:path}",
    response_model=BlobStorageStructureSink,
    dependencies=get_auth_deps(),
)
async def get_single_sink(sinkId: str) -> BlobStorageStructureSink:
    possible_sink = get_sink_by_id(sinkId)

    if possible_sink is None:
        raise HTTPException(
            status_code=404,
            detail="Could not find BLOB " + sinkId,
        )

    return possible_sink


@blob_storage_adapter_router.get(
    "/thingNodes/{thingNodeId}/metadata/",
    response_model=List,
    dependencies=get_auth_deps(),
)
async def get_thing_nodes_metadata(
    thingNodeId: str,  # pylint: disable=unused-argument
) -> List:
    """Get metadata attached to thing Nodes.

    This adapter does not implement metadata. Therefore this will always result
    in an empty list!
    """
    return []


@blob_storage_adapter_router.get(
    "/thingNodes/{thingNodeId}",
    response_model=StructureThingNode,
    dependencies=get_auth_deps(),
)
async def get_single_thingNode(
    thingNodeId: str,
) -> StructureThingNode:
    possible_thing_node = get_thing_node_by_id(thingNodeId)

    if possible_thing_node is None:
        raise HTTPException(
            status_code=404,
            detail="Could not find bucket " + thingNodeId,
        )

    return possible_thing_node

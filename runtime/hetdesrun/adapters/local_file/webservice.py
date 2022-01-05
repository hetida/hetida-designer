"""Web service endpoints for frontend for the local file adapter

Note that the local file adapter is not a generic rest adapter, so these webendpoints
have the sole purpose to tell the frontend which data sources and sinks are available and
can be wired.

Actual data ingestion/egestion happens in the corresponding Runtime-Python-Plugin of this adapter.
"""


from typing import Optional, List

from fastapi import APIRouter, Query, HTTPException

from hetdesrun.service.auth_dependency import get_auth_deps


from hetdesrun.adapters.local_file.structure import (
    get_structure,
    get_sources,
    get_sinks,
    get_source_by_id,
    get_sink_by_id,
    get_thing_node_by_id,
)

from hetdesrun.adapters.local_file import VERSION

from hetdesrun.adapters.local_file.models import (
    InfoResponse,
    StructureResponse,
    MultipleSourcesResponse,
    MultipleSinksResponse,
    LocalFileStructureSource,
    LocalFileStructureSink,
    StructureThingNode,
)

from hetdesrun.adapters.local_file.utils import from_url_representation

# Note: As CORS middleware the router employs the main FastAPI app's one
local_file_adapter_router = APIRouter()


@local_file_adapter_router.get(
    "/info", response_model=InfoResponse, dependencies=get_auth_deps(),
)
async def get_info_endpoint() -> InfoResponse:
    return InfoResponse(
        id="local-file-adapter", name="Local File Adapter", version=VERSION
    )


@local_file_adapter_router.get(
    "/structure", response_model=StructureResponse, dependencies=get_auth_deps(),
)
async def get_structure_endpoint(parentId: Optional[str] = None) -> StructureResponse:
    return get_structure(parent_id=parentId)


@local_file_adapter_router.get(
    "/sources", response_model=MultipleSourcesResponse, dependencies=get_auth_deps(),
)
async def get_sources_endpoint(
    filter_str: Optional[str] = Query(None, alias="filter")
) -> MultipleSourcesResponse:
    found_sources = get_sources(filter_str=filter_str)
    return MultipleSourcesResponse(
        resultCount=len(found_sources), sources=found_sources,
    )


@local_file_adapter_router.get(
    "/sinks", response_model=MultipleSinksResponse, dependencies=get_auth_deps(),
)
async def get_sinks_endpoint(
    filter_str: Optional[str] = Query(None, alias="filter")
) -> MultipleSinksResponse:
    found_sinks = get_sinks(filter_str=filter_str)
    return MultipleSinksResponse(resultCount=len(found_sinks), sinks=found_sinks,)


@local_file_adapter_router.get(
    "/sources/{sourceId}/metadata/", response_model=List, dependencies=get_auth_deps(),
)
async def get_sources_metadata(
    sourceId: str,  # pylint: disable=unused-argument
) -> List:
    """Get metadata attached to sources

    This adapter does not implement metadata. Therefore this will always result
    in an empty list!
    """
    return []


@local_file_adapter_router.get(
    "/sources/{source_id:path}",
    response_model=LocalFileStructureSource,
    dependencies=get_auth_deps(),
)
async def get_single_source(source_id: str) -> LocalFileStructureSource:
    possible_source = get_source_by_id(source_id)

    if possible_source is None:
        raise HTTPException(
            status_code=404,
            detail="Could not find loadable local file at path "
            + from_url_representation(source_id)
            + " or path not in configured local_dirs",
        )

    return possible_source


@local_file_adapter_router.get(
    "/sinks/{sinkId}/metadata/", response_model=List, dependencies=get_auth_deps(),
)
async def get_sinks_metadata(sinkId: str) -> List:  # pylint: disable=unused-argument
    """Get metadata attached to sinks

    This adapter does not implement metadata. Therefore this will always result
    in an empty list!
    """
    return []


@local_file_adapter_router.get(
    "/sinks/{sink_id:path}",
    response_model=LocalFileStructureSink,
    dependencies=get_auth_deps(),
)
async def get_single_sink(sink_id: str) -> LocalFileStructureSink:
    possible_sink = get_sink_by_id(sink_id)

    if possible_sink is None:
        raise HTTPException(
            status_code=404,
            detail="Could not find writable local file at path "
            + from_url_representation(sink_id)
            + " or path not in configured local_dirs",
        )

    return possible_sink


@local_file_adapter_router.get(
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


@local_file_adapter_router.get(
    "/thingNodes/{id}", response_model=StructureThingNode, dependencies=get_auth_deps(),
)
async def get_single_thingNode(
    id: str,  # pylint: disable=redefined-builtin
) -> StructureThingNode:
    possible_thing_node = get_thing_node_by_id(id)

    if possible_thing_node is None:
        raise HTTPException(
            status_code=404,
            detail="Could not find directory at path "
            + from_url_representation(id)
            + " or path not in configured local_dirs",
        )

    return possible_thing_node

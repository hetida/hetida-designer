"""Web service endpoints for frontend for the sql adapter

Note that the sql adapter is not a generic rest adapter, so these webendpoints
have the sole purpose to tell the frontend which data sources and sinks are available and
can be wired.

Actual data ingestion/egestion happens in the corresponding Runtime-Python-Plugin of this adapter.
"""

from fastapi import HTTPException, Query

from hetdesrun.adapters.sql_adapter import VERSION
from hetdesrun.adapters.sql_adapter.models import (
    InfoResponse,
    MultipleSinksResponse,
    MultipleSourcesResponse,
    SQLAdapterStructureSink,
    SQLAdapterStructureSource,
    StructureResponse,
    StructureThingNode,
)
from hetdesrun.adapters.sql_adapter.structure import (
    get_sink_by_id,
    get_sinks,
    get_source_by_id,
    get_sources,
    get_structure,
    get_thing_node_by_id,
)
from hetdesrun.adapters.sql_adapter.utils import from_url_representation
from hetdesrun.webservice.auth_dependency import get_auth_deps
from hetdesrun.webservice.router import HandleTrailingSlashAPIRouter

# Note: As CORS middleware the router employs the main FastAPI app's one
sql_adapter_router = HandleTrailingSlashAPIRouter(prefix="/adapters/sql", tags=["sql adapter"])


@sql_adapter_router.get(
    "/info",
    response_model=InfoResponse,
    # no auth for info endpoint
)
async def get_info_endpoint() -> InfoResponse:
    return InfoResponse(id="sql-adapter", name="SQL Adapter", version=VERSION)


@sql_adapter_router.get(
    "/structure",
    response_model=StructureResponse,
    dependencies=get_auth_deps(),
)
async def get_structure_endpoint(parentId: str | None = None) -> StructureResponse:
    return get_structure(parent_id=parentId)


@sql_adapter_router.get(
    "/sources",
    response_model=MultipleSourcesResponse,
    dependencies=get_auth_deps(),
)
async def get_sources_endpoint(
    filter_str: str | None = Query(None, alias="filter"),
) -> MultipleSourcesResponse:
    found_sources = get_sources(filter_str=filter_str)
    return MultipleSourcesResponse(
        resultCount=len(found_sources),
        sources=found_sources,
    )


@sql_adapter_router.get(
    "/sinks",
    response_model=MultipleSinksResponse,
    dependencies=get_auth_deps(),
)
async def get_sinks_endpoint(
    filter_str: str | None = Query(None, alias="filter"),  # noqa: ARG001
) -> MultipleSinksResponse:
    found_sinks = get_sinks(filter_str=filter_str)
    return MultipleSinksResponse(
        resultCount=len(found_sinks),
        sinks=found_sinks,
    )


@sql_adapter_router.get(
    "/sources/{sourceId:path}/metadata/",
    response_model=list,
    dependencies=get_auth_deps(),
)
async def get_sources_metadata(
    sourceId: str,  # noqa: ARG001
) -> list:
    """Get metadata attached to sources

    This adapter does not implement metadata. Therefore this will always result
    in an empty list!
    """
    return []


@sql_adapter_router.get(
    "/sources/{source_id:path}",
    response_model=SQLAdapterStructureSource,
    dependencies=get_auth_deps(),
)
async def get_single_source(source_id: str) -> SQLAdapterStructureSource:
    possible_source = get_source_by_id(source_id)

    if possible_source is None:
        raise HTTPException(
            status_code=404,
            detail="Could not find loadable sql data " + from_url_representation(source_id),
        )

    return possible_source


@sql_adapter_router.get(
    "/sinks/{sinkId:path}/metadata/",
    response_model=list,
    dependencies=get_auth_deps(),
)
async def get_sinks_metadata(sinkId: str) -> list:  # noqa: ARG001
    """Get metadata attached to sinks

    This adapter does not implement metadata. Therefore this will always result
    in an empty list!
    """
    return []


@sql_adapter_router.get(
    "/sinks/{sink_id:path}",
    response_model=SQLAdapterStructureSink,
    dependencies=get_auth_deps(),
)
async def get_single_sink(sink_id: str) -> SQLAdapterStructureSink:
    possible_sink = get_sink_by_id(sink_id)

    if possible_sink is None:
        raise HTTPException(
            status_code=404,
            detail="Could not find writable sql table " + from_url_representation(sink_id),
        )

    return possible_sink


@sql_adapter_router.get(
    "/thingNodes/{thingNodeId}/metadata/",
    response_model=list,
    dependencies=get_auth_deps(),
)
async def get_thing_nodes_metadata(
    thingNodeId: str,  # noqa: ARG001
) -> list:
    """Get metadata attached to thing Nodes.

    This adapter does not implement metadata. Therefore this will always result
    in an empty list!
    """
    return []


@sql_adapter_router.get(
    "/thingNodes/{id}",
    response_model=StructureThingNode,
    dependencies=get_auth_deps(),
)
async def get_single_thingNode(
    id: str,  # noqa: A002
) -> StructureThingNode:
    possible_thing_node = get_thing_node_by_id(id)

    if possible_thing_node is None:
        raise HTTPException(
            status_code=404,
            detail="Could not find sql thing node at id path " + from_url_representation(id),
        )

    return possible_thing_node

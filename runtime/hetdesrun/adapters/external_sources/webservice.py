from fastapi import HTTPException, Query

from hetdesrun.adapters.external_sources import VERSION
from hetdesrun.adapters.external_sources.models import (
    ExternalSourcesStructureSink,
    ExternalSourcesStructureSource,
    InfoResponse,
    MultipleSinksResponse,
    MultipleSourcesResponse,
    StructureResponse,
    StructureThingNode,
)
from hetdesrun.adapters.external_sources.structure import (
    get_sink_by_id,
    get_sinks,
    get_source_by_id,
    get_sources,
    get_structure,
    get_thing_node_by_id,
)
from hetdesrun.webservice.auth_dependency import get_auth_deps
from hetdesrun.webservice.router import HandleTrailingSlashAPIRouter

# Note: As CORS middleware the router employs the main FastAPI app's one
external_sources_adapter_router = HandleTrailingSlashAPIRouter(
    prefix="/adapters/external_sources", tags=["external sources adapter"]
)


@external_sources_adapter_router.get(
    "/info",
    response_model=InfoResponse,
    # no auth for info endpoint
)
async def get_info_endpoint() -> InfoResponse:
    return InfoResponse(id="external-sources", name="External Sources Adapter", version=VERSION)


@external_sources_adapter_router.get(
    "/structure",
    response_model=StructureResponse,
    dependencies=get_auth_deps(),
)
async def get_structure_endpoint(parentId: str | None = None) -> StructureResponse:
    return get_structure(parent_id=parentId)


@external_sources_adapter_router.get(
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


@external_sources_adapter_router.get(
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


@external_sources_adapter_router.get(
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


@external_sources_adapter_router.get(
    "/sources/{source_id:path}",
    response_model=ExternalSourcesStructureSource,
    dependencies=get_auth_deps(),
)
async def get_single_source(source_id: str) -> ExternalSourcesStructureSource:
    possible_source = get_source_by_id(source_id)

    if possible_source is None:
        raise HTTPException(
            status_code=404,
            detail="Could not find loadable external source " + source_id,
        )

    return possible_source


@external_sources_adapter_router.get(
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


@external_sources_adapter_router.get(
    "/sinks/{sink_id:path}",
    response_model=ExternalSourcesStructureSink,
    dependencies=get_auth_deps(),
)
async def get_single_sink(sink_id: str) -> ExternalSourcesStructureSink:
    possible_sink = get_sink_by_id(sink_id)

    if possible_sink is None:
        raise HTTPException(
            status_code=404,
            detail="Could not find external sink " + sink_id,
        )

    return possible_sink


@external_sources_adapter_router.get(
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


@external_sources_adapter_router.get(
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
            detail="Could not find external sources node with id " + id,
        )

    return possible_thing_node

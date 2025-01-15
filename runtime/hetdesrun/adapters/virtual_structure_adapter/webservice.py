import logging
from uuid import UUID

from fastapi import HTTPException, Query

from hetdesrun.adapters.virtual_structure_adapter import VERSION
from hetdesrun.adapters.virtual_structure_adapter.models import (
    MultipleVirtualStructureAdapterSinksResponse,
    MultipleVirtualStructureAdapterSourcesResponse,
    VirtualStructureAdapterInfoResponse,
    VirtualStructureAdapterResponse,
    VirtualStructureAdapterSink,
    VirtualStructureAdapterSource,
    VirtualStructureAdapterThingNode,
)
from hetdesrun.adapters.virtual_structure_adapter.structure import (
    get_filtered_sinks,
    get_filtered_sources,
    get_single_sink,
    get_single_source,
    get_single_thingnode,
    get_structure,
)
from hetdesrun.webservice.auth_dependency import get_auth_deps
from hetdesrun.webservice.router import HandleTrailingSlashAPIRouter

logger = logging.getLogger(__name__)
virtual_structure_adapter_router = HandleTrailingSlashAPIRouter(
    prefix="/adapters/virtual_structure", tags=["virtual structure adapter"]
)


@virtual_structure_adapter_router.get(
    "/info",
    response_model=VirtualStructureAdapterInfoResponse,
    # no auth for info endpoint
)
async def get_info_endpoint() -> VirtualStructureAdapterInfoResponse:
    return VirtualStructureAdapterInfoResponse(
        id="virtual-structure-adapter", name="Virtual Structure Adapter", version=VERSION
    )


@virtual_structure_adapter_router.get(
    "/structure",
    response_model=VirtualStructureAdapterResponse,
    dependencies=get_auth_deps(),
)
async def get_structure_endpoint(parentId: UUID | None = None) -> VirtualStructureAdapterResponse:
    """Returns one level of the thingnode hierarchy for lazy-loading in the frontend."""
    return get_structure(parent_id=parentId)


@virtual_structure_adapter_router.get(
    "/thingNodes/{node_id}/metadata/",
    response_model=list,
    dependencies=get_auth_deps(),
)
async def get_thingnode_metadata_endpoint(node_id: UUID) -> list:  # noqa: ARG001
    """Get metadata attached to thing nodes.

    This adapter does not implement metadata yet.
    """
    return []


@virtual_structure_adapter_router.get(
    "/thingNodes/{node_id}",
    response_model=VirtualStructureAdapterThingNode,
    dependencies=get_auth_deps(),
)
async def get_single_thingnode_endpoint(node_id: UUID) -> VirtualStructureAdapterThingNode:
    node = get_single_thingnode(node_id)
    if node is None:
        logger.info("No ThingNode found for provided UUID: %s", node_id)
        raise HTTPException(
            status_code=404, detail=f"No ThingNode found for provided UUID: {node_id}"
        )

    return node


@virtual_structure_adapter_router.get(
    "/sources",
    response_model=MultipleVirtualStructureAdapterSourcesResponse,
    dependencies=get_auth_deps(),
)
async def get_sources_endpoint(
    filter_str: str | None = Query(None, alias="filter"),
) -> MultipleVirtualStructureAdapterSourcesResponse:
    matching_sources = get_filtered_sources(filter_str)
    return MultipleVirtualStructureAdapterSourcesResponse(
        resultCount=len(matching_sources),
        sources=matching_sources,
    )


@virtual_structure_adapter_router.get(
    "/sources/{source_id}/metadata/",
    response_model=list,
    dependencies=get_auth_deps(),
)
async def get_source_metadata_endpoint(source_id: UUID) -> list:  # noqa: ARG001
    """Get metadata attached to sources.

    This adapter does not implement metadata yet.
    """
    return []


@virtual_structure_adapter_router.get(
    "/sources/{source_id}",
    response_model=VirtualStructureAdapterSource,
    dependencies=get_auth_deps(),
)
async def get_single_source_endpoint(source_id: UUID) -> VirtualStructureAdapterSource:
    source = get_single_source(source_id)
    if source is None:
        raise HTTPException(
            status_code=404, detail=f"No Source found for provided UUID: {source_id}"
        )

    return source


@virtual_structure_adapter_router.get(
    "/sinks",
    response_model=MultipleVirtualStructureAdapterSinksResponse,
    dependencies=get_auth_deps(),
)
async def get_sinks_endpoint(
    filter_str: str | None = Query(None, alias="filter"),
) -> MultipleVirtualStructureAdapterSinksResponse:
    matching_sinks = get_filtered_sinks(filter_str)
    return MultipleVirtualStructureAdapterSinksResponse(
        resultCount=len(matching_sinks),
        sinks=matching_sinks,
    )


@virtual_structure_adapter_router.get(
    "/sinks/{sink_id}/metadata/",
    response_model=list,
    dependencies=get_auth_deps(),
)
async def get_sink_metadata_endpoint(sink_id: UUID) -> list:  # noqa: ARG001
    """Get metadata attached to sinks.

    This adapter does not implement metadata yet.
    """
    return []


@virtual_structure_adapter_router.get(
    "/sinks/{sink_id}",
    response_model=VirtualStructureAdapterSink,
    dependencies=get_auth_deps(),
)
async def get_single_sink_endpoint(sink_id: UUID) -> VirtualStructureAdapterSink:
    sink = get_single_sink(sink_id)
    if sink is None:
        raise HTTPException(status_code=404, detail=f"No Sink found for provided UUID: {sink_id}")

    return sink

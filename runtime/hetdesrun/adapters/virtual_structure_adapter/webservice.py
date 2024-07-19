import logging
from uuid import UUID

from fastapi import HTTPException

from hetdesrun.adapters.virtual_structure_adapter.models import (
    StructureResponse,
    StructureThingNode,
    StructureVirtualSink,
    StructureVirtualSource,
)
from hetdesrun.adapters.virtual_structure_adapter.structure import (
    get_single_sink,
    get_single_source,
    get_single_thingnode,
    get_structure,
)
from hetdesrun.structure.db.exceptions import DBNotFoundError
from hetdesrun.webservice.router import HandleTrailingSlashAPIRouter

logger = logging.getLogger(__name__)
virtual_structure_adapter_router = HandleTrailingSlashAPIRouter(
    prefix="/adapters/vst", tags=["virtual structure adapter"]
)


@virtual_structure_adapter_router.get(
    "/structure",
    response_model=StructureResponse,
    dependencies=[],
)
async def get_structure_endpoint(parentId: UUID | None = None) -> StructureResponse:
    """Returns one level of the thingnode hierarchy for lazy-loading in the frontend"""
    return get_structure(parent_id=parentId)



@virtual_structure_adapter_router.get(
    "/thingNodes/{id}",
    response_model=StructureThingNode,
    dependencies=[],
)
async def get_single_thingnode_endpoint(node_id: UUID) -> StructureThingNode:
    try:
        node = get_single_thingnode(node_id)
    except DBNotFoundError as exc:
        logger.info("No ThingNode found for provided UUID (%s)", node_id)
        raise HTTPException(
            status_code=404, detail=f"No ThingNode found for provided UUID ({node_id})"
        ) from exc

    return node


@virtual_structure_adapter_router.get(
    "/sources/{source_id:path}",
    response_model=StructureVirtualSource,
    dependencies=[],
)
async def get_single_source_endpoint(source_id: UUID) -> StructureVirtualSource:
    try:
        source = get_single_source(source_id)
    except DBNotFoundError as exc:
        logger.info("No Source found for provided UUID (%s)", source_id)
        raise HTTPException(
            status_code=404, detail=f"No Source found for provided UUID ({source_id})"
        ) from exc

    return source


@virtual_structure_adapter_router.get(
    "/sinks/{sink_id:path}",
    response_model=StructureVirtualSink,
    dependencies=[],
)
async def get_single_sink_endpoint(sink_id: UUID) -> StructureVirtualSink:
    try:
        sink = get_single_sink(sink_id)
    except DBNotFoundError as exc:
        logger.info("No Sink found for provided UUID (%s)", sink_id)
        raise HTTPException(
            status_code=404, detail=f"No Sink found for provided UUID ({sink_id})"
        ) from exc

    return sink

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
    get_single_node,
    get_structure,
)
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
async def get_structure_endpoint(parentId: str | None = None) -> StructureResponse:
    if parentId:
        parentId = UUID(parentId)
    return get_structure(parent_id=parentId)


@virtual_structure_adapter_router.get(
    "/sources/{source_id:path}",
    response_model=StructureVirtualSource,
    dependencies=[],
)
async def get_single_source(source_id: UUID) -> StructureVirtualSource:
    source = get_single_node(source_id)

    if source is None:
        raise HTTPException(status_code=404, detail="Could not find the source")

    if not isinstance(source, StructureVirtualSource):
        raise HTTPException(
            status_code=400, detail="The requested UUID is not a source"
        )

    return source


@virtual_structure_adapter_router.get(
    "/sinks/{sink_id:path}",
    response_model=StructureVirtualSink,
    dependencies=[],
)
async def get_single_sink(sink_id: UUID) -> StructureVirtualSink:
    sink = get_single_node(sink_id)

    if sink is None:
        raise HTTPException(status_code=404, detail="Could not find the sink")

    if not isinstance(sink, StructureVirtualSink):
        raise HTTPException(status_code=400, detail="The requested UUID is not a sink")

    return sink


@virtual_structure_adapter_router.get(
    "/thingNodes/{id}",
    response_model=StructureThingNode,
    dependencies=[],
)
async def get_single_thingnode(node_id: UUID) -> StructureThingNode:
    node = get_single_node(node_id)

    if node is None:
        raise HTTPException(status_code=404, detail="Could not find the thingnode")

    if not isinstance(node, StructureThingNode):
        raise HTTPException(
            status_code=400, detail="The requested UUID is not a thingnode"
        )

    return node

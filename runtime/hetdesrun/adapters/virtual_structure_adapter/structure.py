import logging
from uuid import UUID

from hetdesrun.adapters.virtual_structure_adapter.models import (
    StructureResponse,
    StructureThingNode,
    StructureVirtualSink,
    StructureVirtualSource,
)
from hetdesrun.structure.models import Sink, Source
from hetdesrun.structure.structure_service import get_children, get_item

logger = logging.getLogger(__name__)


def get_level_from_struct_service(
    parent_id: UUID | None = None,
) -> tuple[
    list[StructureThingNode], list[StructureVirtualSource], list[StructureVirtualSink]
]:
    thing_nodes, sources, sinks = get_children(parent_id)
    struct_thing_nodes = [
        StructureThingNode.from_structure_service(node) for node in thing_nodes
    ]
    struct_sources = [
        StructureVirtualSource.from_structure_service(source) for source in sources
    ]
    struct_sinks = [StructureVirtualSink.from_structure_service(sink) for sink in sinks]

    return struct_thing_nodes, struct_sources, struct_sinks


def get_structure(parent_id: UUID | None = None) -> StructureResponse:
    nodes, sources, sinks = get_level_from_struct_service(parent_id)

    return StructureResponse(
        id="vst-adapter",
        name="Virtual Structure Adapter",
        thingNodes=nodes,
        sources=sources,
        sinks=sinks,
    )


def get_single_node(
    node_id: UUID,
) -> StructureThingNode | StructureVirtualSource | StructureVirtualSink:
    node = get_item(node_id)

    if isinstance(node, Source):
        return StructureVirtualSource.from_structure_service(node)

    if isinstance(node, Sink):
        return StructureVirtualSink.from_structure_service(node)

    return StructureThingNode.from_structure_service(node)

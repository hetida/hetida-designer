import logging
from uuid import UUID

from hetdesrun.adapters.virtual_structure_adapter.models import (
    StructureResponse,
    StructureThingNode,
    StructureVirtualSink,
    StructureVirtualSource,
)
from hetdesrun.structure.structure_service import (
    get_children,
    get_single_sink_from_db,
    get_single_source_from_db,
    get_single_thingnode_from_db,
)


logger = logging.getLogger(__name__)


def get_level_from_struct_service(
    parent_id: UUID | None = None,
) -> tuple[list[StructureThingNode], list[StructureVirtualSource], list[StructureVirtualSink]]:
    thing_nodes, sources, sinks = get_children(parent_id)
    struct_thing_nodes = [StructureThingNode.from_structure_service(node) for node in thing_nodes]
    struct_sources = [StructureVirtualSource.from_structure_service(source) for source in sources]
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


def get_single_thingnode(
    tn_id: UUID,
) -> StructureThingNode:
    node = get_single_thingnode_from_db(tn_id)
    return StructureThingNode.from_structure_service(node)


def get_single_source(
    src_id: UUID,
) -> StructureVirtualSource:
    source = get_single_source_from_db(src_id)
    return StructureVirtualSource.from_structure_service(source)


def get_single_sink(
    sink_id: UUID,
) -> StructureVirtualSink:
    sink = get_single_sink_from_db(sink_id)
    return StructureVirtualSink.from_structure_service(sink)

import logging
from uuid import UUID

from hetdesrun.adapters.exceptions import AdapterHandlingException
from hetdesrun.adapters.virtual_structure_adapter.models import (
    StructureResponse,
    StructureThingNode,
    StructureVirtualSink,
    StructureVirtualSource,
)

logger = logging.getLogger(__name__)


# TODO DUMMY to simulate existing structure service
# TODO Type definitions might change -> Pass structure service objects directly?
def get_level_from_struct_service(
    parent_id: UUID | None = None,
) -> tuple[
    list[StructureThingNode], list[StructureVirtualSource], list[StructureVirtualSink]
]:
    if parent_id is None:
        logger.info("##### VST-ADAPTER Got empty service call #####")
        root_node = StructureThingNode(
            id=UUID("e3a804fd-51d5-4ab4-b7c8-37268852d379"),
            parentId=None,
            name="IamRoot",
            description="nf",
        )
        return [root_node], [], []

    logger.info("##### VST-ADAPTER past if-statement on service call #####")
    example_source = StructureVirtualSource(
        id=UUID("65c3ce6f-7b69-418d-a68a-5d7b6b453ef0"),
        thingNodeId=UUID("e3a804fd-51d5-4ab4-b7c8-37268852d379"),
        name="ExampleSource",
        path="nf.source",
    )
    test_node = StructureThingNode(
        id=UUID("65c3ce6f-7b69-418d-a78a-5d7b6b453ef0"),
        parentId=UUID("e3a804fd-51d5-4ab4-b7c8-37268852d379"),
        name="IamChild",
        description="nf",
    )

    # return [], [example_source], []
    return [test_node], [example_source], []


def get_structure(parent_id: UUID | None = None) -> StructureResponse:
    nodes, sources, sinks = get_level_from_struct_service(parent_id)

    # TODO Possible casting step
    if sources:
        logger.info("##### VST-ADAPTER returning source #####")
    return StructureResponse(
        id="vst-adapter",
        name="Virtual Structure Adapter",
        thingNodes=nodes,
        sources=sources,
        sinks=sinks,
    )


# TODO Are functions for each type needed? source, node, sink
def get_single_node(
    node_id: UUID,
) -> StructureThingNode | StructureVirtualSource | StructureVirtualSink | None:
    # TODO Call struct service here
    node = StructureVirtualSource(
        id=UUID("65c3ce6f-7b69-418d-a68a-5d7b6b453ef0"),
        thingNodeId=UUID("e3a804fd-51d5-4ab4-b7c8-37268852d379"),
        name="ExampleSource",
        path="nf.source",
    )

    return node

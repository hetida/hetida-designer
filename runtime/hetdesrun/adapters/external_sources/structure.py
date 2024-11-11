from hetdesrun.adapters.exceptions import AdapterHandlingException
from hetdesrun.adapters.external_sources.models import (
    ExternalSourcesStructureSink,
    ExternalSourcesStructureSource,
    StructureResponse,
    StructureThingNode,
    single_root_node_id,
)
from hetdesrun.adapters.external_sources.sinks import sinks
from hetdesrun.adapters.external_sources.sources import sources


def get_external_sources() -> list[ExternalSourcesStructureSource]:
    return list(sources.values())


def get_external_sinks() -> list[ExternalSourcesStructureSink]:
    return list(sinks.values())


def get_structure(parent_id: str | None = None) -> StructureResponse:
    if parent_id is None:
        return StructureResponse(
            id="external-sources",
            name="External Sources",
            thingNodes=[StructureThingNode()],  # the only thing node of this adapter
            sources=[],
            sinks=[],
        )

    if parent_id == single_root_node_id:
        return StructureResponse(
            id="external-sources",
            name="External Sources",
            thingNodes=[],
            sources=get_external_sources(),
            sinks=get_external_sinks(),
        )

    raise AdapterHandlingException(
        "Unknown parent_id, external sources adapter only has one thing node"
        f" with id {single_root_node_id}."
    )


def get_source_by_id(source_id: str) -> ExternalSourcesStructureSource | None:
    return sources.get(source_id, None)


def get_sink_by_id(sink_id: str) -> ExternalSourcesStructureSink | None:
    return sinks.get(sink_id, None)


def get_sources(filter_str: str | None = None) -> list[ExternalSourcesStructureSource]:
    return [val for key, val in sources.items() if filter_str is None or filter_str in key]


def get_sinks(filter_str: str | None = None) -> list[ExternalSourcesStructureSink]:
    return [val for key, val in sinks.items() if filter_str is None or filter_str in key]


def get_thing_node_by_id(id: str) -> StructureThingNode | None:  # noqa: A002
    if id == single_root_node_id:
        return StructureThingNode()

    return None

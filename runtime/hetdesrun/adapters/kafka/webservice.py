from fastapi import HTTPException, Query

from hetdesrun.adapters.kafka.models import (
    InfoResponse,
    KafkaAdapterStructureSink,
    KafkaAdapterStructureSource,
    MultipleSinksResponse,
    MultipleSourcesResponse,
    StructureResponse,
    StructureThingNode,
)
from hetdesrun.adapters.kafka.structure import (
    get_sink_by_id,
    get_sinks,
    get_source_by_id,
    get_sources,
    get_structure,
    get_thing_node_by_id,
)
from hetdesrun.adapters.kafka.utils import from_url_representation
from hetdesrun.adapters.sql_adapter import VERSION
from hetdesrun.webservice.auth_dependency import get_auth_deps
from hetdesrun.webservice.router import HandleTrailingSlashAPIRouter

kafka_adapter_router = HandleTrailingSlashAPIRouter(
    prefix="/adapters/kafka", tags=["kafka adapter"]
)


@kafka_adapter_router.get(
    "/info",
    response_model=InfoResponse,
    # no auth for info endpoint
)
async def get_info_endpoint() -> InfoResponse:
    return InfoResponse(id="kafka-adapter", name="Kafka Adapter", version=VERSION)


@kafka_adapter_router.get(
    "/structure",
    response_model=StructureResponse,
    dependencies=get_auth_deps(),
)
async def get_structure_endpoint(parentId: str | None = None) -> StructureResponse:
    return get_structure(parent_id=parentId)


@kafka_adapter_router.get(
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


@kafka_adapter_router.get(
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


@kafka_adapter_router.get(
    "/sources/{sourceId:path}/metadata/",
    response_model=list,
    dependencies=get_auth_deps(),
)
async def get_sources_metadata(
    sourceId: str,  # noqa: ARG001
) -> list:
    """Get metadata attached to sources

    This adapter does not implement metadata attached to sources.
     Therefore this will always result in an empty list!
    """
    return []


@kafka_adapter_router.get(
    "/sources/{source_id:path}",
    response_model=KafkaAdapterStructureSource,
    dependencies=get_auth_deps(),
)
async def get_single_source(source_id: str) -> KafkaAdapterStructureSource:
    possible_source = get_source_by_id(source_id)

    if possible_source is None:
        raise HTTPException(
            status_code=404,
            detail="Could not find kafka source " + from_url_representation(source_id),
        )

    return possible_source


@kafka_adapter_router.get(
    "/sinks/{sinkId:path}/metadata/",
    response_model=list,
    dependencies=get_auth_deps(),
)
async def get_sinks_metadata(sinkId: str) -> list:  # noqa: ARG001
    """Get metadata attached to sinks

    This adapter does not implement metadata attached to sinks.
    Therefore this will always result in an empty list!
    """
    return []


@kafka_adapter_router.get(
    "/sinks/{sink_id:path}",
    response_model=KafkaAdapterStructureSink,
    dependencies=get_auth_deps(),
)
async def get_single_sink(sink_id: str) -> KafkaAdapterStructureSink:
    possible_sink = get_sink_by_id(sink_id)

    if possible_sink is None:
        raise HTTPException(
            status_code=404,
            detail="Could not find kafka sink " + from_url_representation(sink_id),
        )

    return possible_sink


@kafka_adapter_router.get(
    "/thingNodes/{thingNodeId}/metadata/",
    response_model=list,
    dependencies=get_auth_deps(),
)
async def get_thing_nodes_metadata(
    thingNodeId: str,  # noqa: ARG001
) -> list:
    """Get metadata attached to thing Nodes.

    This adapter does not implement metadata attached to thingnodes.
    Therefore this will always result in an empty list!
    """
    return []


@kafka_adapter_router.get(
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
            detail="Adapter does not provide thing node with id " + from_url_representation(id),
        )
    return possible_thing_node

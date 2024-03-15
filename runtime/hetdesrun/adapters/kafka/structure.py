import logging
from collections.abc import Iterable

from hetdesrun.adapters.exceptions import AdapterHandlingException
from hetdesrun.adapters.generic_rest.external_types import ExternalType
from hetdesrun.adapters.kafka.config import get_kafka_adapter_config
from hetdesrun.adapters.kafka.models import (
    KafkaAdapterStructureSink,
    KafkaAdapterStructureSource,
    KafkaConfig,
    StructureResponse,
    StructureThingNode,
)

logger = logging.getLogger(__name__)


def structure_sources_from_kafka_config(
    key: str,
    kafka_config: KafkaConfig,
) -> list[KafkaAdapterStructureSource]:
    if not kafka_config.consumable:
        return []

    if kafka_config.types is None:
        allowed_types = [e.value for e in ExternalType]
    else:
        allowed_types = kafka_config.types

    return [
        KafkaAdapterStructureSource(
            id=key + "_" + str(kc_type.value),
            thingNodeId="base",
            name=kafka_config.display_name + " " + str(kc_type.value),
            type=kc_type,
            path=key + "/" + str(kc_type.value),
            metadataKey=key if str(kc_type.value).lower().startswith("metadata") else None,
            filters={
                "message_value_key": {
                    "name": "Message Value key (key in multi value message)",
                    "type": "free_text",
                    "required": True,
                }
            },
        )
        for kc_type in allowed_types
    ]


def structure_sinks_from_kafka_config(
    key: str,
    kafka_config: KafkaConfig,
) -> list[KafkaAdapterStructureSink]:
    if not kafka_config.producable:
        return []

    if kafka_config.types is None:
        allowed_types = [e.value for e in ExternalType]
    else:
        allowed_types = kafka_config.types

    return [
        KafkaAdapterStructureSink(
            id=key + "_" + str(kc_type.value),
            thingNodeId="base",
            name=kafka_config.display_name + " " + str(kc_type.value),
            type=kc_type,
            path=key + "/" + str(kc_type.value),
            metadataKey=key if str(kc_type.value).lower().startswith("metadata") else None,
            filters={
                "message_value_key": {
                    "name": "Message Value key (key in multi value message)",
                    "type": "free_text",
                    "required": True,
                },
                "message_identifier": {
                    "name": "Message Identifier (if >1 msg from output desired)",
                    "type": "free_text",
                    "required": True,
                },
            },
        )
        for kc_type in allowed_types
    ]


def get_all_kafka_sources(
    kafka_configs: dict[str, KafkaConfig],
) -> list[KafkaAdapterStructureSource]:
    all_sources = []
    for key, ka_config in kafka_configs.items():
        sources = structure_sources_from_kafka_config(key, ka_config)
        all_sources.extend(sources)
    return all_sources


def get_all_kafka_sinks(
    kafka_configs: dict[str, KafkaConfig],
) -> list[KafkaAdapterStructureSink]:
    all_sinks = []
    for key, ka_config in kafka_configs.items():
        sinks = structure_sinks_from_kafka_config(key, ka_config)
        all_sinks.extend(sinks)
    return all_sinks


def filter_kafka_sources(
    kafka_sources: Iterable[KafkaAdapterStructureSource], filter_str: str
) -> list[KafkaAdapterStructureSource]:
    filter_lower = filter_str.lower()
    return [
        x for x in kafka_sources if filter_lower in x.name.lower() or filter_lower in x.path.lower()
    ]


def filter_kafka_sinks(
    kafka_sinks: Iterable[KafkaAdapterStructureSink], filter_str: str
) -> list[KafkaAdapterStructureSink]:
    filter_lower = filter_str.lower()
    return [
        x for x in kafka_sinks if filter_lower in x.name.lower() or filter_lower in x.path.lower()
    ]


def get_structure(parent_id: str | None = None) -> StructureResponse:
    if parent_id is None:
        return StructureResponse(
            id="kafka-adapter",
            name="Kafka Adapter",
            thingNodes=[
                StructureThingNode(id="base", parentId=None, name="Kafka", description="Kafka")
            ],
            sinks=[],
            sources=[],
        )

    if parent_id == "base":
        kafka_adapter_config = get_kafka_adapter_config()

        all_sources = get_all_kafka_sources(kafka_adapter_config.kafka_configs)

        all_sinks = get_all_kafka_sinks(kafka_adapter_config.kafka_configs)

        return StructureResponse(
            id="base", name="Kafka", thingNodes=[], sinks=all_sinks, sources=all_sources
        )
    raise AdapterHandlingException("Unknown string provided as parent_id for kafka adapter.")


def get_source_by_id(source_id: str) -> KafkaAdapterStructureSource | None:
    """Get specific kafka source by id

    Returns None if source could not be found
    """

    parts = source_id.rsplit("_", maxsplit=1)
    if len(parts) != 2:
        return None

    kafka_config_key, kc_type_str = parts

    try:
        kc_type = ExternalType(kc_type_str)
    except ValueError:
        msg = (
            f"Could not extract type from source id {source_id}. "
            f"Extracted {kc_type_str} does not correspond to any valid external type."
        )
        logger.warning(msg)
        return None

    kafka_adapter_config = get_kafka_adapter_config()

    try:
        kafka_config = kafka_adapter_config.kafka_configs[kafka_config_key]
    except KeyError:
        msg = (
            f"No kafka config configured with key {kafka_config_key} for "
            f"requested source with source_id {source_id}"
        )
        logger.warning(msg)
        return None

    if not kafka_config.consumable:
        msg = (
            f"The kafka config with key {kafka_config_key} for "
            f"requested source with source_id {source_id} does not allow consumption. "
            "Therefore it does not offer the requested source!"
        )
        logger.warning(msg)
        return None

    if kafka_config.types is None:
        allowed_types = [e.value for e in ExternalType]
    else:
        allowed_types = kafka_config.types

    if kc_type not in allowed_types:
        msg = (
            f"The kafka config with key {kafka_config_key} for "
            f"requested source with source_id {source_id} and inferred type {kc_type} "
            f"does not allow this type. Allowed types are: {allowed_types}"
        )
        logger.warning(msg)
        return None

    return KafkaAdapterStructureSource(
        id=kafka_config_key + "_" + str(kc_type.value),
        thingNodeId="base",
        name=kafka_config.display_name + " " + str(kc_type.value),
        type=kc_type,
        path=kafka_config_key + "/" + str(kc_type.value),
        metadataKey=kafka_config_key if str(kc_type.value).lower().startswith("metadata") else None,
        filters={
            "message_value_key": {
                "name": "Message Value key (key in multi value message)",
                "type": "free_text",
                "required": True,
            }
        },
    )


def get_sink_by_id(sink_id: str) -> KafkaAdapterStructureSink | None:
    """Get specific kafka sink by id

    Returns None if sink could not be found
    """

    parts = sink_id.rsplit("_", maxsplit=1)
    if len(parts) != 2:
        return None

    kafka_config_key, kc_type_str = parts

    try:
        kc_type = ExternalType(kc_type_str)
    except ValueError:
        msg = (
            f"Could not extract type from sink id {sink_id}. "
            f"Extracted {kc_type_str} does not correspond to any valid external type."
        )
        logger.warning(msg)
        return None

    kafka_adapter_config = get_kafka_adapter_config()

    try:
        kafka_config = kafka_adapter_config.kafka_configs[kafka_config_key]
    except KeyError:
        msg = (
            f"No kafka config configured with key {kafka_config_key} for "
            f"requested sink with sink_id {sink_id}"
        )
        logger.warning(msg)
        return None

    if not kafka_config.producable:
        msg = (
            f"The kafka config with key {kafka_config_key} for "
            f"requested sink with sink_id {sink_id} does not allow producing. "
            "Therefore it does not offer the requested sink!"
        )
        logger.warning(msg)
        return None

    if kafka_config.types is None:
        allowed_types = [e.value for e in ExternalType]
    else:
        allowed_types = kafka_config.types

    if kc_type not in allowed_types:
        msg = (
            f"The kafka config with key {kafka_config_key} for "
            f"requested sink with sink_id {sink_id} and inferred type {kc_type} "
            f"does not allow this type."
        )
        logger.warning(msg)
        return None

    return KafkaAdapterStructureSink(
        id=kafka_config_key + "_" + str(kc_type.value),
        thingNodeId="base",
        name=kafka_config.display_name + " " + str(kc_type.value),
        type=kc_type,
        path=kafka_config_key + "/" + str(kc_type.value),
        metadataKey=kafka_config_key if str(kc_type.value).lower().startswith("metadata") else None,
        filters={
            "message_value_key": {
                "name": "Message Value key (key in multi value message)",
                "type": "free_text",
                "required": True,
            },
            "message_identifier": {
                "name": "Message Identifier (if >1 msg from output desired)",
                "type": "free_text",
                "required": True,
            },
        },
    )


def get_sources(filter_str: str | None = None) -> list[KafkaAdapterStructureSource]:
    kafka_adapter_config = get_kafka_adapter_config()

    all_sources = get_all_kafka_sources(kafka_adapter_config.kafka_configs)

    if filter_str is None:
        return all_sources

    return filter_kafka_sources(all_sources, filter_str)


def get_sinks(filter_str: str | None = None) -> list[KafkaAdapterStructureSink]:
    kafka_adapter_config = get_kafka_adapter_config()

    all_sinks = get_all_kafka_sinks(kafka_adapter_config.kafka_configs)

    if filter_str is None:
        return all_sinks

    return filter_kafka_sinks(all_sinks, filter_str)


def get_thing_node_by_id(
    id: str,  # noqa: A002, ARG001
) -> None:
    if id == "base":
        return StructureThingNode(id="base", parentId=None, name="Kafka", description="Kafka")

    return None

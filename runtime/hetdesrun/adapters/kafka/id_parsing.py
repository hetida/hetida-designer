from hetdesrun.adapters.exceptions import AdapterHandlingException
from hetdesrun.adapters.generic_rest.external_types import ExternalType
from hetdesrun.adapters.kafka.config import get_kafka_adapter_config
from hetdesrun.adapters.kafka.models import KafkaConfig


class KafkaAdapterIdParsingException(AdapterHandlingException):
    pass


def parse_id(id_str: str) -> tuple[str, KafkaConfig, ExternalType]:
    """Parse a source or sink id into a valid KafkaConfig and an ExternalType

    Returns a triple of form
        (kafka_config_key, kafka_config, external_type)

    where kafka_config is the configuration configured for kafka_config_key

    Raises KafkaAdapterIdParsingException on any parsing or validating failure
    """
    parts = id_str.rsplit("_", maxsplit=1)
    if len(parts) != 2:
        raise KafkaAdapterIdParsingException(
            "Failed parsing Kafka id string %s during splitting into appropriate parts.",
            id_str,
        )

    kafka_config_key, kc_type_str = parts

    try:
        kc_type = ExternalType(kc_type_str)
    except ValueError as e:
        msg = (
            f"Could not extract type from id str {id_str}. "
            f"Extracted {kc_type_str} does not correspond to any valid external type."
        )
        raise KafkaAdapterIdParsingException(msg) from e

    kafka_adapter_config = get_kafka_adapter_config()
    try:
        kafka_config = kafka_adapter_config.kafka_configs[kafka_config_key]
    except KeyError as e:
        raise KafkaAdapterIdParsingException(
            "There is no KafkaConfig configured with key %s parsed from id string %s",
            kafka_config_key,
            id_str,
        ) from e

    return (kafka_config_key, kafka_config, kc_type)


def parse_source_id(source_id: str) -> tuple[str, KafkaConfig, ExternalType]:
    """Parse a source id and validate it

    Additionally validates consumability and allowed type

    Returns a triple of form
        (kafka_config_key, kafka_config, external_type)

    where kafka_config is the configuration configured for kafka_config_key

    Raises KafkaAdapterIdParsingException on any parsing or validating failure.
    """

    try:
        kafka_config_key, kafka_config, kc_type = parse_id(source_id)
    except KafkaAdapterIdParsingException as e:
        raise e

    if not kafka_config.consumable:
        msg = (
            f"The kafka config with key {kafka_config_key} for "
            f"requested source with source_id {source_id} does not allow consumption. "
            "Therefore it does not offer the requested source!"
        )
        raise KafkaAdapterIdParsingException(msg)

    if not kafka_config.type_allowed(kc_type):
        msg = (
            f"The kafka config with key {kafka_config_key} for "
            f"requested source with source_id {source_id} and inferred type {kc_type} "
            f"does not allow this type."
        )
        raise KafkaAdapterIdParsingException(msg)

    return (kafka_config_key, kafka_config, kc_type)


def parse_sink_id(sink_id: str) -> tuple[str, KafkaConfig, ExternalType]:
    """Parse a sink id and validate it

    Additionally validates producability and allowed type

    Returns a triple of form
        (kafka_config_key, kafka_config, external_type)

    where kafka_config is the configuration configured for kafka_config_key

    Raises KafkaAdapterIdParsingException on any parsing or validating failure.
    """

    try:
        kafka_config_key, kafka_config, kc_type = parse_id(sink_id)
    except KafkaAdapterIdParsingException as e:
        raise e

    if not kafka_config.producable:
        msg = (
            f"The kafka config with key {kafka_config_key} for "
            f"requested source with sink_id {sink_id} does not allow consumption. "
            "Therefore it does not offer the requested source!"
        )
        raise KafkaAdapterIdParsingException(msg)

    if not kafka_config.type_allowed(kc_type):
        msg = (
            f"The kafka config with key {kafka_config_key} for "
            f"requested source with sink_id {sink_id} and inferred type {kc_type} "
            f"does not allow this type."
        )
        raise KafkaAdapterIdParsingException(msg)

    return (kafka_config_key, kafka_config, kc_type)

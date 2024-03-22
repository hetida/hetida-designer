import asyncio
import logging
from typing import Any

from hetdesrun.adapters.exceptions import AdapterHandlingException
from hetdesrun.adapters.kafka.id_parsing import (
    KafkaAdapterIdParsingException,
    parse_sink_id,
)
from hetdesrun.adapters.kafka.models import KafkaMessageValue
from hetdesrun.adapters.kafka.send import send_kafka_message
from hetdesrun.models.data_selection import FilteredSink

logger = logging.getLogger(__name__)


def gather_messages(
    wf_output_name_to_filtered_sink_mapping_dict: dict[str, FilteredSink],
    wf_output_name_to_value_mapping_dict: dict[str, Any],
) -> list[dict[str | None, KafkaMessageValue]]:
    """Gather all Kafka sink information and values

    Returns a list of dictionaries each representing a combined message.

    Each message dictionary contains entries for all message values to be sent
    together as part of the same message.

    For single value messages there is only one key "None" in the message dictionary.
    """
    by_kafka_config_by_message: dict[
        str, dict[str, dict[str | None, KafkaMessageValue]]
    ] = {}
    for (
        output_name,
        filtered_sink,
    ) in wf_output_name_to_filtered_sink_mapping_dict.items():
        id_to_use = (
            filtered_sink.ref_key
            if filtered_sink.ref_key is not None
            else filtered_sink.ref_id
        )
        assert id_to_use is not None  # noqa: S101 # for mypy
        try:
            kafka_config_key, kafka_config, kc_type = parse_sink_id(id_to_use)
        except KafkaAdapterIdParsingException as e:
            logger.error(
                "During gathering of Kafka sinks an error occured while parsing sink ids:\n%s",
                str(e),
            )
            raise e

        # "" corresponds to default message
        message_identifier: str = filtered_sink.filters.get("message_identifier", "")

        message_value_key: str | None = filtered_sink.filters.get(
            "message_value_key", None
        )
        if message_value_key == "":
            message_value_key = None

        kafka_key_message_dict = by_kafka_config_by_message.get(kafka_config_key, None)
        if kafka_key_message_dict is None:
            kafka_key_message_dict = {}
            by_kafka_config_by_message[kafka_config_key] = kafka_key_message_dict

        message_value_dict: dict[
            str | None, KafkaMessageValue
        ] | None = kafka_key_message_dict.get(message_identifier, None)
        if message_value_dict is None:
            message_value_dict = {}
            kafka_key_message_dict[message_identifier] = message_value_dict

        if message_value_dict.get(message_value_key, None) is not None:
            # duplicate message_value_key!
            msg = (
                f"Kafka adapter received a duplicate message_value_key {message_value_key} "
                f"for the same Kafka Config key {kafka_config_key} for the same message identifier "
                f"{message_identifier} from output {output_name}"
            )
            raise AdapterHandlingException(msg)

        if message_value_key is None and len(message_value_dict) > 0:
            # we have already entries and now want to add a single value message entry
            msg = (
                f"Kafka adapter received either multiple unset / empty message_value_keys "
                f"or a combination of unset / empty message_value_keys and non-empty message value "
                f"keys for the same Kafka Config key {kafka_config_key} for the same message "
                f"identifier {message_identifier}. A Kafka message cannot contain conflicting "
                f"value structure."
            )
            raise AdapterHandlingException(msg)

        message_value_dict[message_value_key] = KafkaMessageValue(
            kafka_config_key=kafka_config_key,
            message_identifier=message_identifier,
            message_value_key=message_value_key,
            kafka_config=kafka_config,
            external_type=kc_type,
            output_name=output_name,
            value=wf_output_name_to_value_mapping_dict[output_name],
        )

    by_value_key_dicts = [
        by_value_key
        for by_message_by_value_key in by_kafka_config_by_message.values()
        for by_value_key in by_message_by_value_key.values()
    ]

    return by_value_key_dicts


async def send_data(
    wf_output_name_to_filtered_sink_mapping_dict: dict[str, FilteredSink],
    wf_output_name_to_value_mapping_dict: dict[str, Any],
    adapter_key: str,  # noqa: ARG001
) -> dict[str, Any]:
    by_value_key_dicts = gather_messages(
        wf_output_name_to_filtered_sink_mapping_dict,
        wf_output_name_to_value_mapping_dict,
    )

    await asyncio.gather(
        *[
            send_kafka_message(by_value_key_dict)
            for by_value_key_dict in by_value_key_dicts
        ]
    )

    return {}

import logging
from typing import Any, cast

import aiokafka
from pydantic import ValidationError

from hetdesrun.adapters.exceptions import AdapterHandlingException
from hetdesrun.adapters.kafka.models import (
    KafkaMultiValueMessage,
    KafkaReceiveValue,
    KafkaSingleValueMessage,
)

logger = logging.getLogger(__name__)


async def receive_encoded_message(consumer: aiokafka.AIOKafkaConsumer) -> Any:
    await consumer.start()
    try:
        message = await consumer.getone()
    finally:
        consumer.stop()

    return message


async def receive_kafka_message(
    receive_message_dict: dict[str | None, KafkaReceiveValue],
) -> dict[str | None, Any]:
    first_val = next(iter(receive_message_dict.values()))
    kafka_config = first_val.kafka_config
    kafka_config_key = first_val.kafka_config_key
    message_identifier = first_val.message_identifier
    topic = kafka_config.topic

    consumer = aiokafka.AIOKafkaConsumer(topic, **(kafka_config.consumer_config))

    logger.debug(
        "Start consuming message %s from Kafka with config key %s to topic %s",
        message_identifier,
        kafka_config_key,
        topic,
    )

    try:
        message = await receive_encoded_message(consumer)
    except Exception as e:  # noqa: BLE001
        msg = (
            f"Error consuming message {message_identifier} from Kafka with "
            f"config key {kafka_config_key}"
            f"from topic {topic}:\n{str(e)}"
        )
        logger.error(msg)
        raise AdapterHandlingException(msg) from e

    logger.debug(
        "Finished consuming message %s from Kafka with config key %s from topic %s",
        message_identifier,
        kafka_config_key,
        topic,
    )

    if (
        len(receive_message_dict) == 1
        and next(iter(receive_message_dict.keys())) is None
    ):
        # expect single message
        try:
            single_val_msg = KafkaSingleValueMessage.parse_raw(
                message.value.decode("utf8")
            )
        except ValidationError as e:
            msg = (
                f"Error parsing/validating single value message {message_identifier} "
                f"from Kafka with config key {kafka_config_key}"
                f"from topic {topic}:\n{str(e)}:\n{str(e)}"
            )
            logger.error(msg)
            raise AdapterHandlingException(msg) from e
        return {None: single_val_msg.value.value}

    try:
        multi_val_msg = KafkaMultiValueMessage.parse_raw(message.value.decode("utf8"))
    except ValidationError as e:
        msg = (
            f"Error parsing/validating multi value message {message_identifier} "
            f"from Kafka with config key {kafka_config_key}"
            f"from topic {topic}:\n{str(e)}:\n{str(e)}"
        )
        logger.error(msg)
        raise AdapterHandlingException(msg) from e

    multi_val_keys = set(multi_val_msg.values.keys())  # noqa: PD011
    expected_keys = set(receive_message_dict.keys())
    if not multi_val_keys.issuperset(expected_keys):
        msg = (
            f"Missing expected multi value key s in received message {message_identifier} "
            f"from Kafka with config key {kafka_config_key}"
            f"from topic {topic}:\n"
            f"Got {str(multi_val_keys)}. "
            f"Expected {str(expected_keys)}. "
        )
        logger.error(msg)
        raise AdapterHandlingException(msg)

    return {
        key: (
            multi_val_msg.values[  # noqa: PD011
                cast(str, key)  # key cannot be None since None should only occur once,
                # i.e. in the SingleValue case
            ]
        ).value
        for key in receive_message_dict
    }

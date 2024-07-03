import logging

import aiokafka

from hetdesrun.adapters.exceptions import AdapterHandlingException
from hetdesrun.adapters.kafka.message import create_message
from hetdesrun.adapters.kafka.models import (
    KafkaMessageValue,
    KafkaMultiValueMessage,
    KafkaSingleValueMessage,
)

logger = logging.getLogger(__name__)


def serialize_message(
    msg_object: KafkaSingleValueMessage | KafkaMultiValueMessage,
) -> bytes:
    return msg_object.json().encode("utf8")


async def send_encoded_message(
    producer: aiokafka.AIOKafkaProducer,
    topic: str,
    encoded_message: bytes,
    key: str | None,
) -> None:
    await producer.start()
    try:
        await producer.send_and_wait(topic, key=key, value=encoded_message)
    finally:
        await producer.stop()


async def send_kafka_message(message_dict: dict[str | None, KafkaMessageValue]) -> None:
    first_val = next(iter(message_dict.values()))
    kafka_config = first_val.kafka_config
    kafka_config_key = first_val.kafka_config_key
    message_identifier = first_val.message_identifier
    topic = kafka_config.topic

    # prepare message
    message = create_message(message_dict)
    try:
        encoded_message = serialize_message(message)
    except Exception as e:  # noqa: BLE001
        msg = (
            f"Error serializing and encoding message {message_identifier}"
            f"for sending to Kafka with "
            f"config key {kafka_config_key}"
            f"to topic {topic}:\n{str(e)}"
        )
        logger.error(msg)
        raise AdapterHandlingException(msg) from e

    # produce
    logger.debug(
        "Start producing message %s to Kafka with config key %s to topic %s",
        message_identifier,
        kafka_config_key,
        topic,
    )

    producer = aiokafka.AIOKafkaProducer(**(kafka_config.producer_config))

    try:
        await send_encoded_message(
            producer=producer, topic=topic, encoded_message=encoded_message, key=None
        )
    except Exception as e:  # noqa: BLE001
        msg = (
            f"Error producing message {message_identifier} to Kafka with "
            f"config key {kafka_config_key}"
            f"to topic {topic}:\n{str(e)}"
        )
        logger.error(msg)
        raise AdapterHandlingException(msg) from e

    logger.debug(
        "Finished producing message %s to Kafka with config key %s to topic %s",
        message_identifier,
        kafka_config_key,
        topic,
    )

import logging

import aiokafka

from hetdesrun.adapters.exceptions import AdapterHandlingException
from hetdesrun.adapters.kafka.message import create_message
from hetdesrun.adapters.kafka.models import KafkaMessageValue

logger = logging.getLogger(__name__)


async def send_kafka_message(message_dict: dict[str, KafkaMessageValue]) -> None:
    first_val = next(iter(message_dict.values()))
    kafka_config = first_val.kafka_config
    kafka_config_key = first_val.kafka_config_key
    message_identifier = first_val.message_identifier
    topic = kafka_config.topic

    producer = aiokafka.AIOKafkaProducer(**(kafka_config.producer_config))
    await producer.start()

    message = create_message(message_dict)
    try:
        encoded_message = message.json().encode("utf8")
    except Exception as e:  # noqa: BLE001
        msg = (
            f"Error serializing and encoding message {message_identifier}"
            f"for sending to Kafka with "
            f"config key {kafka_config_key}"
            f"to topic {topic}:\n{str(e)}"
        )
        logger.error(msg)
        raise AdapterHandlingException(msg) from e

    logger.debug(
        "Start producing message %s to Kafka with config key %s to topic %s",
        message_identifier,
        kafka_config_key,
        topic,
    )
    try:
        await producer.send_and_wait(topic, key=None, value=encoded_message)
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

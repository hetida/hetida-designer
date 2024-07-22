import logging
from typing import Any, cast

import aiokafka
from pydantic import ValidationError

from hetdesrun.adapters.exceptions import AdapterHandlingException
from hetdesrun.adapters.kafka.context import (
    _get_kafka_messages_context,
)
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
        await consumer.stop()

    return message


def parse_message(
    message_bytes: bytes, multi: bool = False
) -> KafkaMultiValueMessage | KafkaSingleValueMessage:
    if multi:
        return KafkaMultiValueMessage.parse_raw(message_bytes.decode("utf8"))
    return KafkaSingleValueMessage.parse_raw(message_bytes.decode("utf8"))


async def receive_kafka_message(
    receive_message_dict: dict[str | None, KafkaReceiveValue],
) -> dict[str | None, Any]:
    first_val = next(iter(receive_message_dict.values()))
    kafka_config = first_val.kafka_config
    kafka_config_key = first_val.kafka_config_key
    message_identifier = first_val.message_identifier
    topic = kafka_config.topic

    multi: bool = not (
        len(receive_message_dict) == 1 and next(iter(receive_message_dict.keys())) is None
    )

    if (msg_object := _get_kafka_messages_context().get(kafka_config_key, None)) is not None:
        if multi and isinstance(msg_object, KafkaSingleValueMessage):
            msg = (
                f"Found kafka message stored in context for kafka_config_key {kafka_config_key}, "
                f"and message identifier {message_identifier} "
                " but it is a single value message and a multi value message is expected!"
            )
            logger.error(msg)
            raise AdapterHandlingException(msg)
        if (not multi) and isinstance(msg_object, KafkaMultiValueMessage):
            msg = (
                f"Found kafka message stored in context for kafka_config_key {kafka_config_key}, "
                f"and message identifier {message_identifier} "
                " but it is a multi value message and a single value message is expected!"
            )
            logger.error(msg)
            raise AdapterHandlingException(msg)

        if multi:
            msg_object = cast(KafkaMultiValueMessage, msg_object)
        else:
            msg_object = cast(KafkaSingleValueMessage, msg_object)

        logger.debug(
            "Found kafka message stored in context for kafka_config_key %s"
            "and message identifier %s "
            " Not consuming again and using the message from context.",
            kafka_config_key,
            message_identifier,
        )
    else:
        logger.debug(
            "Start consuming message %s from Kafka with config key %s to topic %s",
            message_identifier,
            kafka_config_key,
            topic,
        )

        consumer = aiokafka.AIOKafkaConsumer(topic, **(kafka_config.consumer_config))

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

        try:
            msg_object = parse_message(message.value, multi=multi)
        except ValidationError as e:
            msg = (
                f'Error parsing/validating {"multi" if multi else "single"} value message '
                f"{message_identifier} "
                f"from Kafka with config key {kafka_config_key}"
                f"from topic {topic}:\n{str(e)}:\n{str(e)}"
            )
            logger.error(msg)
            raise AdapterHandlingException(msg) from e

    if not multi:
        return {None: cast(KafkaSingleValueMessage, msg_object).value.value}

    # multi value message from now onwards
    msg_object = cast(KafkaMultiValueMessage, msg_object)
    multi_val_keys = set(msg_object.values.keys())  # noqa: PD011
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
            msg_object.values[  # noqa: PD011
                cast(str, key)  # key cannot be None since None should only occur once,
                # i.e. in the SingleValue case
            ]
        ).value
        for key in receive_message_dict
    }

"""Handle context for consumption

In consumption mode, messages are received before adapters are called. Hence the Kafka
adapter is required to obtain the message from memory instead of receiving a new message.

This module handles intermediate storingof such message.
"""

from contextvars import ContextVar

from hetdesrun.adapters.kafka.models import (
    KafkaMultiValueMessage,
    KafkaSingleValueMessage,
)

kafka_messages: ContextVar[dict[str, None | KafkaSingleValueMessage | KafkaMultiValueMessage]] = (
    ContextVar("kafka_messages")
)


def _get_kafka_messages_context() -> (
    dict[str, None | KafkaSingleValueMessage | KafkaMultiValueMessage]
):
    try:
        return kafka_messages.get()
    except LookupError:
        kafka_messages.set({})
        return kafka_messages.get()


def bind_kafka_messages(
    message_by_kafka_config_key: dict[str, KafkaSingleValueMessage | KafkaMultiValueMessage],
) -> None:
    _get_kafka_messages_context().update(**message_by_kafka_config_key)


def unbind_kafka_messages(*keys: str) -> None:
    ctx_dict = _get_kafka_messages_context()
    for key in keys:
        ctx_dict.pop(key, None)


def clear_kafka_messages_context() -> None:
    kafka_messages.set({})

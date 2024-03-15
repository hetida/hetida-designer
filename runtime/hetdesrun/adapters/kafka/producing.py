from typing import Any


async def produce_data_to_kafka_sink(data_to_send: Any, sink_id: str) -> None:
    # serialize data to dict depending on the provided sink's external type

    # create WrappedKafkaMessage

    # produce to Kafka

    # handle errors

    raise NotImplementedError

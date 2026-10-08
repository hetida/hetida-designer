import asyncio
import datetime
import json
import logging
import math
from typing import Annotated

import aiokafka
from pydantic import (
    AwareDatetime,
    BaseModel,
    Field,
    ValidationInfo,
    field_serializer,
    field_validator,
)
from pydantic_settings import BaseSettings, NoDecode

logger = logging.getLogger(__name__)


class KafkaConfig(BaseSettings):
    """Class that loads environment variables regarding the kafka connection configuration.

    Attributes
    ----------
    servers : list[str]
        Kafka bootstrap servers, loaded from "HETIDA_PLATFORM_KAFKA_SERVERS".
        At least one entry is required.
    tenants : list[str]
        Tenant ids the data is sent to, loaded from "HETIDA_PLATFORM_KAFKA_TENANTS".
        At least one entry is required.
    topic : str
        Kafka topic, loaded from "HETIDA_PLATFORM_KAFKA_TIMESERIES_INGESTION_TOPIC".
        Must not be empty.

    `servers` and `tenants` accept a JSON list, e.g.
    HETIDA_PLATFORM_KAFKA_SERVERS='["kafka-1:9092","kafka-2:9092"]', or a plain
    string, e.g. HETIDA_PLATFORM_KAFKA_SERVERS='kafka:9092', both from the
    environment and when passed directly as argument. Entries are additionally
    split at commas, e.g. HETIDA_PLATFORM_KAFKA_SERVERS='kafka-1:9092,kafka-2:9092'.
    If "HETIDA_PLATFORM_KAFKA_SERVERS" or
    "HETIDA_PLATFORM_KAFKA_TIMESERIES_INGESTION_TOPIC" is missing, creating the
    config fails with a ValidationError naming the variable.
    """

    # NoDecode: pydantic-settings passes the raw environment value to the validator
    # below instead of decoding it as JSON itself.
    servers: Annotated[list[str], NoDecode] = Field(
        alias="HETIDA_PLATFORM_KAFKA_SERVERS",
        min_length=1,
        description="Kafka bootstrap servers",
    )
    tenants: Annotated[list[str], NoDecode] = Field(
        alias="HETIDA_PLATFORM_KAFKA_TENANTS",
        min_length=1,
        description="Tenant ids the data is sent to",
    )
    topic: str = Field(
        alias="HETIDA_PLATFORM_KAFKA_TIMESERIES_INGESTION_TOPIC",
        min_length=1,
        description="Kafka topic",
    )

    @field_validator("servers", "tenants", mode="before")
    @classmethod
    def parse_json_string(cls, v):
        # Handles values from the environment and passed as argument (e.g. the
        # tenant input in main) alike. A string not starting with "[" is taken
        # as a single entry.
        if not isinstance(v, str):
            return v
        v = v.strip()
        if v.startswith("["):
            return json.loads(v)
        return [v] if v else []

    @field_validator("servers", "tenants")
    @classmethod
    def split_comma_separated(cls, v, info: ValidationInfo):
        # One server / tenant per list entry, aiokafka does not split list entries.
        # Runs after the list validation, so min_length does not cover entries
        # consisting only of commas.
        items = [item.strip() for entry in v for item in entry.split(",")]
        items = [item for item in items if item]
        if not items:
            raise ValueError(f"At least one entry in {info.field_name} is required")
        return items


class KafkaTemplate(BaseModel):
    """Class that corresponds to the format of a single data point in kafka payloads
    for the platform.

    Only numeric values are supported, since the platform stores time series values
    as floating point numbers. Values that cannot be converted to float, e.g. text,
    make the execution fail with a ValidationError. Data points with NaN or
    infinite value are skipped by `main`.

    Attributes
    ----------
    timestamp : AwareDatetime
        Timezone aware datetime, serialized via `isoformat()`.
    metric : str
        Key of timeseries (=alias) in database.
    value : float
        Measured value.
    """

    timestamp: AwareDatetime
    metric: str
    value: float

    @field_serializer("timestamp")
    def serialize_dt(self, timestamp: datetime.datetime, _info):
        return timestamp.isoformat()


class KafkaHandler:
    """Class that handles the delivery of messages to kafka.

    Use it as async context manager: the producer is started on entering the
    `async with` block and stopped on leaving it.

    Attributes
    ----------
    config : KafkaConfig
        Kafka configuration info.
    kafka_producer : aiokafka.AIOKafkaProducer | None
        Started Kafka producer to send messages with.
        None outside of the `async with` block.
    max_data_points_per_message : int
        Upper limit of data points per kafka message. Keeps messages well below the
        default maximum message size of 1 MB, since every data point is contained
        twice (in "payloads" and in "originalPayload").
    """

    max_data_points_per_message = 1000

    def __init__(self, config: KafkaConfig):
        self.config = config
        self.kafka_producer: aiokafka.AIOKafkaProducer | None = None

    async def __aenter__(self):
        producer = aiokafka.AIOKafkaProducer(bootstrap_servers=self.config.servers)
        try:
            await producer.start()
        except Exception:
            # A failed start() leaves the client's connections open, and
            # AIOKafkaProducer.__aexit__ is not called in that case.
            await producer.stop()
            raise
        self.kafka_producer = producer
        return self

    async def __aexit__(self, *exc_info):
        if self.kafka_producer is None:
            return
        await self.kafka_producer.stop()
        self.kafka_producer = None

    async def send_msg_to_kafka(self, payload: list[dict]):
        """Send data points to kafka, once per configured tenant.

        The data points are split into messages of at most
        `max_data_points_per_message` data points each.

        Parameters
        ----------
        payload : list[dict]
            Data points as dumped `KafkaTemplate` objects.

        Raises
        ------
        RuntimeError
            If called outside of the `async with` block.
        ValueError
            If a data point has a NaN or infinite value, which is not valid JSON.
        """
        if self.kafka_producer is None:
            raise RuntimeError(
                "Kafka producer is not started - use KafkaHandler with `async with`."
            )

        deliveries = []
        for start in range(0, len(payload), self.max_data_points_per_message):
            chunk = payload[start : start + self.max_data_points_per_message]
            original_payload = json.dumps(chunk, allow_nan=False)
            for tenant in self.config.tenants:
                kafka_payload = {
                    "tenantId": tenant,
                    "topic": self.config.topic,
                    "origin": "UNKNOWN",
                    "originalPayload": original_payload,
                    "payloads": chunk,
                }
                deliveries.append(
                    await self.kafka_producer.send(
                        self.config.topic,
                        json.dumps(kafka_payload, allow_nan=False).encode(),
                    )
                )
        # send() only enqueues; wait for all acknowledgements together so aiokafka can batch.
        await asyncio.gather(*deliveries)
        logger.info(
            "Sent %d data point(s) in %d message(s) to topic %s",
            len(payload),
            len(deliveries),
            self.config.topic,
        )


# %%
# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "data": {"data_type": "MULTITSFRAME"},
        "tenant": {"data_type": "STRING"},
    },
    "outputs": {},
    "name": "Hetida Platform Kafka",
    "category": "Data Sinks",
    "description": "New created component",
    "version_tag": "0.1.0",
    "id": "fb307c92-26d1-4f34-867e-ee5bf4e94479",
    "revision_group_id": "7e2c3659-ba5c-4046-9865-78764282a006",
    "state": "RELEASED",
    "released_timestamp": "2026-09-09T11:26:28.406786+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


async def main(*, data, tenant):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****

    # write your function code here.
    config = KafkaConfig(HETIDA_PLATFORM_KAFKA_TENANTS=tenant)

    data_points = [
        KafkaTemplate(**record).model_dump() for record in data.to_dict(orient="records")
    ]
    # NaN and infinite values are not valid JSON, the platform would reject the whole message.
    finite_data_points = [point for point in data_points if math.isfinite(point["value"])]
    if len(finite_data_points) < len(data_points):
        logger.warning(
            "Skipping %d data point(s) with NaN or infinite value",
            len(data_points) - len(finite_data_points),
        )

    if not finite_data_points:
        logger.info("No data points to send")
        return

    async with KafkaHandler(config) as kafka_handler:
        await kafka_handler.send_msg_to_kafka(finite_data_points)


# %%

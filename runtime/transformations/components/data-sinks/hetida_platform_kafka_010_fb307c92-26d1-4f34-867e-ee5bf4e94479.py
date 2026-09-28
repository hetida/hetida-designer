import datetime
import json
import logging

import aiokafka
from pydantic import AwareDatetime, BaseModel, Field, field_serializer
from pydantic_settings import BaseSettings

class KafkaConfig(BaseSettings):
    """Class that loads environment variables regarding the kafka connection configuration.

    Attributes
    ----------
    server : str
        Kafka server, loaded from "KAFKA_SERVER"
    tenant : str
        Kafka tenant, loaded from "KAFKA_TENANT"
    topic : str
        Kafka topic, loaded from "KAFKA_TOPIC"
    """

    server: str = Field(
        alias="KAFKA_SERVER",
        default="nothing-to-load",
        description="Kafka server",
    )
    tenant: str = Field(
        alias="KAFKA_TENANT",
        default="nothing-to_load",
        description="Kafka tenant",
    )
    topic: str = Field(alias="KAFKA_TOPIC", default="")

class KafkaTemplate(BaseModel):
    """Class that corresponds to the standard format of kafka payloads for the platform.

    Attributes
    ----------
    timestamp : AwareDatetime
        Timezone aware, isoformatable datetime, e.g., "%Y-%m-%dT%H:%M:%S.%fZ"
    metric : str
        Key of timeseries (=alias) in database.
    value : value
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

    Attributes
    ----------
    config : KafkaConfig
        kafka configuration info
    group_members : OrderedDict[str, GroupMember]
        Dictionary with expected group members to get data from.
    kafka_producer : aiokafka.AIOKafkaProducer | None
        Initialized Kafka Producer to sent messages with.
        If it is none, the Kafka producer is not initialized yet.
    """

    timestamp_format = "%Y-%m-%dT%H:%M:%S.%fZ"

    def __init__(
        self,
        config: KafkaConfig
    ):
        self.config = config
        self.kafka_producer: aiokafka.AIOKafkaProducer | None = None

    async def set_kafka_producer(self):
        """Initializes Kafka producer."""
        try:
            self.kafka_producer = aiokafka.AIOKafkaProducer(bootstrap_servers=self.config.server)
            await self.kafka_producer.start()
        except aiokafka.errors.KafkaConnectionError:
            await self.unset_kafka_producer()
            raise

    async def unset_kafka_producer(self):
        """Initializes Kafka producer."""
        if self.kafka_producer is None:
            return
        await self.kafka_producer.stop()
        self.kafka_producer = None

    async def send_msg_to_kafka(self, payload: list[dict], original_payload: str):
        """Send message to kafka.

        Parameters
        ----------
        payload : list[dict]
            Prepared payload from `prepare_payload`.
        original_payload : str
            Prepared payload from `prepare_payload` as string.

        Raises
        ------
        ImportError
            If Kafka producer is not initialized beforehand with `set_kafka_producer`.
        """
        tenant = self.config.tenant
        kafka_payload = {
            "tenantId": tenant,
            "topic": self.config.topic,
            "originalPayload": str(original_payload),
            "payloads": payload,
        }

        if self.kafka_producer is None:
            raise ImportError("Cannot import kafka producer - is it already defined?")

        await self.kafka_producer.send_and_wait(
            self.config.topic,
            json.dumps(kafka_payload).encode(),
        )

    async def send_msg_to_kafka(self, payload: list[dict]):
        """Send message to kafka.

        Parameters
        ----------
        payload : list[dict]
            Prepared payload.

        Raises
        ------
        ImportError
            If Kafka producer is not initialized beforehand with `set_kafka_producer`.
        """
        tenant = self.config.tenant
        kafka_payload = {
            "tenantId": tenant,
            "topic": self.config.topic,
            "payloads": payload,
        }

        if self.kafka_producer is None:
            raise ImportError("Cannot import kafka producer - is it already defined?")

        await self.kafka_producer.send_and_wait(
            self.config.topic,
            json.dumps(kafka_payload).encode(),
        )
logger = logging.getLogger(__name__)

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
    config = KafkaConfig(KAFKA_TENANT=tenant)
    kafka_handler = KafkaHandler(config)
    await kafka_handler.set_kafka_producer()
    await kafka_handler.send_msg_to_kafka(
        [
            KafkaTemplate(**record).model_dump()
            for record in data.to_dict(orient="records")
        ]
    )
    
# %%

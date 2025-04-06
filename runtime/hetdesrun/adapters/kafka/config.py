import os

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings

from hetdesrun.adapters.kafka.models import KafkaConfig


class KafkaAdapterConfig(BaseSettings):
    active: bool = Field(
        True,
        description="Whether Kafka adapter is started",
        validation_alias="KAFKA_ADAPTER_ACTIVE",
    )

    service_in_runtime: bool = Field(
        True,
        description=(
            "Whether the API part serving the hd frontend is started as part"
            " of the runtime API service as opposed to as part of the backend API."
        ),
        validation_alias="KAFKA_ADAPTER_SERVICE_IN_RUNTIME",
    )

    kafka_configs: dict[str, KafkaConfig] = Field(
        {},
        description="Kafka configurations, from which "
        "sinks and sources are generated for the Kafka adapter",
        validation_alias="HD_KAFKA_CONFIGS",
    )
    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)


environment_file = os.environ.get("HD_KAFKA_ADAPTER_ENVIRONMENT_FILE", None)

kafka_adapter_config = KafkaAdapterConfig(
    _env_file=environment_file if environment_file else None  # type: ignore[call-arg]
)


def get_kafka_adapter_config() -> KafkaAdapterConfig:
    return kafka_adapter_config

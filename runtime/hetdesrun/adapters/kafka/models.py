import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from hetdesrun.adapters.generic_rest.external_types import ExternalType
from hetdesrun.datatypes import AdvancedTypesOutputSerializationConfig, DataType


class StructureThingNode(BaseModel):
    id: str  # noqa: A003
    parentId: str | None = None
    name: str
    description: str


class KafkaAdapterStructureSink(BaseModel):
    id: str  # noqa: A003
    thingNodeId: str
    name: str
    type: ExternalType
    visible: Literal[True] = True
    path: str = Field(..., description="Display path used in Designer Frontend")
    metadataKey: str | None = None
    filters: dict[str, dict] | None = {}


class KafkaAdapterStructureSource(BaseModel):
    id: str  # noqa: A003
    thingNodeId: str
    name: str
    type: ExternalType
    visible: Literal[True] = True
    path: str = Field(..., description="Display path used in Designer Frontend")
    metadataKey: str | None = None
    filters: dict[str, dict] | None = {}


class InfoResponse(BaseModel):
    id: str  # noqa: A003
    name: str
    version: str


class MultipleSourcesResponse(BaseModel):
    resultCount: int
    sources: list[KafkaAdapterStructureSource]


class MultipleSinksResponse(BaseModel):
    resultCount: int
    sinks: list[KafkaAdapterStructureSink]


class StructureResponse(BaseModel):
    id: str  # noqa: A003
    name: str
    thingNodes: list[StructureThingNode]
    sources: list
    sinks: list[KafkaAdapterStructureSink]


class KafkaConfig(BaseModel):
    display_name: str = Field(
        ...,
        description="Name to show to user in offered sources/sinks.",
        min_length=1,
    )
    topic: str = Field(..., description="Kafka topic", min_length=1)
    kafka_cluster_config: Any = Field({"bootstrap_servers": []})
    types: list[ExternalType] | None = Field(
        None, description="All types that should be offered/accepted by this config"
    )
    producable: bool = True
    consumable: bool = False
    producer_config: dict = {}
    consumer_config: dict = {}
    consumer_commit_after: bool = Field(
        False,
        description="In consumption mode activating this will trigger a commit after each"
        " successfully handled message(no Exceptions). group_id must be set in consumer_config"
        " for this to have an effect. Furthermore enable_auto_commit should be set to False. "
        " Then this will activate at least once semantics.",
    )
    consumer_commit_before: bool = Field(
        False,
        description="In consumption mode activating this will trigger a commit before each"
        " message handling try. group_id must be set in consumer_config"
        " for this to have an effect. Furthermore enable_auto_commit should be set to False. "
        " Then this will activate at at most once semantics.",
    )
    call_consumer_stop_method_after_exception: bool = Field(
        True,
        description="If continue_consumption_after_exception is False, this option controls"
        " whether consumer.stop() will be awaited. When the consumer_config option"
        " enable_auto_commit is True (the default), stopping the consumer triggers a commit."
        " Among others (depending on auto commit interval) this would commit the kafka message"
        " which led to the exception which may be undesirable. On the other side calling"
        " stop is desirable because it properly leaves the consumer group.",
    )
    continue_consumption_after_exception: bool = Field(
        False,
        description=(
            "Whether the consumption mode is continued if an exception occurs during message."
            " handling. Note that this will commit messages thath triggered exceptions."
        ),
    )
    offer_sources_and_sinks: bool = True

    def type_allowed(self, external_type: ExternalType) -> bool:
        allowed_types = [e.value for e in ExternalType] if self.types is None else self.types
        return external_type in allowed_types


def kafka_configs_consumable_together(kafka_configs: list[KafkaConfig]) -> bool:
    """Check whether a collection of kafka_configs can be consumed together

    This should be checked for the kafka configs corresponding to all input wirings
    to the kafka adapter when in consuming mode.
    """
    return (
        len({(kc.topic, kc.consumer_config, kc.kafka_cluster_config) for kc in kafka_configs}) == 1
    )


class KafkaMessageValue(BaseModel):
    """Represents an output value to be sent into a Kafka topic"""

    kafka_config_key: str
    message_identifier: str
    message_value_key: str | None = Field(
        ..., description="null value indicates a single value message"
    )
    kafka_config: KafkaConfig
    external_type: ExternalType = Field(..., description="External type of the value")
    output_name: str
    value: Any


class KafkaReceiveValue(BaseModel):
    """Represents an output value to be sent into a Kafka topic"""

    kafka_config_key: str
    message_identifier: str
    message_value_key: str | None = Field(
        ..., description="null value indicates a single value message"
    )
    kafka_config: KafkaConfig
    external_type: ExternalType = Field(..., description="External type of the value")
    input_name: str


class KafkaMessageValueRepresentation(BaseModel):
    value: Any
    data_type: ExternalType = Field(..., description="The hetida designer datatype of the value")
    output_name: str | None = Field(
        None,
        description="If data was generated by a hetida designer trafo, this is"
        " the name of the transformation output from which the value was produced.",
    )


class KafkaMessage(BaseModel):
    """Common properties of KafkaSingleValueMessage and KafkaMultiValueMessage"""

    transformation_id: str | None = Field(
        None,
        description="If data was generated by a hetida designer trafo, this is"
        " the id of the transformation that generated the data",
    )
    job_id: str | None = Field(
        None,
        description="If data was generated by a hetida designer trafo, this is"
        " the job id of the execution. You may also provide this when generating"
        " Kafka messages from other sources that should be handled by hetida designer"
        " in order to trace job progress.",
    )
    message_creation_timestamp: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )


class KafkaSingleValueMessage(KafkaMessage):
    """A Message containing a single value

    For example one output of a hetida designer transformation
    """

    value: KafkaMessageValueRepresentation

    Config = AdvancedTypesOutputSerializationConfig


class KafkaMultiValueMessage(KafkaMessage):
    """A Message containing multiple values as a dictionary

    For example one or more outputs from a hetida designer transformation
    execution.
    """

    values: dict[str, KafkaMessageValueRepresentation]

    Config = AdvancedTypesOutputSerializationConfig


class KafkaWrappedHdData(BaseModel):
    content__: Any = Field(
        ...,
        alias="__content__",
        description="A json object representing the data of type data_type."
        " The format is that of direct provisioning",
    )
    data_type: DataType = Field(..., description="The hetida designer datatype of __content__")
    output_name: str | None = Field(
        None,
        description="If data was generated by a hetida designer trafo, this is"
        " the name of the transformation output from which the was produced.",
    )
    transformation_id: str | None = Field(
        None,
        description="If data was generated by a hetida designer trafo, this is"
        " the id of the transformation that generated the data",
    )
    job_id: str | None = Field(
        None,
        description="If data was generated by a hetida designer trafo, this is"
        " the job id of the execution. You may also provide this when generating"
        " Kafka messages from other sources that should be handled by hetida designer"
        " in order to trace job progress.",
    )

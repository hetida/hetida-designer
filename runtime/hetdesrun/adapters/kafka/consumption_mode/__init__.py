import asyncio
import logging
from uuid import uuid4

import aiokafka
from pydantic import ValidationError

from hetdesrun.adapters.kafka.context import bind_kafka_messages
from hetdesrun.adapters.kafka.id_parsing import (
    KafkaAdapterIdParsingException,
    parse_source_id,
)
from hetdesrun.adapters.kafka.models import KafkaConfig
from hetdesrun.adapters.kafka.receive import parse_message
from hetdesrun.adapters.kafka.utils import parse_value_and_msg_identifier
from hetdesrun.backend.execution import (
    TrafoExecutionError,
    perf_measured_execute_trafo_rev,
)
from hetdesrun.models.execution import ExecByIdInput
from hetdesrun.models.wiring import FilterKey
from hetdesrun.webservice.config import get_config

logger = logging.getLogger(__name__)


def extract_consumption_mode_config_info() -> tuple[str, KafkaConfig, bool]:
    """Extract the relevant info from kafka consumption mode config

    Returns a tuple
        relevant_kafka_config_key, relevant_kafka_config, multi
    where

    * relevant_kafka_config_key is the single kafka config key that occurs in
      the input wirings of the configured execution input (Uniqueness is validated)
    * relevant_kafka_config is the associated KafkaConfig
    * multi indicates whether KafkaaMultiValueMessage or a KafkaaSingleValueMessage
      is expected as the topic's payload. It is validated that only one message
      identifier occurs in input wirings and that either all input wirings have a message
      value key or there is only one input wiring.

    Raises ValueError if something is invalid. In particular ensures that
    only one message needs to be fetched from one topic from one kafka config.
    """
    consumption_mode_exec_base = get_config().hd_kafka_consumption_mode
    if consumption_mode_exec_base is None:
        raise ValueError("The kafka consumption config is invalidly None.")

    if consumption_mode_exec_base.wiring is None:
        raise ValueError("The kafka consumption config invalidly has None wiring.")

    kafka_input_wirings = [
        inp_wiring
        for inp_wiring in consumption_mode_exec_base.wiring.input_wirings
        if inp_wiring.adapter_id == "kafka"
    ]

    if len(kafka_input_wirings) == 0:
        raise ValueError("No kafka input wirings in provided wiring for kafka consumption mode!")

    try:
        relevant_id_parsing_results = [
            parse_source_id(
                inp_wiring.ref_key if inp_wiring.ref_key is not None else inp_wiring.ref_id  # type: ignore
            )
            for inp_wiring in kafka_input_wirings
            if (inp_wiring.ref_key is not None or inp_wiring.ref_id is not None)
        ]
    except KafkaAdapterIdParsingException as e:
        raise ValueError from e

    multi = False

    value_keys = {
        parse_value_and_msg_identifier(
            val_key
            if (val_key := inp_wiring.filters.get(FilterKey("message_value_key"), "")) is not None
            else ""
        )[1]
        for inp_wiring in kafka_input_wirings
    }

    first_value_key = parse_value_and_msg_identifier(
        val_key
        if (val_key := kafka_input_wirings[0].filters.get(FilterKey("message_value_key"), ""))
        is not None
        else ""
    )[1]

    if len(value_keys) > 1 or first_value_key != "":
        # multi value message
        multi = True

    if multi and ("" in value_keys):
        raise ValueError(
            "Detected multi value kafka message input wiring during kafka consumption mode."
            " In this case there are no additional single value input wirings allowed."
        )

    if len({parsing_result_tuple[0] for parsing_result_tuple in relevant_id_parsing_results}) != 1:
        raise ValueError(
            "More than one kafka_config present in input wirings configured for kafka adapter"
            " consumption mode. Kafka adapter consumption mode can only listen to one topic"
            " from one kafka_config."
        )

    relevant_kafka_config_key = relevant_id_parsing_results[0][0]
    relevant_kafka_config = relevant_id_parsing_results[0][1]

    message_identifiers = {
        parse_value_and_msg_identifier(
            val_key
            if (val_key := inp_wiring.filters.get(FilterKey("message_value_key"), "")) is not None
            else ""
        )[0]
        for inp_wiring in kafka_input_wirings
    }

    if len(message_identifiers) != 1:
        raise ValueError(
            "More than message identifiers parsed from message_value_key filters "
            "from the provided input wirings configured for kafka adapter consumption mode. "
            "Kafka adapter consumption mode can only listen to one topic"
            " from one kafka_config and trigger on one message at the same time."
        )

    return relevant_kafka_config_key, relevant_kafka_config, multi


async def handle_message(
    kafka_msg: aiokafka.structs.ConsumerRecord, kafka_config_key: str, multi: bool
) -> None:
    try:
        msg_obj = parse_message(kafka_msg.value, multi=multi)
    except ValidationError as e:
        raise e

    # bind to context in order for kafka adapter processing to use the message
    # from context instead of fetching another one.
    bind_kafka_messages({kafka_config_key: msg_obj})

    consumption_mode_exec_base = get_config().hd_kafka_consumption_mode

    assert consumption_mode_exec_base is not None  # noqa: S101 # for mypy

    # Always provide a new job id. The job id possibly received in the kafka message
    # is logged together with the new job id below in order to being able to track
    # jobs across multiple kafka steps.
    new_job_id = uuid4()

    exec_input = ExecByIdInput(
        id=consumption_mode_exec_base.id,
        wiring=consumption_mode_exec_base.wiring,
        run_pure_plot_operators=consumption_mode_exec_base.run_pure_plot_operators,
        job_id=new_job_id,
    )

    logger.info(
        f"Trigger execution of trafo {str(exec_input.id)} via Kakfa consumption mode from message "
        f"with message job id {str(msg_obj.job_id)} with job_id={str(new_job_id)}.\n"
        "Kafka message: "
        "topic={}:partition={:d}:offset={:d}: key={} timestamp={}".format(
            kafka_msg.topic,
            kafka_msg.partition,
            kafka_msg.offset,
            kafka_msg.key,
            kafka_msg.timestamp,
        ),
    )

    try:
        exec_response = await perf_measured_execute_trafo_rev(exec_input)
    except TrafoExecutionError as e:
        raise e
    except Exception as e:
        raise e

    # Outputs wired to direct provisioning go nowhere in kafka consumption mode.
    # That's why we log properly here
    result_msg = (
        f"Finished execution of trafo {str(exec_input.id)} via Kakfa consumption mode from message"
        f" with message job id {str(msg_obj.job_id)} with job_id={str(new_job_id)}.\n"
        "Kafka message:"
    ) + (
        f"topic={kafka_msg.topic}:partition={kafka_msg.partition:d}:offset={kafka_msg.offset:d}: key={kafka_msg.key} timestamp={kafka_msg.timestamp}"  # noqa: E501, ISC003
        + "\nExecution Result:\n"
        + exec_response.json(indent=2)
    )

    logger.info(result_msg)


def create_aiokafka_consumer(topic: str, consumer_config: dict) -> aiokafka.AIOKafkaConsumer:
    return aiokafka.AIOKafkaConsumer(topic, **(consumer_config))


async def start_consumption_mode() -> None:
    # extract unique kafka_config from input wirings in respective config

    (
        relevant_kafka_config_key,
        relevant_kafka_config,
        multi,
    ) = extract_consumption_mode_config_info()  # may raise ValueError on invalid config

    consumer = create_aiokafka_consumer(
        relevant_kafka_config.topic, relevant_kafka_config.consumer_config
    )

    group_id = relevant_kafka_config.consumer_config.get("group_id", None)

    consumption_mode_exec_base = get_config().hd_kafka_consumption_mode

    assert consumption_mode_exec_base is not None  # noqa: S101 # for mypy

    logger.info(
        "Start consuming in kafka adapter consumption mode.\n"
        "kafka config key: "
        "%s\nMulti: %s\n"
        "consumption mode exec:\n%s",
        relevant_kafka_config_key,
        str(multi),
        consumption_mode_exec_base.json(indent=2),
    )
    await consumer.start()

    msg_handling_exception_occured = False
    try:
        async for kafka_msg in consumer:
            # need to handle in asyncio task in order to open new context for
            # message context storing

            try:
                if relevant_kafka_config.consumer_commit_before and group_id is not None:
                    await consumer.commit()
                await asyncio.create_task(
                    handle_message(
                        kafka_msg,
                        relevant_kafka_config_key,
                        multi,
                    )
                )
            except Exception as e:
                msg_handling_exception_occured = True
                msg = (
                    "An unexpected exception occured during handling of a kafka message in "
                    "kafka adapter consumption mode. kafka config key: "
                    f"{relevant_kafka_config_key}. Multi: {str(multi)}."
                    f"Kafka message:\n"
                    "topic={}:partition={:d}:offset={:d}: key={} timestamp={} value=\n{}{}".format(
                        kafka_msg.topic,
                        kafka_msg.partition,
                        kafka_msg.offset,
                        kafka_msg.key,
                        kafka_msg.timestamp,
                        kafka_msg.value,
                        f"\nError was:\n{str(e)}",
                    )
                )
                logger.error(msg)
                if relevant_kafka_config.continue_consumption_after_exception:
                    continue
                raise e
            if relevant_kafka_config.consumer_commit_after and group_id is not None:
                await consumer.commit()

    finally:
        # This will
        # * commit if enable_auto_commit is True
        # * Leave group if group_id is set

        if (
            not msg_handling_exception_occured
        ) or relevant_kafka_config.call_consumer_stop_method_after_exception:
            await consumer.stop()

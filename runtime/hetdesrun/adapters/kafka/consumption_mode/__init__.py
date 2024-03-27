import asyncio
import logging
import os
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
from hetdesrun.backend.execution import execute_transformation_revision
from hetdesrun.models.execution import ExecByIdInput
from hetdesrun.models.run import PerformanceMeasuredStep
from hetdesrun.models.wiring import FilterKey
from hetdesrun.webservice.config import get_config

logger = logging.getLogger(__name__)


def extract_relevant_kafka_config() -> tuple[str, KafkaConfig, bool]:
    """Extract the unique relevant kafka config from the configured input wirings

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
        raise ValueError(
            "No kafka input wirings in provided wiring for kafka consumption mode!"
        )

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
            if (val_key := inp_wiring.filters.get(FilterKey("message_value_key"), ""))
            is not None
            else ""
        )[1]
        for inp_wiring in kafka_input_wirings
    }

    first_value_key = parse_value_and_msg_identifier(
        val_key
        if (
            val_key := kafka_input_wirings[0].filters.get(
                FilterKey("message_value_key"), ""
            )
        )
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

    if (
        len(
            {
                parsing_result_tuple[0]
                for parsing_result_tuple in relevant_id_parsing_results
            }
        )
        != 1
    ):
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
            if (val_key := inp_wiring.filters.get(FilterKey("message_value_key"), ""))
            is not None
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

    bind_kafka_messages({kafka_config_key: msg_obj})

    consumption_mode_exec_base = get_config().hd_kafka_consumption_mode

    assert consumption_mode_exec_base is not None  # noqa: S101 # for mypy

    new_job_id = uuid4()

    exec_input = ExecByIdInput(
        id=consumption_mode_exec_base.id,
        wiring=consumption_mode_exec_base.wiring,
        run_pure_plot_operators=consumption_mode_exec_base.run_pure_plot_operators,
        job_id=new_job_id,  # TODO: from kafka message: msg_obj.job_id
    )

    logger.info(
        f"Trigger execution of trafo {str(exec_input.id)} via Kakfa consumption mode from message "
        f"with message job id {str(msg_obj.job_id)} with job id {str(new_job_id)}.\n"
        "Kafka message: "
        "topic={}:partition={:d}:offset={:d}: key={} timestamp={}".format(
            kafka_msg.topic,
            kafka_msg.partition,
            kafka_msg.offset,
            kafka_msg.key,
            kafka_msg.timestamp,
        ),
    )
    internal_full_measured_step = PerformanceMeasuredStep.create_and_begin(
        "internal_full"
    )

    try:
        exec_response = await execute_transformation_revision(exec_input)
    except Exception as e:
        raise e

    internal_full_measured_step.stop()
    exec_response.measured_steps.internal_full = internal_full_measured_step

    if get_config().advanced_performance_measurement_active:
        exec_response.process_id = os.getpid()

    if get_config().log_execution_performance_info:
        logger.info(
            "Measured steps for job %s on process with PID %s:\n%s",
            str(exec_response.job_id),
            str(exec_response.process_id),
            str(exec_response.measured_steps),
        )

    # Outputs wired to direct provisioning go nowhere in kafka consumption mode.
    # That's why we log properly here
    result_msg = (
        f"Finished execution of trafo {str(exec_input.id)} via Kakfa consumption mode from message"
        f" with message job id {str(msg_obj.job_id)} with job id {str(new_job_id)}.\n"
        "Kafka message:"
    ) + (
        "topic={}:partition={:d}:offset={:d}: key={} timestamp={}".format(
            kafka_msg.topic,
            kafka_msg.partition,
            kafka_msg.offset,
            kafka_msg.key,
            kafka_msg.timestamp,
        )
        + "\nExecution Result:\n"
        + exec_response.json(indent=2)
    )

    logger.info(result_msg)


async def start_consumption_mode() -> None:
    # extract unique kafka_config from input wirings in respective config

    (
        relevant_kafka_config_key,
        relevant_kafka_config,
        multi,
    ) = extract_relevant_kafka_config()

    consumer = aiokafka.AIOKafkaConsumer(
        relevant_kafka_config.topic, **(relevant_kafka_config.consumer_config)
    )

    consumption_mode_exec_base = get_config().hd_kafka_consumption_mode

    assert consumption_mode_exec_base is not None  # noqa: S101 # for mypy

    await consumer.start()
    logger.info(
        "Start consuming in kafka adapter consumption mode.\n"
        "kafka config key: "
        "%s\nMulti: %s\n"
        "consumption mode exec:\n%s",
        relevant_kafka_config_key,
        str(multi),
        consumption_mode_exec_base.json(indent=2),
    )
    try:
        async for kafka_msg in consumer:
            # need to handle in asyncio task in order to open new context for
            # message context storing
            try:
                await asyncio.create_task(
                    handle_message(
                        kafka_msg,
                        relevant_kafka_config_key,
                        multi,
                    )
                )
            except Exception as e:
                msg = (
                    "An unexpected exception occured during handling of a kafka message in "
                    "kafka adapter consumption mode. kafka config key: "
                    f"{relevant_kafka_config_key}. Multi: {str(multi)}."
                    f"Kafka message:\n"
                    "topic={}:partition={:d}:offset={:d}: key={} timestamp={} value=\n{}".format(
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
                raise e

    finally:
        await consumer.stop()

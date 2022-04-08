import asyncio
import logging
from functools import cache
from typing import Coroutine, Optional
from uuid import uuid4

import aiokafka
from pydantic import ValidationError

from hetdesrun.backend.execution import (
    ExecByIdInput,
    TrafoExecutionError,
    execute_transformation_revision,
)
from hetdesrun.backend.models.info import ExecutionResponseFrontendDto
from hetdesrun.webservice.config import runtime_config

logger = logging.getLogger(__name__)


class KafkaWorkerContext:  # pylint: disable=too-many-instance-attributes
    """Bundles the per webservice-worker-process Kafka consumer and producer instances

    This class handles the typical scenario where a consumer consumes messages from
    one topic and reacts/responds by sending response messages to another topic.

    In particular manages state of the consumer and producer instances, the consumption
    asyncio task and necessary cleanup operations.

    One instance (singleton) should be created per web service worker process.

    Init Arguments:

        consumer_topic, consumer_options: parameters for construction of aiokafka
            consumer client object
        producer_topic, producer_options: parameters for producer / construction of
            aiokafka producer client

        msg_handling_coroutine : async function / coroutine that runs the message
            handling (async for) loop. It should expect an instance of this class
            as its only argument and access the consumer etc. from that.
            E.g.:

            async def my_message_handler(kafka_context):
                async for msg in kafka_context.consumer:
                    ...
                    await kafka_context.producer.send_and_wait(...)

    After initialization the start method should be awaited, e.g. in a startup_event
    coroutine of a FastAPI web application. Similarly in a shutdown_event coroutine
    the stop method should be awaited.
    """

    def __init__(
        self,
        consumer_topic: str,
        consumer_options: dict,
        msg_handling_coroutine: Coroutine,
        producer_topic: str,
        producer_options: dict,
    ):

        self.event_loop = asyncio.get_event_loop()
        self.consumer_topic = consumer_topic
        self.consumer_options = consumer_options
        self.msg_handling_coroutine = msg_handling_coroutine
        self.last_unhandled_exception: Optional[Exception] = None

        self.producer_topic = producer_topic
        self.producer_options = producer_options

        # init
        self.consumer_task = None
        self.consumer_id = uuid4()

        self._init_consumer()
        self._init_producer()

    def _init_consumer(self) -> None:
        self._consumer = aiokafka.AIOKafkaConsumer(
            self.consumer_topic,
            **(self.consumer_options),
        )

    @property
    def consumer(self):
        return self._consumer

    @property
    def producer(self):
        return self._producer

    def _init_producer(self) -> None:
        self._producer = aiokafka.AIOKafkaProducer(**(self.producer_options))

    async def _start_consumer(self) -> None:
        await self.consumer.start()
        self.consumer_task = asyncio.create_task(  # type: ignore
            self.msg_handling_coroutine(self)  # type: ignore
        )
        logger.info(
            "Started consumer and message handling from Kafka Context with consumer id %s",
            self.consumer_id,
        )

    async def _start_producer(self) -> None:
        await self.producer.start()

    async def start(self):
        await self._start_producer()
        await self._start_consumer()

    async def _stop_consumer(self):
        self.consumer_task.cancel()
        await self.consumer.stop()

    async def _stop_producer(self):
        await self.producer.stop()

    async def stop(self):
        await self._stop_consumer()
        await self._stop_producer()


@cache
def get_kafka_worker_context():
    """Kafka worker context singleton"""
    return KafkaWorkerContext(
        consumer_topic=runtime_config.hd_kafka_consumer_topic,
        consumer_options=runtime_config.hd_kafka_consumer_options,
        msg_handling_coroutine=consume_execution_trigger_message,
        producer_topic=runtime_config.hd_kafka_response_topic,
        producer_options=runtime_config.hd_kafka_producer_options,
    )


async def consume_execution_trigger_message(
    kafka_ctx: KafkaWorkerContext,
) -> None:
    """Executes transformation revisions as requested by Kafka messages to the respective topic"""
    async for msg in kafka_ctx.consumer:
        try:
            logger.debug("Consumed msg: %s", str(msg))
            logger.info(
                (
                    "Consumer %s is with partition assignment %s is starting"
                    " to consume message from Kafka."
                ),
                kafka_ctx.consumer_id,
                str(kafka_ctx.consumer.assignment()),
            )
            try:
                exec_by_id_input = ExecByIdInput.parse_raw(msg.value.decode("utf8"))
            except ValidationError as e:
                msg = (
                    f"Kafka consumer {kafka_ctx.consumer_id} failed to parse message"
                    f" payload for execution. Validation Error was {str(e)}. Aborting."
                )
                kafka_ctx.last_unhandled_exception = e
                logger.error(msg)
                continue
            logger.info(
                "Start execution of trafo rev %s with job id %s from Kafka consumer %s",
                str(exec_by_id_input.id),
                str(exec_by_id_input.job_id),
                kafka_ctx.consumer_id,
            )
            try:
                exec_result = await execute_transformation_revision(
                    exec_by_id_input.id,
                    exec_by_id_input.wiring,
                    exec_by_id_input.run_pure_plot_operators,
                    exec_by_id_input.job_id,
                )
            except TrafoExecutionError as e:
                msg = (
                    f"Kafka consumer failed to execute trafo rev {exec_by_id_input.id}"
                    f" for job {exec_by_id_input.job_id}. Error Message: {str(e)}. Aborting."
                )
                kafka_ctx.last_unhandled_exception = e
                logger.error(msg)
                continue
            logger.info(
                "Kafka consumer %s finished execution for job %s with result status %s. Error: %s",
                kafka_ctx.consumer_id,
                str(exec_by_id_input.job_id),
                str(exec_result.result),
                str(exec_result.error),
            )
            logger.debug("Kafka consumer execution result: \n%s", str(exec_result))
            await producer_send_result_msg(kafka_ctx, exec_result)
        except Exception as e:  # pylint: disable=broad-except
            kafka_ctx.last_unhandled_exception = e
            logger.error(
                "Unexpected Error during Kafka execution: %s. Aborting.", str(e)
            )
            continue


async def producer_send_result_msg(
    kakfa_ctx: KafkaWorkerContext, exec_result: ExecutionResponseFrontendDto
) -> None:
    """Send an execution result message to Kafka result/response topic"""
    message_value = exec_result.json().encode("utf8")
    logger.info(
        "Start sending result message to Kafka response topic for job %s",
        str(exec_result.job_id),
    )
    await kakfa_ctx.producer.send_and_wait(
        runtime_config.hd_kafka_response_topic,
        key=None,
        value=message_value,
    )
    logger.info(
        "Finished sending result message to Kafka response topic for job %s",
        str(exec_result.job_id),
    )

import asyncio
from unittest import mock
from uuid import UUID

import pytest
from pydantic import ValidationError

from hetdesrun.backend.execution import TrafoExecutionError
from hetdesrun.webservice.config import get_config

exec_by_id_input_msg = r"""
{
    "id": "79ce1eb1-3ef8-4c74-9114-c856fd88dc89",
    "run_pure_plot_operators": false,
    "wiring": {
        "input_wirings": [
            {
                "id": "06eb850e-b839-4f96-b4db-763040fc752d",
                "workflow_input_name": "window_size",
                "adapter_id": "direct_provisioning",
                "filters": {
                    "value": "180min"
                }
            },
            {
                "id": "74b28791-67df-4e8b-9200-50d6cd1f06f8",
                "workflow_input_name": "window_timestamp_location",
                "adapter_id": "direct_provisioning",
                "filters": {
                    "value": "center"
                }
            },
            {
                "id": "dd6108b1-3a86-4c32-9771-867921664893",
                "workflow_input_name": "input_series",
                "adapter_id": "direct_provisioning",
                "filters": {
                    "value": "{\"2018-05-19T22:20:00.000Z\":86.9358994238,\"2018-05-19T22:25:00.000Z\":78.6552569681,\"2018-05-19T22:30:00.000Z\":93.515633185,\"2018-05-19T22:35:00.000Z\":96.3497006614,\"2018-05-19T22:40:00.000Z\":83.1926874657,\"2018-05-22T05:50:00.000Z\":926.4357356548,\"2018-05-22T05:55:00.000Z\":934.7257131637,\"2018-05-22T06:00:00.000Z\":908.4082221891,\"2018-05-22T06:05:00.000Z\":917.7112901544,\"2018-05-22T06:10:00.000Z\":924.0958121497}"
                }
            },
            {
                "id": "fc77f03d-4202-4c9c-aeac-dd1e23a1d571",
                "workflow_input_name": "threshold",
                "adapter_id": "direct_provisioning",
                "filters": {
                    "value": "600.0"
                }
            }
        ],
        "output_wirings": [
            {
                "id": "b420a0a8-3b8a-43e5-b4f4-7298be9b9b09",
                "workflow_output_name": "score",
                "adapter_id": "direct_provisioning"
            },
            {
                "id": "b4021cae-e915-4161-8e5e-0ebe0abdb690",
                "workflow_output_name": "data_and_alerts",
                "adapter_id": "direct_provisioning"
            }
        ]
    },
    "job_id": "00000000-0000-0000-0000-000000000002"
}
"""

exec_latest_by_group_id_input_msg = r"""
{
    "revision_group_id": "d0d40c45-aef0-424a-a8f4-b16cd5f8b129",
    "run_pure_plot_operators": false,
    "wiring": {
        "input_wirings": [
            {
                "id": "06eb850e-b839-4f96-b4db-763040fc752d",
                "workflow_input_name": "window_size",
                "adapter_id": "direct_provisioning",
                "filters": {
                    "value": "180min"
                }
            },
            {
                "id": "74b28791-67df-4e8b-9200-50d6cd1f06f8",
                "workflow_input_name": "window_timestamp_location",
                "adapter_id": "direct_provisioning",
                "filters": {
                    "value": "center"
                }
            },
            {
                "id": "dd6108b1-3a86-4c32-9771-867921664893",
                "workflow_input_name": "input_series",
                "adapter_id": "direct_provisioning",
                "filters": {
                    "value": "{\"2018-05-19T22:20:00.000Z\":86.9358994238,\"2018-05-19T22:25:00.000Z\":78.6552569681,\"2018-05-19T22:30:00.000Z\":93.515633185,\"2018-05-19T22:35:00.000Z\":96.3497006614,\"2018-05-19T22:40:00.000Z\":83.1926874657,\"2018-05-22T05:50:00.000Z\":926.4357356548,\"2018-05-22T05:55:00.000Z\":934.7257131637,\"2018-05-22T06:00:00.000Z\":908.4082221891,\"2018-05-22T06:05:00.000Z\":917.7112901544,\"2018-05-22T06:10:00.000Z\":924.0958121497}"
                }
            },
            {
                "id": "fc77f03d-4202-4c9c-aeac-dd1e23a1d571",
                "workflow_input_name": "threshold",
                "adapter_id": "direct_provisioning",
                "filters": {
                    "value": "600.0"
                }
            }
        ],
        "output_wirings": [
            {
                "id": "b420a0a8-3b8a-43e5-b4f4-7298be9b9b09",
                "workflow_output_name": "score",
                "adapter_id": "direct_provisioning"
            },
            {
                "id": "b4021cae-e915-4161-8e5e-0ebe0abdb690",
                "workflow_output_name": "data_and_alerts",
                "adapter_id": "direct_provisioning"
            }
        ]
    },
    "job_id": "00000000-0000-0000-0000-000000000002"
}
"""

exec_result_raw = r"""
{"error": null, "execution_id": null, "output_results_by_output_name": {"score": {"data": [{"mode": "lines", "x": ["2018-05-19T20:50:00+00:00", "2018-05-19T20:55:00+00:00", "2018-05-19T21:00:00+00:00", "2018-05-19T21:05:00+00:00", "2018-05-19T21:10:00+00:00", "2018-05-22T04:20:00+00:00", "2018-05-22T04:25:00+00:00", "2018-05-22T04:30:00+00:00", "2018-05-22T04:35:00+00:00", "2018-05-22T04:40:00+00:00"], "y": [null, 0.0, 16.56128491139998, 16.56128491139998, 35.388887386599976, 0.0, 0.0, 52.63498194919998, 52.63498194919998, 52.63498194919998], "type": "scatter", "line": {"color": "#1199bb"}}], "layout": {"xaxis": {"title": {"text": "Time"}, "automargin": true}, "yaxis": {"title": {"text": "volatilities"}, "automargin": true}, "autosize": true, "height": 200, "margin": {"l": 0, "r": 0, "b": 0, "t": 5, "pad": 0}}}, "data_and_alerts": {"data": [{"mode": "lines", "x": ["2018-05-19T22:20:00+00:00", "2018-05-19T22:25:00+00:00", "2018-05-19T22:30:00+00:00", "2018-05-19T22:35:00+00:00", "2018-05-19T22:40:00+00:00", "2018-05-22T05:50:00+00:00", "2018-05-22T05:55:00+00:00", "2018-05-22T06:00:00+00:00", "2018-05-22T06:05:00+00:00", "2018-05-22T06:10:00+00:00"], "y": [86.9358994238, 78.6552569681, 93.515633185, 96.3497006614, 83.1926874657, 926.4357356548, 934.7257131637, 908.4082221891, 917.7112901544, 924.0958121497], "type": "scatter"}], "layout": {"xaxis": {"title": {"text": "Time"}, "automargin": true}, "yaxis": {"title": {"text": "Values"}, "automargin": true}, "autosize": true, "height": 200, "margin": {"l": 0, "r": 0, "b": 0, "t": 5, "pad": 0}}}}, "output_types_by_output_name": {"score": "PLOTLYJSON", "data_and_alerts": "PLOTLYJSON"}, "response": null, "result": "ok", "traceback": null, "job_id": "00000000-0000-0000-0000-000000000002"}
"""

from hetdesrun.backend.models.info import ExecutionResponseFrontendDto

exec_result = ExecutionResponseFrontendDto.parse_raw(exec_result_raw)


class MockKafkaConsumer:
    """Simulate aiokafka consumer async message iterator

    Provides exactly one message for testing purposes.
    """

    def __init__(self, exec_msg_str):
        self.exec_msg_str = exec_msg_str

    def __aiter__(self):
        self.sent = False
        return self

    async def __anext__(self):
        if not self.sent:
            self.sent = True
            mock_msg = mock.Mock
            mock_msg.value = self.exec_msg_str.encode("utf8")
            mock_msg.key = b"exec3"
            return mock_msg
        raise StopAsyncIteration

    def assignment(self):
        return ("this consumer", 42)

    async def start(self):
        pass

    async def stop(self):
        pass


async def mock_successful_execute_transformation_revision(*args, **kwargs):
    return exec_result


async def mock_failed_execute_transformation_revision(*args, **kwargs):
    raise TrafoExecutionError("Something went wrong")


async def mock_failed_execute_transformation_revision_with_arbitrary_exc(
    *args, **kwargs
):
    raise Exception("Something went horribly wrong")


async def run_kafka_msg(
    msg_str, exec_func_mock=mock_successful_execute_transformation_revision
):
    with mock.patch(
        "hetdesrun.backend.kafka.consumer.KafkaWorkerContext.consumer",
        new_callable=mock.PropertyMock,
        return_value=MockKafkaConsumer(exec_msg_str=msg_str),
    ) as mocked_ctx_consumer:

        producer_mock = mock.AsyncMock()
        with mock.patch(
            "hetdesrun.backend.kafka.consumer.KafkaWorkerContext.producer",
            producer_mock,
        ) as mocked_ctx_producer:

            from hetdesrun.backend.kafka.consumer import get_kafka_worker_context

            kafka_ctx = get_kafka_worker_context()
            await kafka_ctx.start()
            loop = asyncio.get_event_loop()

            with mock.patch(
                "hetdesrun.backend.kafka.consumer.execute_transformation_revision",
                exec_func_mock,
            ):
                results = loop.run_until_complete(
                    asyncio.gather(kafka_ctx.consumer_task)
                )
                await kafka_ctx.stop()

    return results, kafka_ctx, mocked_ctx_producer


@pytest.mark.asyncio
async def test_consumer_successful_exec_by_id_input():
    results, kafka_ctx, mocked_producer = await run_kafka_msg(exec_by_id_input_msg)

    assert kafka_ctx.last_unhandled_exception is None

    # check result message is shipped:
    mocked_producer.send_and_wait.assert_called_once()
    mocked_producer.send_and_wait.assert_called_with(
        get_config().hd_kafka_response_topic,
        key=None,
        value=exec_result.json().encode("utf8"),
    )


@pytest.mark.asyncio
async def test_consumer_successful_exec_latest_by_group_id_input():
    with mock.patch(
        "hetdesrun.backend.kafka.consumer.get_latest_revision_id",
        return_value=UUID("79ce1eb1-3ef8-4c74-9114-c856fd88dc89"),
    ) as mocked_get_latest_id:

        results, kafka_ctx, mocked_producer = await run_kafka_msg(
            exec_latest_by_group_id_input_msg
        )

        assert kafka_ctx.last_unhandled_exception is None

        # check result message is shipped:
        mocked_producer.send_and_wait.assert_called_once()
        mocked_producer.send_and_wait.assert_called_with(
            get_config().hd_kafka_response_topic,
            key=None,
            value=exec_result.json().encode("utf8"),
        )


@pytest.mark.asyncio
async def test_consumer_invalid_msg():
    results, kafka_ctx, mocked_producer = await run_kafka_msg("not parsable")
    assert kafka_ctx.last_unhandled_exception is not None
    assert isinstance(kafka_ctx.last_unhandled_exception, ValidationError)


@pytest.mark.asyncio
async def test_consumer_failed_exec():
    results, kafka_ctx, mocked_producer = await run_kafka_msg(
        exec_by_id_input_msg, exec_func_mock=mock_failed_execute_transformation_revision
    )
    assert kafka_ctx.last_unhandled_exception is not None
    assert isinstance(kafka_ctx.last_unhandled_exception, TrafoExecutionError)


@pytest.mark.asyncio
async def test_consumer_failed_exec_arbitray_exception():
    results, kafka_ctx, mocked_producer = await run_kafka_msg(
        exec_by_id_input_msg,
        exec_func_mock=mock_failed_execute_transformation_revision_with_arbitrary_exc,
    )
    assert kafka_ctx.last_unhandled_exception is not None
    assert isinstance(kafka_ctx.last_unhandled_exception, Exception)

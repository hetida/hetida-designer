from collections import namedtuple
from unittest import mock

import pytest

from hetdesrun.adapters.generic_rest.external_types import ExternalType
from hetdesrun.adapters.kafka.models import (
    KafkaMessageValueRepresentation,
    KafkaMultiValueMessage,
    KafkaSingleValueMessage,
)

KafkaRawMessage = namedtuple("KafkaRawMessage", ["value"])


@pytest.fixture
def mocked_receive_kafka_message():
    with mock.patch(
        "hetdesrun.adapters.kafka.receive.receive_encoded_message",
        return_value=KafkaRawMessage(
            value=KafkaSingleValueMessage(
                value=KafkaMessageValueRepresentation(
                    value={"a": 42.3, "b": "test"}, data_type=ExternalType.METADATA_ANY
                ),
                type=ExternalType.METADATA_ANY,
            )
            .json()
            .encode("utf8")
        ),
    ) as mocked_receive:
        yield mocked_receive


@pytest.fixture
def mocked_receive_multi_value_kafka_message():
    with mock.patch(
        "hetdesrun.adapters.kafka.receive.receive_encoded_message",
        return_value=KafkaRawMessage(
            value=KafkaMultiValueMessage(
                values={
                    "key": KafkaMessageValueRepresentation(
                        value={"a": 42.3, "b": "test"},
                        data_type=ExternalType.METADATA_ANY,
                    )
                },
                type=ExternalType.METADATA_ANY,
            )
            .json()
            .encode("utf8")
        ),
    ) as mocked_receive:
        yield mocked_receive


@pytest.mark.asyncio
async def test_kafka_adapter_consuming_any_single_value_message_via_execution_endpoint(
    two_kafka_configs,
    _db_with_pass_through_component,  # noqa: PT019
    open_async_test_client_with_kafka_adapter,
    mocked_receive_kafka_message,
):
    payload = {
        "id": "1946d5f8-44a8-724c-176f-16f3e49963af",  # Pass Through (ANY)
        "run_pure_plot_operators": False,
        "wiring": {
            "dashboard_positionings": [],
            "input_wirings": [
                {
                    "adapter_id": "kafka",
                    "ref_id": "base",
                    "ref_id_type": "THINGNODE",
                    "ref_key": "test_kafka_config2_metadata(any)",
                    "type": "metadata(any)",
                    "filters": {"message_value_key": ""},
                    "use_default_value": False,
                    "workflow_input_name": "input",
                }
            ],
            "output_wirings": [],
        },
    }

    resp = await open_async_test_client_with_kafka_adapter.post(
        "api/transformations/execute", json=payload
    )
    assert resp.status_code == 200
    assert resp.json()["error"] is None

    mocked_receive_kafka_message.assert_called_once_with(mock.ANY)

    assert resp.json()["output_results_by_output_name"]["output"] == {
        "a": 42.3,
        "b": "test",
    }


@pytest.mark.asyncio
async def test_kafka_adapter_consuming_any_multi_value_message_via_execution_endpoint(
    two_kafka_configs,
    _db_with_pass_through_component,  # noqa: PT019
    open_async_test_client_with_kafka_adapter,
    mocked_receive_multi_value_kafka_message,
):
    payload = {
        "id": "1946d5f8-44a8-724c-176f-16f3e49963af",  # Pass Through (ANY)
        "run_pure_plot_operators": False,
        "wiring": {
            "dashboard_positionings": [],
            "input_wirings": [
                {
                    "adapter_id": "kafka",
                    "ref_id": "base",
                    "ref_id_type": "THINGNODE",
                    "ref_key": "test_kafka_config2_metadata(any)",
                    "type": "metadata(any)",
                    "filters": {"message_value_key": "key"},
                    "use_default_value": False,
                    "workflow_input_name": "input",
                }
            ],
            "output_wirings": [],
        },
    }

    resp = await open_async_test_client_with_kafka_adapter.post(
        "api/transformations/execute", json=payload
    )
    assert resp.status_code == 200
    assert resp.json()["error"] is None

    mocked_receive_multi_value_kafka_message.assert_called_once_with(mock.ANY)

    assert resp.json()["output_results_by_output_name"]["output"] == {
        "a": 42.3,
        "b": "test",
    }


@pytest.mark.asyncio
async def test_kafka_adapter_consuming_any_multi_value_message_via_execution_endpoint_wrong_keys(
    two_kafka_configs,
    _db_with_pass_through_component,  # noqa: PT019
    open_async_test_client_with_kafka_adapter,
    mocked_receive_multi_value_kafka_message,
):
    payload = {
        "id": "1946d5f8-44a8-724c-176f-16f3e49963af",  # Pass Through (ANY)
        "run_pure_plot_operators": False,
        "wiring": {
            "dashboard_positionings": [],
            "input_wirings": [
                {
                    "adapter_id": "kafka",
                    "ref_id": "base",
                    "ref_id_type": "THINGNODE",
                    "ref_key": "test_kafka_config2_metadata(any)",
                    "type": "metadata(any)",
                    "filters": {"message_value_key": "WRONG_KEY"},
                    "use_default_value": False,
                    "workflow_input_name": "input",
                }
            ],
            "output_wirings": [],
        },
    }

    resp = await open_async_test_client_with_kafka_adapter.post(
        "api/transformations/execute", json=payload
    )
    assert resp.status_code == 200
    assert resp.json()["error"] is not None

    assert "missing" in resp.json()["error"]["message"].lower()
    assert resp.json()["error"]["type"] == "AdapterHandlingException"

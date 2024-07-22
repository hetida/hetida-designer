import string
import uuid
from unittest import mock

import pytest

from hetdesrun.adapters.kafka.consumption_mode import start_consumption_mode
from hetdesrun.adapters.kafka.models import KafkaSingleValueMessage
from hetdesrun.models.execution import ExecByIdBase
from hetdesrun.models.wiring import WorkflowWiring


class MockKafkaConsumer:
    """Simulate aiokafka consumer async message iterator

    Provides exactly one message for testing purposes.
    """

    def __init__(self, topic, msg_object):
        self.exec_msg_str = msg_object.json()
        self.topic = topic

    def __aiter__(self):
        self.sent = False
        return self

    async def __anext__(self):
        if not self.sent:
            self.sent = True
            mock_msg = mock.Mock
            mock_msg.value = self.exec_msg_str.encode("utf8")
            mock_msg.topic = self.topic
            mock_msg.key = b"exec3"
            mock_msg.partition = 42
            mock_msg.offset = 42
            mock_msg.timestamp = "unknown timestamp"
            return mock_msg
        raise StopAsyncIteration

    def assignment(self):
        return ("this consumer", 42)

    async def start(self):
        pass

    async def stop(self):
        pass


to_remove = string.punctuation + string.whitespace
translation_mapping = {ord(x): None for x in to_remove}


def string_without_whitespace(s):
    return s.translate(translation_mapping)


@pytest.mark.asyncio
async def test_consumption_mode(
    two_kafka_configs,
    _db_with_pass_through_component,  # noqa: PT019
    caplog,
):
    payload = KafkaSingleValueMessage(
        value={"value": {"something": "test"}, "data_type": "metadata(any)"}
    )
    # noqa: SIM117
    with mock.patch(  # noqa: SIM117
        "hetdesrun.webservice.config.runtime_config.hd_kafka_consumption_mode",
        new=ExecByIdBase(
            id=uuid.UUID("1946d5f8-44a8-724c-176f-16f3e49963af"),
            wiring=WorkflowWiring(
                input_wirings=[
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
                ]
            ),
        ),
    ):
        with mock.patch(
            "hetdesrun.adapters.kafka.consumption_mode.create_aiokafka_consumer",
            return_value=MockKafkaConsumer(
                topic="multi ts ingestion",
                msg_object=payload,
            ),
        ) as _mocked_ctx_consumer:
            await start_consumption_mode()

    assert "Execution Result" in caplog.text

    # Output that is not wired in consumption mode is just logged.
    # We therefore check that the passed through input occurs in the log
    assert string_without_whitespace(
        r"""
            "output_results_by_output_name": {
                "output": {
                    "something": "test"
                }
            }
        """
    ) in string_without_whitespace(caplog.text)

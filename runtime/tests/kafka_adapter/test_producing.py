from unittest import mock

import pandas as pd
import pytest

from hetdesrun.adapters.generic_rest.external_types import ExternalType
from hetdesrun.adapters.kafka.message import create_message
from hetdesrun.adapters.kafka.models import KafkaMessageValue, KafkaSingleValueMessage
from hetdesrun.adapters.kafka.send import send_kafka_message


@pytest.fixture
def mocked_send_encoded_message():
    with mock.patch(
        "hetdesrun.adapters.kafka.send.send_encoded_message"
    ) as mocked_send_encoded:
        yield mocked_send_encoded


@pytest.mark.asyncio
async def test_producing(two_kafka_configs, mocked_send_encoded_message):
    kf_msg_val = KafkaMessageValue(
        kafka_config_key="test_kafka_config2",
        message_identifier="",
        message_value_key=None,
        kafka_config=two_kafka_configs["test_kafka_config2"],
        external_type=ExternalType.MULTITSFRAME,
        output_name="some_output",
        value=pd.DataFrame(
            {
                "metric": [
                    "a",
                    "b",
                ],
                "timestamp": pd.to_datetime(
                    ["2024-01-01T00:00:00+00:00", "2024-01-01T01:00:00+00:00"]
                ),
                "value": [1.2, 3.9],
            }
        ),
    )

    msg_dict = {None: kf_msg_val}

    await send_kafka_message(msg_dict)
    mocked_send_encoded_message.assert_called_once_with(
        producer=mock.ANY,
        topic="multi ts ingestion",
        encoded_message=mock.ANY,
        key=None,
    )

    received_encoded_message = mocked_send_encoded_message.call_args.kwargs[
        "encoded_message"
    ]
    received_msg_object = KafkaSingleValueMessage.parse_raw(
        received_encoded_message.decode("utf8")
    )
    to_send_msg_object = create_message(msg_dict)
    to_send_msg_object.message_creation_timestamp = (
        received_msg_object.message_creation_timestamp
    )

    # compare after converting to json since DataFrames are not comparable by default:
    assert received_msg_object.json() == to_send_msg_object.json()

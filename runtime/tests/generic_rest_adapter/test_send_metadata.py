from unittest import mock

import pytest

from hetdesrun.adapters.exceptions import AdapterConnectionError
from hetdesrun.adapters.generic_rest import send_data
from hetdesrun.models.data_selection import FilteredSink


@pytest.mark.asyncio
async def test_end_to_end_send_only_single_metadata_data():
    response = mock.Mock()
    response.status_code = 200
    post_mock = mock.AsyncMock(return_value=response)

    with mock.patch(  # noqa: SIM117
        "hetdesrun.adapters.generic_rest.send_metadata.get_generic_rest_adapter_base_url",
        return_value="https://hetida.de",
    ):
        with mock.patch(
            "hetdesrun.adapters.generic_rest.send_metadata.httpx.AsyncClient.post",
            new=post_mock,
        ):
            # one frame
            await send_data(
                {
                    "inp_1": FilteredSink(
                        ref_id="sink_id_1",
                        type="metadata(int)",
                        ref_id_type="SOURCE",
                        ref_key="number",
                        filters={"filter_key": "filter_value"},
                    )
                },
                {"inp_1": 55},
                adapter_key="test_end_to_end_send_only_metadata_data_adapter_key",
            )
            assert post_mock.called  # we got through to actually posting!

            _, args, kwargs = post_mock.mock_calls[0]

            assert kwargs["json"] == {"key": "number", "value": 55, "dataType": "int"}
            assert kwargs["params"] == {"filter_key": "filter_value"}
            assert args[0] == "https://hetida.de/sources/sink_id_1/metadata/number"

            response.status_code = 400
            response.text = "my http error"
            with pytest.raises(AdapterConnectionError, match="my http error"):
                await send_data(
                    {
                        "inp_1": FilteredSink(
                            ref_id="sink_id_1",
                            type="metadata(int)",
                            ref_id_type="SOURCE",
                            ref_key="number",
                            filters={},
                        )
                    },
                    {"inp_1": 55},
                    adapter_key="test_end_to_end_send_only_metadata_data_adapter_key",
                )


@pytest.mark.asyncio
async def test_end_to_end_send_only_metadata_data():
    response = mock.Mock()
    response.status_code = 200
    post_mock = mock.AsyncMock(return_value=response)

    with mock.patch(  # noqa: SIM117
        "hetdesrun.adapters.generic_rest.send_metadata.get_generic_rest_adapter_base_url",
        return_value="https://hetida.de",
    ):
        with mock.patch(
            "hetdesrun.adapters.generic_rest.send_metadata.httpx.AsyncClient.post",
            new=post_mock,
        ):
            # more than one
            await send_data(
                {
                    "outp_1": FilteredSink(
                        ref_id="th_node_id",
                        type="metadata(string)",
                        ref_id_type="THINGNODE",
                        ref_key="description",
                        filters={"filter_key_1": "filter_value_1"},
                    ),
                    "outp_2": FilteredSink(
                        ref_id="sink_id",
                        type="metadata(float)",
                        ref_id_type="SINK",
                        ref_key="upper_lim",
                        filters={"filter_key_2": "filter_value_2"},
                    ),
                },
                {"outp_1": "some description", "outp_2": 47.8},
                adapter_key="test_end_to_end_send_only_metadata_data_adapter_key",
            )

            _, args_1, kwargs_1 = post_mock.mock_calls[0]
            _, args_2, kwargs_2 = post_mock.mock_calls[1]

            assert (
                {
                    "key": "description",
                    "value": "some description",
                    "dataType": "string",
                }
            ) in [kwargs_1["json"], kwargs_2["json"]]
            assert (
                {
                    "key": "upper_lim",
                    "value": 47.8,
                    "dataType": "float",
                }
            ) in [kwargs_1["json"], kwargs_2["json"]]
            assert {"filter_key_1": "filter_value_1"} in [kwargs_1["params"], kwargs_2["params"]]
            assert {"filter_key_2": "filter_value_2"} in [kwargs_1["params"], kwargs_2["params"]]
            assert "https://hetida.de/thingNodes/th_node_id/metadata/description" in [
                args_1[0],
                args_2[0],
            ]

            assert "https://hetida.de/sinks/sink_id/metadata/upper_lim" in [
                args_1[0],
                args_2[0],
            ]

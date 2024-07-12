from unittest import mock

import numpy as np
import pandas as pd
import pytest

from hetdesrun.adapters.exceptions import AdapterOutputDataError
from hetdesrun.adapters.generic_rest import send_data
from hetdesrun.adapters.generic_rest.external_types import ExternalType
from hetdesrun.adapters.generic_rest.load_framelike import decode_attributes
from hetdesrun.models.data_selection import FilteredSink


@pytest.mark.asyncio
async def test_end_to_end_send_only_timeseries_data_works():
    response = mock.Mock()
    response.status_code = 200
    post_mock = mock.AsyncMock(return_value=response)

    with (
        mock.patch(  # noqa: SIM117
            "hetdesrun.adapters.generic_rest.send_framelike.get_generic_rest_adapter_base_url",
            return_value="https://hetida.de",
        ),
        mock.patch(
            "hetdesrun.adapters.generic_rest.send_ts_data.AsyncClient.post",
            new=post_mock,
        ),
    ):
        ts_1 = pd.Series(
            [1.2, 3.4, 5.9],
            index=pd.to_datetime(
                [
                    "2020-01-15T00:00:00.000Z",
                    "2020-01-15T01:00:00.000Z",
                    "2020-01-15T02:00:00.000Z",
                ]
            ),
        )

        # one timeseries
        await send_data(
            {
                "outp_1": FilteredSink(
                    ref_id="sink_id_1",
                    type="timeseries(float)",
                    filters={"filter_key": "filter_value"},
                )
            },
            {"outp_1": ts_1},
            adapter_key="test_end_to_end_send_only_timeseries_data_adapter_key",
        )
        assert post_mock.called  # we got through to actually posting!

        _, _, kwargs = post_mock.mock_calls[0]
        assert kwargs["params"] == [
            ("timeseriesId", "sink_id_1"),
            ("filter_key", "filter_value"),
        ]
        assert kwargs["json"] == [
            {"timestamp": "2020-01-15T00:00:00.000000000Z", "value": 1.2},
            {"timestamp": "2020-01-15T01:00:00.000000000Z", "value": 3.4},
            {"timestamp": "2020-01-15T02:00:00.000000000Z", "value": 5.9},
        ]

        # more than one timeseries
        ts_2 = pd.Series(
            ["first", "second"],
            index=pd.to_datetime(
                [
                    "2020-01-15T00:00:00.000Z",
                    "2020-01-15T01:00:00.000Z",
                ]
            ),
        )

        await send_data(
            {
                "outp_1": FilteredSink(
                    ref_id="sink_id_1",
                    type="timeseries(float)",
                    filters={"filter_key_1": "filter_value_1"},
                ),
                "outp_2": FilteredSink(
                    ref_id="sink_id_2",
                    type=ExternalType.TIMESERIES_STR,
                    filters={"filter_key_2": "filter_value_2"},
                ),
            },
            {
                "outp_1": ts_1,
                "outp_2": ts_2,
            },
            adapter_key="test_end_to_end_send_only_timeseries_data_adapter_key",
        )

        # note: can be async!
        _, _, kwargs_1 = post_mock.mock_calls[1]
        _, _, kwargs_2 = post_mock.mock_calls[2]
        assert (len(kwargs_1["json"]) == 3) or (len(kwargs_2["json"]) == 3)
        assert (len(kwargs_1["json"]) == 2) or (len(kwargs_2["json"]) == 2)
        assert kwargs_1["params"] == [
            ("timeseriesId", "sink_id_1"),
            ("filter_key_1", "filter_value_1"),
        ] or kwargs_2["params"] == [
            ("timeseriesId", "sink_id_1"),
            ("filter_key_1", "filter_value_1"),
        ]
        assert kwargs_1["params"] == [
            ("timeseriesId", "sink_id_2"),
            ("filter_key_2", "filter_value_2"),
        ] or kwargs_2["params"] == [
            ("timeseriesId", "sink_id_2"),
            ("filter_key_2", "filter_value_2"),
        ]

        # a timeseries with attributes
        ts_3 = pd.Series(
            [1.2, 3.4, np.nan],
            index=pd.to_datetime(
                [
                    "2020-01-15T00:00:00.000Z",
                    "2020-01-15T01:00:00.000Z",
                    "2020-01-15T02:00:00.000Z",
                ]
            ),
        )
        ts_3_attrs = {"a": 1}
        ts_3.attrs = ts_3_attrs
        await send_data(
            {
                "outp_1": FilteredSink(ref_id="sink_id_1", type="timeseries(float)", filters={}),
            },
            {"outp_1": ts_3},
            adapter_key="test_end_to_end_send_only_timeseries_data_adapter_key",
        )
        # note: can be async!
        _, _, kwargs_3 = post_mock.mock_calls[3]

        assert kwargs_3["json"][2]["value"] is None  # np.nan comes through as null
        assert "Data-Attributes" in kwargs_3["headers"]
        received_attrs = decode_attributes(kwargs_3["headers"]["Data-Attributes"])
        for key, value in ts_3_attrs.items():
            assert key in received_attrs
            assert received_attrs[key] == value

        ts_4 = pd.Series([])
        await send_data(
            {"outp_4": FilteredSink(ref_id="sink_id_4", type="timeseries(float)")},
            {"outp_4": ts_4},
            adapter_key="test_end_to_end_send_only_timeseries_data_adapter_key",
        )
        _, _, kwargs_4 = post_mock.mock_calls[4]

        assert kwargs_4["json"] == []


@pytest.mark.asyncio
async def test_end_to_end_send_only_timeseries_data_exception_handling():
    ts_5 = pd.Series([1.0], index=["not a timestamp"])
    with pytest.raises(AdapterOutputDataError, match="does not have DatetimeTZDtype dtype"):
        await send_data(
            {"outp_5": FilteredSink(ref_id="sink_id_5", type="timeseries(float)")},
            {"outp_5": ts_5},
            adapter_key="test_end_to_end_send_only_timeseries_data_adapter_key",
        )

    ts_6 = pd.Series([1.0], index=[pd.Timestamp("2019-08-01T15:45:36+01:00")])
    with pytest.raises(AdapterOutputDataError, match="does not have UTC timezone"):
        await send_data(
            {"outp_6": FilteredSink(ref_id="sink_id_6", type="timeseries(float)")},
            {"outp_6": ts_6},
            adapter_key="test_end_to_end_send_only_timeseries_data_adapter_key",
        )

    ts_7 = pd.Series(["not a float"], index=[pd.Timestamp("2019-08-01T15:45:36Z")])
    with pytest.raises(AdapterOutputDataError, match="Expected float"):
        await send_data(
            {"outp_7": FilteredSink(ref_id="sink_id_7", type="timeseries(float)")},
            {"outp_7": ts_7},
            adapter_key="test_end_to_end_send_only_timeseries_data_adapter_key",
        )

    ts_8 = pd.Series(["not an int"], index=[pd.Timestamp("2019-08-01T15:45:36Z")])
    with pytest.raises(AdapterOutputDataError, match="Expected int"):
        await send_data(
            {"outp_8": FilteredSink(ref_id="sink_id_8", type="timeseries(int)")},
            {"outp_8": ts_8},
            adapter_key="test_end_to_end_send_only_timeseries_data_adapter_key",
        )

    ts_9 = pd.Series(["not a bool"], index=[pd.Timestamp("2019-08-01T15:45:36Z")])
    with pytest.raises(AdapterOutputDataError, match="Expected bool"):
        await send_data(
            {"outp_9": FilteredSink(ref_id="sink_id_9", type="timeseries(bool)")},
            {"outp_9": ts_9},
            adapter_key="test_end_to_end_send_only_timeseries_data_adapter_key",
        )

    ts_10 = pd.Series([1.0], index=[pd.Timestamp("2019-08-01T15:45:36Z")])
    with pytest.raises(AdapterOutputDataError, match="Expected string"):
        await send_data(
            {"outp_10": FilteredSink(ref_id="sink_id_10", type="timeseries(string)")},
            {"outp_10": ts_10},
            adapter_key="test_end_to_end_send_only_timeseries_data_adapter_key",
        )

    no_ts = pd.DataFrame(
        {
            "metric": ["a"],
            "timestamp": [pd.Timestamp("2019-08-01T15:45:36Z")],
            "value": [1.0],
        }
    )
    with pytest.raises(AdapterOutputDataError, match="Did not receive Pandas Series"):
        await send_data(
            {"outp_11": FilteredSink(ref_id="sink_id_11", type="timeseries(float)")},
            {"outp_11": no_ts},
            adapter_key="test_end_to_end_send_only_timeseries_data_adapter_key",
        )

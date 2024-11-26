from unittest import mock

import numpy as np
import pandas as pd
import pytest

from hetdesrun.adapters.exceptions import AdapterClientWiringInvalidError, AdapterOutputDataError
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


@pytest.mark.parametrize(
    ("series_input", "series_type", "error_msg"),
    [
        pytest.param(
            pd.Series([1.0], index=["not a timestamp"]),
            "timeseries(float)",
            "does not have DatetimeTZDtype dtype",
            id="no DatetimeTZDtype",
        ),
        pytest.param(
            pd.Series([1.0], index=[pd.Timestamp("2019-08-01T15:45:36+01:00")]),
            "timeseries(float)",
            "does not have UTC timezone",
            id="no UTC zone",
        ),
        pytest.param(
            pd.Series(["not a float"], index=[pd.Timestamp("2019-08-01T15:45:36Z")]),
            "timeseries(float)",
            "Expected float",
            id="not a float",
        ),
        pytest.param(
            pd.Series(["not an int"], index=[pd.Timestamp("2019-08-01T15:45:36Z")]),
            "timeseries(int)",
            "Expected int",
            id="not a int",
        ),
        pytest.param(
            pd.Series(["not a bool"], index=[pd.Timestamp("2019-08-01T15:45:36Z")]),
            "timeseries(bool)",
            "Expected bool",
            id="not a bool",
        ),
        pytest.param(
            pd.Series([1.0], index=[pd.Timestamp("2019-08-01T15:45:36Z")]),
            "timeseries(string)",
            "Expected string",
            id="not a string",
        ),
        pytest.param(
            pd.Series(["not a numeric"], index=[pd.Timestamp("2019-08-01T15:45:36Z")]),
            "timeseries(numeric)",
            "Expected int or float",
            id="not a numeric",
        ),
        pytest.param(
            pd.DataFrame(
                {
                    "metric": ["a"],
                    "timestamp": [pd.Timestamp("2019-08-01T15:45:36Z")],
                    "value": [1.0],
                }
            ),
            "timeseries(float)",
            "Did not receive Pandas Series",
            id="not a series",
        ),
    ],
)
@pytest.mark.asyncio
async def test_end_to_end_send_only_timeseries_data_exception_handling(
    series_input, series_type, error_msg
):
    with pytest.raises(AdapterOutputDataError, match=error_msg):
        await send_data(
            {"outp": FilteredSink(ref_id="sink", type=series_type)},
            {"outp": series_input},
            adapter_key="test_end_to_end_send_only_timeseries_data_adapter_key",
        )


@pytest.mark.parametrize(
    ("series_input", "dtype"),
    [
        pytest.param([1, 3, 5], "timeseries(numeric)", id="numerical as int"),
        pytest.param([1.5, 3.5, 5.5], "timeseries(numeric)", id="numerical as float"),
        pytest.param([1, 3, 5], "timeseries(int)", id="int as int"),
        pytest.param([1.5, 3.5, 5.5], "timeseries(float)", id="float as float"),
        pytest.param(["1.5", "3.5", "5.5"], "timeseries(string)", id="sting as string"),
    ],
)
@pytest.mark.asyncio
async def test_send_data_good(series_input, dtype):
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
            series_input,
            index=pd.to_datetime(
                [
                    "2020-01-15T00:00:00.000Z",
                    "2020-01-15T01:00:00.000Z",
                    "2020-01-15T02:00:00.000Z",
                ]
            ),
        )

        await send_data(
            {
                "outp_1": FilteredSink(
                    ref_id="sink_id_1",
                    type=dtype,
                    filters={"filter_key": "filter_value"},
                )
            },
            {"outp_1": ts_1},
            adapter_key="test_end_to_end_send_only_timeseries_data_adapter_key",
        )
        assert post_mock.called  # we got through to actually posting!


@pytest.mark.parametrize(
    ("series_input", "dtype", "error_type"),
    [
        pytest.param(
            ["1.5", "3.5", "5.5"],
            "metadata(float)",
            AdapterClientWiringInvalidError,
            id="metadata as string",
        ),
        pytest.param(
            ["1.5", "3.5", "5.5"],
            "timeseries(Any)",
            AdapterClientWiringInvalidError,
            id="Any as string",
        ),
    ],
)
@pytest.mark.asyncio
async def test_send_data_undefined_type(series_input, dtype, error_type):
    ts_1 = pd.Series(
        series_input,
        index=pd.to_datetime(
            [
                "2020-01-15T00:00:00.000Z",
                "2020-01-15T01:00:00.000Z",
                "2020-01-15T02:00:00.000Z",
            ]
        ),
    )

    with pytest.raises(error_type):
        await send_data(
            {
                "outp_1": FilteredSink(
                    ref_id="sink_id_1",
                    type=dtype,
                    filters={"filter_key": "filter_value"},
                )
            },
            {"outp_1": ts_1},
            adapter_key="test_end_to_end_send_only_timeseries_data_adapter_key",
        )

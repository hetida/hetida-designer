from unittest import mock

import numpy as np
import pandas as pd
import pytest

from hetdesrun.adapters.exceptions import AdapterOutputDataError
from hetdesrun.adapters.generic_rest import send_data
from hetdesrun.adapters.generic_rest.external_types import ExternalType
from hetdesrun.adapters.generic_rest.load_framelike import decode_attributes
from hetdesrun.models.data_selection import FilteredSink


@pytest.fixture
def mocked_url():
    with mock.patch(  # noqa: SIM117
        "hetdesrun.adapters.generic_rest.send_framelike.get_generic_rest_adapter_base_url",
        return_value="https://hetida.de",
    ) as _fixutre:
        yield _fixutre


@pytest.fixture()
def mocked_api():
    post_mock = mock.AsyncMock(return_value=mock.Mock(status_code=200))
    with mock.patch(
        "hetdesrun.adapters.generic_rest.send_singletsframe.AsyncClient.post",
        new=post_mock,
    ) as _fixutre:
        yield _fixutre


@pytest.mark.asyncio
async def test_end_to_end_send_only_singletsframe_data(mocked_url, mocked_api) -> None:
    """A SingleTSFrame is sent as records without a metric field, with all value dimensions"""
    stsf_1 = pd.DataFrame(
        {
            "timestamp": [
                pd.Timestamp("2019-08-01T15:45:36.000Z"),
                pd.Timestamp("2019-08-01T15:45:37.000Z"),
            ],
            "value": [1.0, 1.2],
            "state": ["ok", "suspicious"],
        }
    )
    stsf_1.attrs = {
        "dataset_metadata": {"single_metric": "abc.temp"},
    }
    stsf_2 = pd.DataFrame(
        {
            "timestamp": [
                pd.Timestamp("2019-08-01T15:45:36.000Z"),
                pd.Timestamp("2019-08-01T15:45:37.000Z"),
            ],
            "value": [np.nan, "text"],
        }
    )

    await send_data(
        {
            "outp_1": FilteredSink(
                ref_id="sink_id_1",
                type="singletsframe",
                filters={"filter_key_1": "filter_value_1"},
            ),
            "outp_2": FilteredSink(
                ref_id="sink_id_2",
                type=ExternalType.SINGLETSFRAME,
                filters={},
            ),
            "outp_3": FilteredSink(
                ref_id="sink_id_3",
                type=ExternalType.SINGLETSFRAME,
                filters={},
            ),
        },
        {"outp_1": stsf_1, "outp_2": stsf_2, "outp_3": pd.DataFrame([])},
        adapter_key="test_end_to_end_send_only_singletsframe_data",
    )

    assert mocked_api.called  # we got through to actually posting!

    _, _, kwargs_1 = mocked_api.mock_calls[0]
    assert kwargs_1["params"] == [
        ("id", "sink_id_1"),
        ("filter_key_1", "filter_value_1"),
    ]
    assert kwargs_1["json"] == [
        {
            "timestamp": "2019-08-01T15:45:36.000000000+00:00",
            "value": 1.0,
            "state": "ok",
        },
        {
            "timestamp": "2019-08-01T15:45:37.000000000+00:00",
            "value": 1.2,
            "state": "suspicious",
        },
    ]
    assert "Data-Attributes" in kwargs_1["headers"]
    received_attrs = decode_attributes(kwargs_1["headers"]["Data-Attributes"])
    assert received_attrs["dataset_metadata"]["single_metric"] == "abc.temp"

    _, _, kwargs_2 = mocked_api.mock_calls[1]
    assert kwargs_2["json"] == [
        {"timestamp": "2019-08-01T15:45:36.000000000+00:00", "value": None},
        {"timestamp": "2019-08-01T15:45:37.000000000+00:00", "value": "text"},
    ]
    assert "Data-Attributes" not in kwargs_2["headers"]

    _, _, kwargs_3 = mocked_api.mock_calls[2]
    assert kwargs_3["json"] == []


@pytest.mark.asyncio
async def test_send_singletsframe_allows_metric_column_as_value_dimension(
    mocked_url, mocked_api
) -> None:
    stsf = pd.DataFrame(
        {
            "timestamp": [pd.Timestamp("2019-08-01T15:45:36.000Z")],
            "metric": ["not interpreted as a metric"],
        }
    )

    await send_data(
        {"outp": FilteredSink(ref_id="sink_id", type="singletsframe", filters={})},
        {"outp": stsf},
        adapter_key="test_send_singletsframe_allows_metric_column",
    )

    _, _, kwargs = mocked_api.mock_calls[0]
    assert kwargs["json"] == [
        {
            "timestamp": "2019-08-01T15:45:36.000000000+00:00",
            "metric": "not interpreted as a metric",
        }
    ]


@pytest.mark.asyncio
async def test_send_singletsframe_no_df(mocked_url, mocked_api) -> None:
    no_stsf = pd.Series([1.0], index=pd.to_datetime(["2019-08-01T15:45:36Z"]))
    with pytest.raises(AdapterOutputDataError, match="Did not receive Pandas DataFrame"):
        await send_data(
            {"outp": FilteredSink(ref_id="sink_id", type="singletsframe", filters={})},
            {"outp": no_stsf},
            adapter_key="test_send_singletsframe_no_df",
        )


@pytest.mark.asyncio
async def test_send_singletsframe_missing_timestamp_column(mocked_url, mocked_api) -> None:
    stsf = pd.DataFrame({"timestamps": [pd.Timestamp("2019-08-01T15:45:36Z")], "value": [1.0]})
    with pytest.raises(AdapterOutputDataError, match="required column"):
        await send_data(
            {"outp": FilteredSink(ref_id="sink_id", type="singletsframe", filters={})},
            {"outp": stsf},
            adapter_key="test_send_singletsframe_missing_timestamp_column",
        )


@pytest.mark.asyncio
async def test_send_singletsframe_no_value_column(mocked_url, mocked_api) -> None:
    stsf = pd.DataFrame({"timestamp": [pd.Timestamp("2019-08-01T15:45:36Z")]})
    with pytest.raises(AdapterOutputDataError, match="at least one value column"):
        await send_data(
            {"outp": FilteredSink(ref_id="sink_id", type="singletsframe", filters={})},
            {"outp": stsf},
            adapter_key="test_send_singletsframe_no_value_column",
        )


@pytest.mark.asyncio
async def test_send_singletsframe_null_timestamps(mocked_url, mocked_api) -> None:
    stsf = pd.DataFrame(
        {
            "timestamp": [pd.Timestamp("2019-08-01T15:45:36Z"), None],
            "value": [1.0, 2.0],
        }
    )
    with pytest.raises(AdapterOutputDataError, match="null values in the column 'timestamp'"):
        await send_data(
            {"outp": FilteredSink(ref_id="sink_id", type="singletsframe", filters={})},
            {"outp": stsf},
            adapter_key="test_send_singletsframe_null_timestamps",
        )


@pytest.mark.asyncio
async def test_send_singletsframe_non_utc_timestamps(mocked_url, mocked_api) -> None:
    stsf = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(["2019-08-01T15:45:36+01:00"]),
            "value": [1.0],
        }
    )
    with pytest.raises(AdapterOutputDataError, match="UTC timezone"):
        await send_data(
            {"outp": FilteredSink(ref_id="sink_id", type="singletsframe", filters={})},
            {"outp": stsf},
            adapter_key="test_send_singletsframe_non_utc_timestamps",
        )

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
        "hetdesrun.adapters.generic_rest.send_multitsframe.AsyncClient.post",
        new=post_mock,
    ) as _fixutre:
        yield _fixutre


@pytest.mark.asyncio
async def test_end_to_end_send_only_multitsframe_data(mocked_url, mocked_api) -> None:
    mtsf_1 = pd.DataFrame(
        {
            "metric": ["a", "b", "c", "a", "b", "c", "a", "b", "c"],
            "timestamp": [
                pd.Timestamp("2019-08-01T15:45:36.000Z"),
                pd.Timestamp("2019-08-01T15:45:37.000Z"),
                pd.Timestamp("2019-08-01T15:45:37.000Z"),
                pd.Timestamp("2019-08-01T15:45:46.000Z"),
                pd.Timestamp("2019-08-01T15:45:46.000Z"),
                pd.Timestamp("2019-08-01T15:45:47.000Z"),
                pd.Timestamp("2019-08-01T15:45:56.000Z"),
                pd.Timestamp("2019-08-01T15:45:57.000Z"),
                pd.Timestamp("2019-08-01T15:45:58.000Z"),
            ],
            "value": [1.0, 1.2, 0.5, 1.9, 1.3, 0.2, 1.5, 1.7, 0.1],
        }
    )
    mtsf_1.attrs = {
        "from": "2019-08-01T15:45:30.000Z",
        "to": "2019-08-01T15:46:00.000Z",
    }
    mtsf_2 = pd.DataFrame(
        {
            "metric": ["a", "d", "e", "a", "a", "e"],
            "timestamp": [
                pd.Timestamp("2019-08-01T15:45:36.000Z"),
                pd.Timestamp("2019-08-01T15:45:37.000Z"),
                pd.Timestamp("2019-08-01T15:45:37.000Z"),
                pd.Timestamp("2019-08-01T15:45:46.000Z"),
                pd.Timestamp("2019-08-01T15:45:56.000Z"),
                pd.Timestamp("2019-08-01T15:45:57.000Z"),
            ],
            "value": [1.0, np.nan, None, 1.9, 1.5, "text"],
        }
    )
    await send_data(
        {
            "outp_1": FilteredSink(
                ref_id="sink_id_1",
                type="multitsframe",
                filters={"filter_key_1": "filter_value_1"},
            ),
            "outp_2": FilteredSink(
                ref_id="sink_id_2",
                type=ExternalType.MULTITSFRAME,
                filters={"filter_key_2": "filter_value_2"},
            ),
            "outp_3": FilteredSink(
                ref_id="sink_id_3",
                type=ExternalType.MULTITSFRAME,
                filters={"filter_key_3": "filter_value_3"},
            ),
        },
        {"outp_1": mtsf_1, "outp_2": mtsf_2, "outp_3": pd.DataFrame([])},
        adapter_key="test_end_to_end_send_only_multitsframe_data",
    )
    assert mocked_api.called  # we got through to actually posting!
    _, _, kwargs_1 = mocked_api.mock_calls[0]
    assert kwargs_1["params"] == [
        ("id", "sink_id_1"),
        ("filter_key_1", "filter_value_1"),
    ]
    assert kwargs_1["json"] == [
        {
            "timestamp": "2019-08-01T15:45:36.000000000Z",
            "metric": "a",
            "value": 1.0,
        },
        {
            "timestamp": "2019-08-01T15:45:37.000000000Z",
            "metric": "b",
            "value": 1.2,
        },
        {
            "timestamp": "2019-08-01T15:45:37.000000000Z",
            "metric": "c",
            "value": 0.5,
        },
        {
            "timestamp": "2019-08-01T15:45:46.000000000Z",
            "metric": "a",
            "value": 1.9,
        },
        {
            "timestamp": "2019-08-01T15:45:46.000000000Z",
            "metric": "b",
            "value": 1.3,
        },
        {
            "timestamp": "2019-08-01T15:45:47.000000000Z",
            "metric": "c",
            "value": 0.2,
        },
        {
            "timestamp": "2019-08-01T15:45:56.000000000Z",
            "metric": "a",
            "value": 1.5,
        },
        {
            "timestamp": "2019-08-01T15:45:57.000000000Z",
            "metric": "b",
            "value": 1.7,
        },
        {
            "timestamp": "2019-08-01T15:45:58.000000000Z",
            "metric": "c",
            "value": 0.1,
        },
    ]
    assert "Data-Attributes" in kwargs_1["headers"]
    received_attrs = decode_attributes(kwargs_1["headers"]["Data-Attributes"])
    assert received_attrs["from"] == "2019-08-01T15:45:30.000Z"
    assert received_attrs["to"] == "2019-08-01T15:46:00.000Z"

    _, _, kwargs_2 = mocked_api.mock_calls[1]
    assert kwargs_2["params"] == [
        ("id", "sink_id_2"),
        ("filter_key_2", "filter_value_2"),
    ]
    assert kwargs_2["json"] == [
        {
            "timestamp": "2019-08-01T15:45:36.000000000Z",
            "metric": "a",
            "value": 1.0,
        },
        {
            "timestamp": "2019-08-01T15:45:37.000000000Z",
            "metric": "d",
            "value": None,
        },
        {
            "timestamp": "2019-08-01T15:45:37.000000000Z",
            "metric": "e",
            "value": None,
        },
        {
            "timestamp": "2019-08-01T15:45:46.000000000Z",
            "metric": "a",
            "value": 1.9,
        },
        {
            "timestamp": "2019-08-01T15:45:56.000000000Z",
            "metric": "a",
            "value": 1.5,
        },
        {
            "timestamp": "2019-08-01T15:45:57.000000000Z",
            "metric": "e",
            "value": "text",
        },
    ]
    assert "Data-Attributes" not in kwargs_2["headers"]

    _, _, kwargs_3 = mocked_api.mock_calls[2]
    assert kwargs_3["params"] == [
        ("id", "sink_id_3"),
        ("filter_key_3", "filter_value_3"),
    ]
    assert kwargs_3["json"] == []


@pytest.mark.asyncio
async def test_send_multitsframe_no_df(mocked_url, mocked_api) -> None:
    no_mts = pd.Series([1.0], index=pd.to_datetime(["2019-08-01T15:45:36Z"]))
    with pytest.raises(AdapterOutputDataError, match="Did not receive Pandas DataFrame"):
        await send_data(
            {
                "outp": FilteredSink(
                    ref_id="sink_id",
                    type="multitsframe",
                    filters={},
                )
            },
            {"outp": no_mts},
            adapter_key="test_end_to_end_send_only_multitsframe_data",
        )


@pytest.mark.asyncio
async def test_send_multitsframe_wrong_colnames(mocked_url, mocked_api) -> None:
    mts = pd.DataFrame(
        {
            "any_column_name": ["a"],
            "timestamps": [pd.Timestamp("2019-08-01T15:45:36Z")],
            "value": [1.0],
        }
    )
    with pytest.raises(
        AdapterOutputDataError, match=r"column names.* don't contain"
    ):  # The column names { {*df.columns} } don't contain
        await send_data(
            {"outp": FilteredSink(ref_id="sink_id", type="multitsframe")},
            {"outp": mts},
            adapter_key="test_end_to_end_send_only_multitsframe_data",
        )


@pytest.mark.asyncio
async def test_send_multitsframe_too_few_columns(mocked_url, mocked_api) -> None:
    mts = pd.DataFrame(
        {
            "timestamp": [pd.Timestamp("2019-08-01T15:45:36Z")],
            "value": [1.0],
        }
    )
    with pytest.raises(
        AdapterOutputDataError, match=r"requires at least 3 columns"
    ):  # The column names { {*df.columns} } don't contain
        await send_data(
            {"outp": FilteredSink(ref_id="sink_id", type="multitsframe")},
            {"outp": mts},
            adapter_key="test_end_to_end_send_only_multitsframe_data",
        )


@pytest.mark.asyncio
async def test_send_multitsframe_nan_in_metric(mocked_url, mocked_api) -> None:
    mts = pd.DataFrame(
        {
            "metric": [np.nan],
            "timestamp": [pd.Timestamp("2019-08-01T15:45:36Z")],
            "value": [1.0],
        }
    )
    with pytest.raises(AdapterOutputDataError, match=r"null values in.*metric"):
        await send_data(
            {"outp": FilteredSink(ref_id="sink_id", type="multitsframe")},
            {"outp": mts},
            adapter_key="test_end_to_end_send_only_multitsframe_data",
        )


@pytest.mark.asyncio
async def test_send_multitsframe_nan_in_timestamp(mocked_url, mocked_api) -> None:
    mts = pd.DataFrame({"metric": ["a"], "timestamp": [pd.NaT], "value": [1.0]})
    with pytest.raises(AdapterOutputDataError, match=r"null values in.*timestamp"):
        await send_data(
            {"outp": FilteredSink(ref_id="sink_id", type="multitsframe")},
            {"outp": mts},
            adapter_key="test_end_to_end_send_only_multitsframe_data",
        )


@pytest.mark.asyncio
async def test_send_multitsframe_no_timestampformat(mocked_url, mocked_api) -> None:
    mts = pd.DataFrame({"metric": ["a"], "timestamp": ["not a timestamp"], "value": [1.0]})
    with pytest.raises(AdapterOutputDataError, match="does not have DatetimeTZDtype dtype"):
        await send_data(
            {"outp": FilteredSink(ref_id="sink_id", type="multitsframe")},
            {"outp": mts},
            adapter_key="test_end_to_end_send_only_multitsframe_data",
        )


@pytest.mark.asyncio
async def test_send_multitsframe_no_utc(mocked_url, mocked_api) -> None:
    mts = pd.DataFrame(
        {
            "metric": ["a"],
            "timestamp": [pd.Timestamp("2019-08-01T15:45:36+01:00")],
            "value": [1.0],
        }
    )
    with pytest.raises(AdapterOutputDataError, match="does not have UTC timezone"):
        await send_data(
            {"outp": FilteredSink(ref_id="sink_id", type="multitsframe")},
            {"outp": mts},
            adapter_key="test_end_to_end_send_only_multitsframe_data",
        )


@pytest.mark.asyncio
async def test_send_multitsframe_extra_columns(mocked_url, mocked_api) -> None:
    mts = pd.DataFrame(
        {
            "metric": ["a"],
            "timestamp": [pd.Timestamp("2019-08-01T15:45:36Z")],
            "value": [1.0],
            "min": [0.0],
        }
    )

    await send_data(
        {"outp": FilteredSink(ref_id="sink_id", type="multitsframe")},
        {"outp": mts},
        adapter_key="test_end_to_end_send_only_multitsframe_data",
    )

    assert mocked_api.called  # we got through to actually posting!

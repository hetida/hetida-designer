import io
from unittest import mock

import pandas as pd
import pytest

from hetdesrun.adapters.generic_rest import load_data
from hetdesrun.adapters.generic_rest.external_types import ExternalType
from hetdesrun.adapters.generic_rest.load_dataframe import (
    load_single_dataframe_from_adapter,
)
from hetdesrun.adapters.generic_rest.send_framelike import encode_attributes
from hetdesrun.models.data_selection import FilteredSource


@pytest.mark.asyncio
async def test_load_single_dataframe_from_adapter() -> None:
    with mock.patch(
        "hetdesrun.adapters.generic_rest.load_dataframe.load_framelike_data",
    ) as load_framelike_mock:
        await load_single_dataframe_from_adapter(
            FilteredSource(
                ref_id="id_1",
                type="dataframe",
                filters={
                    "from": "2019-08-01T15:45:30.000Z",
                    "to": "2019-08-01T15:46:00.000Z",
                    "filter_key": "filter_value",
                },
            ),
            adapter_key="load_dataframe",
        )

        load_framelike_mock.assert_awaited_once_with(
            [
                FilteredSource(
                    ref_id="id_1",
                    type="dataframe",
                    filters={
                        "from": "2019-08-01T15:45:30.000Z",
                        "to": "2019-08-01T15:46:00.000Z",
                        "filter_key": "filter_value",
                    },
                )
            ],
            additional_params=[
                ("from", "2019-08-01T15:45:30.000Z"),
                ("to", "2019-08-01T15:46:00.000Z"),
                ("filter_key", "filter_value"),
            ],
            adapter_key="load_dataframe",
            endpoint="dataframe",
        )


async def mock_load_generic_rest_dataframe_data(*args, **kwargs):
    return pd.DataFrame(
        {
            "a": [1.0, 2.0, 3.4, 5.8],
            "b": [2.58, 3.4, 10.2, 11.5],
        }
    )


@pytest.mark.asyncio
async def test_end_to_end_load_only_dataframe_data():
    with mock.patch(
        "hetdesrun.adapters.generic_rest.load_dataframe.load_single_dataframe_from_adapter",
        new=mock_load_generic_rest_dataframe_data,
    ):
        # one
        loaded_data = await load_data(
            {"inp_1": FilteredSource(ref_id="id_1", type="dataframe")},
            adapter_key="end_to_end_only_dataframe_data",
        )

        assert len(loaded_data) == 1
        assert isinstance(loaded_data["inp_1"], pd.DataFrame)
        assert loaded_data["inp_1"].shape == (4, 2)

        # more than one
        loaded_data = await load_data(
            {
                "inp_1": FilteredSource(ref_id="id_1", type=ExternalType.DATAFRAME),
                "inp_2": FilteredSource(ref_id="id_1", type=ExternalType.DATAFRAME),
            },
            adapter_key="end_to_end_only_dataframe_data",
        )

        assert len(loaded_data) == 2
        assert isinstance(loaded_data["inp_2"], pd.DataFrame)
        assert loaded_data["inp_2"].shape == (4, 2)


async def mock_load_generic_rest_dataframe_with_timestamp_col(*args, **kwargs):
    return pd.DataFrame(
        {
            "a": [1.0, 2.0, 3.4, 5.8],
            "timestamp": [
                "2021-01-01T01:00:00.000Z",
                "2021-01-02T01:00:00.000Z",
                "2021-01-03T01:00:00.000Z",
                "2021-01-04T01:00:00.000Z",
            ],
        }
    )


@pytest.mark.asyncio
async def test_end_to_end_load_dataframe_data_with_timestamp_column():
    resp_mock = mock.Mock()
    resp_mock.status_code = 200
    resp_mock.raw = io.StringIO(
        """\n
        {"timestamp": "2020-03-11T13:45:18.194000000Z", "a": 42.3}
        {"timestamp": "2020-03-11T14:45:18.194000000Z", "a": 41.7}
        {"timestamp": "2020-03-11T15:45:18.194000000Z", "a": 15.89922333}
        """
    )
    resp_mock.headers = {}
    with mock.patch(  # noqa: SIM117
        "hetdesrun.adapters.generic_rest.load_framelike.get_generic_rest_adapter_base_url",
        return_value="https://hetida.de",
    ):
        with mock.patch(
            "hetdesrun.adapters.generic_rest.load_framelike.requests.Session.get",
            return_value=resp_mock,
        ):
            loaded_data = await load_data(
                {
                    "inp_1": FilteredSource(ref_id="id_1", type=ExternalType.DATAFRAME),
                },
                adapter_key="end_to_end_only_dataframe_data",
            )

            assert len(loaded_data) == 1
            assert isinstance(loaded_data["inp_1"], pd.DataFrame)
            assert loaded_data["inp_1"].shape == (3, 2)
            assert isinstance(loaded_data["inp_1"].index.dtype, pd.DatetimeTZDtype)


@pytest.mark.asyncio
async def test_end_to_end_load_dataframe_data_with_attrs():
    resp_mock = mock.Mock()
    resp_mock.status_code = 200
    attributes = {"b": 2}
    resp_mock.headers = {"Data-Attributes": encode_attributes(attributes)}
    resp_mock.raw = io.StringIO(
        """\n
        {"timestamp": "2020-03-11T13:45:18.194000000Z", "a": 42.3}
        {"timestamp": "2020-03-11T14:45:18.194000000Z", "a": 41.7}
        {"timestamp": "2020-03-11T15:45:18.194000000Z", "a": 15.89922333}
        """
    )
    with mock.patch(  # noqa: SIM117
        "hetdesrun.adapters.generic_rest.load_framelike.get_generic_rest_adapter_base_url",
        return_value="https://hetida.de",
    ):
        with mock.patch(
            "hetdesrun.adapters.generic_rest.load_framelike.requests.Session.get",
            return_value=resp_mock,
        ):
            loaded_data = await load_data(
                {
                    "inp_1": FilteredSource(ref_id="id_1", type=ExternalType.DATAFRAME),
                },
                adapter_key="end_to_end_only_dataframe_data",
            )

            assert len(loaded_data) == 1
            assert isinstance(loaded_data["inp_1"], pd.DataFrame)
            assert loaded_data["inp_1"].shape == (3, 2)
            assert len(loaded_data["inp_1"].attrs) == 1
            assert loaded_data["inp_1"].attrs == attributes

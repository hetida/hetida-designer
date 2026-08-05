import io
from unittest import mock

import pandas as pd
import pytest

from hetdesrun.adapters.exceptions import AdapterClientWiringInvalidError
from hetdesrun.adapters.generic_rest import load_data
from hetdesrun.adapters.generic_rest.external_types import ExternalType
from hetdesrun.adapters.generic_rest.load_singletsframe import (
    load_single_singletsframe_from_adapter,
    load_singletsframes_from_adapter,
)
from hetdesrun.adapters.generic_rest.send_framelike import encode_attributes
from hetdesrun.models.data_selection import FilteredSource


@pytest.mark.asyncio
async def test_load_single_singletsframe_from_adapter_end_to_end() -> None:
    """Records have no metric field; every field besides timestamp is a value dimension"""
    resp_mock = mock.Mock(
        status_code=200,
        headers={
            "Data-Attributes": encode_attributes(
                {
                    "dataset_metadata": {"single_metric": "abc.temp"},
                    "from": "2019-08-01T15:45:30.000Z",
                }
            )
        },
        raw=io.BytesIO(
            b"""
        {"timestamp": "2019-08-01T15:45:36.000Z", "value": 1.0, "state": "ok"}
        {"timestamp": "2019-08-01T15:45:37.000Z", "value": 1.2, "state": "ok"}
        {"timestamp": "2019-08-01T15:45:46.000Z", "value": 1.9, "state": "suspicious"}
        """
        ),
    )
    with mock.patch(  # noqa: SIM117
        "hetdesrun.adapters.generic_rest.load_framelike.get_generic_rest_adapter_base_url",
        return_value="https://hetida.de",
    ):
        with mock.patch(
            "hetdesrun.adapters.generic_rest.load_framelike.niquests.Session.get",
            return_value=resp_mock,
        ):
            stsf = await load_single_singletsframe_from_adapter(
                FilteredSource(
                    ref_id="id_1",
                    type="singletsframe",
                    filters={
                        "from": "2019-08-01T15:45:30.000Z",
                        "to": "2019-08-01T15:46:00.000Z",
                    },
                ),
                adapter_key="end_to_end_load_singletsframe",
            )
            assert stsf.shape == (3, 3)
            assert set(stsf.columns) == {"timestamp", "value", "state"}
            assert isinstance(stsf["timestamp"].dtype, pd.DatetimeTZDtype)
            assert stsf.attrs["dataset_metadata"]["single_metric"] == "abc.temp"

            with pytest.raises(AdapterClientWiringInvalidError):
                await load_data(
                    {"inp_1": FilteredSource(ref_id="id_1", type=ExternalType.SINGLETSFRAME)},
                    adapter_key="end_to_end_load_singletsframe",
                )


@pytest.mark.asyncio
async def test_load_single_singletsframe_from_adapter_alone() -> None:
    with mock.patch(
        "hetdesrun.adapters.generic_rest.load_singletsframe.load_framelike_data",
    ) as load_framelike_mock:
        await load_single_singletsframe_from_adapter(
            FilteredSource(
                ref_id="id_1",
                type="singletsframe",
                filters={
                    "from": "2019-08-01T15:45:30.000Z",
                    "to": "2019-08-01T15:46:00.000Z",
                    "lower_threshold": "93.4",
                },
            ),
            adapter_key="load_singletsframe",
        )

        load_framelike_mock.assert_awaited_once_with(
            [
                FilteredSource(
                    ref_id="id_1",
                    type="singletsframe",
                    filters={
                        "from": "2019-08-01T15:45:30.000Z",
                        "to": "2019-08-01T15:46:00.000Z",
                        "lower_threshold": "93.4",
                    },
                )
            ],
            additional_params=[
                ("from", "2019-08-01T15:45:30.000Z"),
                ("to", "2019-08-01T15:46:00.000Z"),
                ("lower_threshold", "93.4"),
            ],
            adapter_key="load_singletsframe",
            endpoint="singletsframe",
        )


@pytest.mark.asyncio
async def test_load_singletsframes_from_adapter_resolves_time_interval() -> None:
    with mock.patch(
        "hetdesrun.adapters.generic_rest.load_singletsframe.load_single_singletsframe_from_adapter",
    ) as load_single_stsf_mock:
        await load_singletsframes_from_adapter(
            data_to_load={
                "inp_1": FilteredSource(
                    ref_id="id_1",
                    type="singletsframe",
                    filters={
                        "timestampFrom": "2019-08-01T15:45:30.000Z",
                        "timestampTo": "2019-08-01T15:46:00.000Z",
                        "lower_threshold": "93.4",
                    },
                )
            },
            adapter_key="load_singletsframe",
        )

        load_single_stsf_mock.assert_awaited_once()
        _, args, _ = load_single_stsf_mock.mock_calls[0]
        assert len(args) == 2
        assert isinstance(args[0], FilteredSource)
        assert args[0].ref_id == "id_1"
        assert args[0].type == "singletsframe"
        assert args[0].filters["lower_threshold"] == "93.4"
        assert args[0].filters["from"] == "2019-08-01T15:45:30+00:00"
        assert args[0].filters["to"] == "2019-08-01T15:46:00+00:00"
        assert args[1] == "load_singletsframe"


async def mock_load_generic_rest_singletsframe_data(*args, **kwargs) -> pd.DataFrame:
    data_stsf = pd.DataFrame(
        {
            "timestamp": [
                "2019-08-01T15:45:36.000Z",
                "2019-08-02T15:45:46.000Z",
                "2019-08-03T15:45:56.000Z",
            ],
            "value": [1.0, 1.9, 1.5],
            "state": ["ok", "ok", "suspicious"],
        }
    )
    data_stsf.attrs = {
        "dataset_metadata": {"single_metric": "abc.temp"},
        "from": "2019-08-01T15:45:30.000Z",
    }
    return data_stsf


@pytest.mark.asyncio
async def test_end_to_end_load_singletsframe_data_with_attrs() -> None:
    with mock.patch(
        "hetdesrun.adapters.generic_rest.load_singletsframe.load_single_singletsframe_from_adapter",
        new=mock_load_generic_rest_singletsframe_data,
    ):
        loaded_data = await load_data(
            {
                "inp_1": FilteredSource(
                    ref_id="id_1",
                    type=ExternalType.SINGLETSFRAME,
                    filters={
                        "timestampFrom": "2019-08-01T15:45:30.000Z",
                        "timestampTo": "2019-08-01T15:46:00.000Z",
                    },
                ),
            },
            adapter_key="end_to_end_load_singletsframe",
        )
        assert len(loaded_data) == 1
        assert isinstance(loaded_data["inp_1"], pd.DataFrame)
        assert loaded_data["inp_1"].shape == (3, 3)
        assert loaded_data["inp_1"].attrs["dataset_metadata"]["single_metric"] == "abc.temp"

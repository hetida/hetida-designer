import io
from unittest import mock

import pandas as pd
import pytest

from hetdesrun.adapters.exceptions import AdapterClientWiringInvalidError
from hetdesrun.adapters.generic_rest import load_data
from hetdesrun.adapters.generic_rest.external_types import ExternalType
from hetdesrun.adapters.generic_rest.load_multitsframe import (
    load_multitsframes_from_adapter,
    load_single_multitsframe_from_adapter,
)
from hetdesrun.adapters.generic_rest.send_framelike import encode_attributes
from hetdesrun.models.data_selection import FilteredSource


@pytest.mark.asyncio
async def test_load_single_multitsframe_from_adapter_end_to_end() -> None:
    resp_mock = mock.Mock(
        status_code=200,
        headers={
            "Data-Attributes": encode_attributes(
                {
                    "from": "2019-08-01T15:45:30.000Z",
                    "to": "2019-08-01T15:46:00.000Z",
                }
            )
        },
        raw=io.StringIO(
            """
        {"timestamp": "2019-08-01T15:45:36.000Z", "metric": "a", "value": 1.0}
        {"timestamp": "2019-08-01T15:45:37.000Z", "metric": "b", "value": 1.2}
        {"timestamp": "2019-08-01T15:45:37.000Z", "metric": "c", "value": 0.5}
        {"timestamp": "2019-08-01T15:45:46.000Z", "metric": "a", "value": 1.9}
        {"timestamp": "2019-08-01T15:45:46.000Z", "metric": "b", "value": 1.3}
        {"timestamp": "2019-08-01T15:45:47.000Z", "metric": "c", "value": 0.2}
        {"timestamp": "2019-08-01T15:45:56.000Z", "metric": "a", "value": 1.5}
        {"timestamp": "2019-08-01T15:45:57.000Z", "metric": "b", "value": 1.7}
        {"timestamp": "2019-08-01T15:45:56.000Z", "metric": "c", "value": 0.1}
        """
        ),
    )
    with mock.patch(  # noqa: SIM117
        "hetdesrun.adapters.generic_rest.load_framelike.get_generic_rest_adapter_base_url",
        return_value="https://hetida.de",
    ):
        with mock.patch(
            "hetdesrun.adapters.generic_rest.load_framelike.requests.Session.get",
            return_value=resp_mock,
        ):
            mtsf = await load_single_multitsframe_from_adapter(
                FilteredSource(
                    ref_id="id_1",
                    type="multitsframe",
                    filters={
                        "from": "2019-08-01T15:45:30.000Z",
                        "to": "2019-08-01T15:46:00.000Z",
                    },
                ),
                adapter_key="end_to_end_load_multitsframe",
            )
            assert mtsf.shape == (9, 3)
            assert len(mtsf.attrs) == 2
            assert mtsf.attrs["from"] == "2019-08-01T15:45:30.000Z"

            with pytest.raises(AdapterClientWiringInvalidError):
                mtsf = await load_data(
                    {"inp_1": FilteredSource(ref_id="id_1", type=ExternalType.MULTITSFRAME)},
                    adapter_key="end_to_end_load_multitsframe",
                )


@pytest.mark.asyncio
async def test_load_single_multitsframe_from_adapter_alone() -> None:
    with mock.patch(
        "hetdesrun.adapters.generic_rest.load_multitsframe.load_framelike_data",
    ) as load_framelike_mock:
        await load_single_multitsframe_from_adapter(
            FilteredSource(
                ref_id="id_1",
                type="multitsframe",
                filters={
                    "from": "2019-08-01T15:45:30.000Z",
                    "to": "2019-08-01T15:46:00.000Z",
                    "lower_threshold": "93.4",
                },
            ),
            adapter_key="load_multitsframe",
        )

        load_framelike_mock.assert_awaited_once_with(
            [
                FilteredSource(
                    ref_id="id_1",
                    type="multitsframe",
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
            adapter_key="load_multitsframe",
            endpoint="multitsframe",
        )


@pytest.mark.asyncio
async def test_load_multitsframe_from_adapter() -> None:
    with mock.patch(
        "hetdesrun.adapters.generic_rest.load_multitsframe.load_single_multitsframe_from_adapter",
    ) as load_single_mtsf_mock:
        await load_multitsframes_from_adapter(
            data_to_load={
                "inp_1": FilteredSource(
                    ref_id="id_1",
                    type="multitsframe",
                    filters={
                        "timestampFrom": "2019-08-01T15:45:30.000Z",
                        "timestampTo": "2019-08-01T15:46:00.000Z",
                        "lower_threshold": "93.4",
                    },
                )
            },
            adapter_key="load_multitsframe",
        )

        load_single_mtsf_mock.assert_awaited_once()
        _, args, _ = load_single_mtsf_mock.mock_calls[0]
        assert len(args) == 2
        assert isinstance(args[0], FilteredSource)
        assert args[0].ref_id == "id_1"
        assert args[0].type == "multitsframe"
        assert args[0].filters["lower_threshold"] == "93.4"
        assert args[0].filters["from"] == "2019-08-01T15:45:30.000Z"
        assert args[0].filters["to"] == "2019-08-01T15:46:00.000Z"
        assert args[1] == "load_multitsframe"


async def mock_load_generic_rest_multitsframe_data(*args, **kwargs) -> pd.DataFrame:
    data_mtsf = pd.DataFrame(
        {
            "metric": ["a", "b", "c", "a", "b", "c", "a", "b", "c"],
            "timestamp": [
                "2019-08-01T15:45:36.000Z",
                "2019-08-01T15:45:37.000Z",
                "2019-08-01T15:45:37.000Z",
                "2019-08-02T15:45:46.000Z",
                "2019-08-02T15:45:46.000Z",
                "2019-08-02T15:45:47.000Z",
                "2019-08-03T15:45:56.000Z",
                "2019-08-03T15:45:57.000Z",
                "2019-08-03T15:45:58.000Z",
            ],
            "value": [1.0, 1.2, 0.5, 1.9, 1.3, 0.2, 1.5, 1.7, 0.1],
        }
    )
    data_mtsf.attrs = {
        "from": "2019-08-01T15:45:30.000Z",
        "to": "2019-08-01T15:46:00.000Z",
    }
    return data_mtsf


@pytest.mark.asyncio
async def test_end_to_end_load_multitsframe_data_with_attrs() -> None:
    with mock.patch(
        "hetdesrun.adapters.generic_rest.load_multitsframe.load_single_multitsframe_from_adapter",
        new=mock_load_generic_rest_multitsframe_data,
    ):
        loaded_data = await load_data(
            {
                "inp_1": FilteredSource(
                    ref_id="id_1",
                    type=ExternalType.MULTITSFRAME,
                    filters={
                        "timestampFrom": "2019-08-01T15:45:30.000Z",
                        "timestampTo": "2019-08-01T15:46:00.000Z",
                    },
                ),
            },
            adapter_key="end_to_end_load_multitsframe",
        )
        assert len(loaded_data) == 1
        assert isinstance(loaded_data["inp_1"], pd.DataFrame)
        assert loaded_data["inp_1"].shape == (9, 3)
        assert len(loaded_data["inp_1"].attrs) == 2
        assert loaded_data["inp_1"].attrs["from"] == "2019-08-01T15:45:30.000Z"

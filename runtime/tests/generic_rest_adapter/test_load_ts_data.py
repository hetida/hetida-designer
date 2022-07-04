from unittest import mock

import pandas as pd
import pytest

from hetdesrun.adapters.exceptions import (
    AdapterClientWiringInvalidError,
    AdapterConnectionError,
)
from hetdesrun.adapters.generic_rest import (
    load_data,
    load_grouped_timeseries_data_together,
)
from hetdesrun.adapters.generic_rest.external_types import ExternalType
from hetdesrun.adapters.generic_rest.load_ts_data import load_ts_data_from_adapter
from hetdesrun.models.data_selection import FilteredSource


@pytest.mark.asyncio
async def test_load_ts_adapter_request():
    with mock.patch(
        "hetdesrun.adapters.generic_rest.load_framelike.get_generic_rest_adapter_base_url",
        return_value="https://hetida.de",
    ):
        resp_mock = mock.Mock()
        resp_mock.status_code = 200
        resp_mock.raw = """\n
            {"timeseriesId": "id_1", "timestamp": "2020-03-11T13:45:18.194000000Z", "value": 42.3}
            {"timeseriesId": "id_1", "timestamp": "2020-03-11T14:45:18.194000000Z", "value": 41.7}
            {"timeseriesId": "id_1", "timestamp": "2020-03-11T15:45:18.194000000Z", "value": 15.89922333}
            """

        filtered_sources = [
            FilteredSource(
                ref_id="id_1",
                type="timeseries(float)",
                filters={
                    "timestampFrom": "2018-09-01T00:00:00Z",
                    "timestampTo": "2020-01-01T00:00:00Z",
                },
            ),
        ]
        with mock.patch(
            "hetdesrun.adapters.generic_rest.load_framelike.requests.Session.get",
            return_value=resp_mock,
        ):
            df = await load_ts_data_from_adapter(
                filtered_sources,
                from_timestamp="2018-09-01T00:00:00Z",
                to_timestamp="2020-01-01T00:00:00Z",
                adapter_key="test_load_ts_generic_adapter_key",
            )

            assert df.shape == (3, 3)

            resp_mock.status_code = 400

            with pytest.raises(AdapterConnectionError):
                await load_ts_data_from_adapter(
                    filtered_sources,
                    from_timestamp="2018-09-01T00:00:00Z",
                    to_timestamp="2020-01-01T00:00:00Z",
                    adapter_key="test_load_ts_generic_adapter_key",
                )

            resp_mock.status_code = 404
            resp_mock.text = "errorCode"
            resp_mock.json = mock.Mock(return_value={"errorCode": "RESULT_EMPTY"})

            df = await load_ts_data_from_adapter(
                filtered_sources,
                from_timestamp="2018-09-01T00:00:00Z",
                to_timestamp="2020-01-01T00:00:00Z",
                adapter_key="test_load_ts_generic_adapter_key",
            )

            assert df.shape == (0, 3)

            resp_mock.status_code = 200
            resp_mock.raw = ""
            df = await load_ts_data_from_adapter(
                filtered_sources,
                from_timestamp="2018-09-01T00:00:00Z",
                to_timestamp="2020-01-01T00:00:00Z",
                adapter_key="test_load_ts_generic_adapter_key",
            )

            assert df.shape == (0, 3)


async def mock_load_generic_rest_ts_data(*args, **kwargs):
    return pd.DataFrame(
        {
            "timestamp": pd.to_datetime(
                [
                    "2018-09-01T00:00:00Z",
                    "2018-09-02T00:00:00Z",
                    "2019-05-01T00:00:00Z",
                    "2019-04-01T00:00:00Z",
                ]
            ),
            "value": [2.58, 3.4, 10.2, 11.5],
            "timeseriesId": ["id_2", "id_1", "id_1", "id_2"],
        }
    )


@pytest.mark.asyncio
async def test_load_ts_data():
    ts_data_to_load = {
        "inp_1": FilteredSource(
            ref_id="id_1",
            type=ExternalType.TIMESERIES_FLOAT,
            filters={
                "timestampFrom": "2018-09-01T00:00:00Z",
                "timestampTo": "2020-01-01T00:00:00Z",
            },
        ),
        "inp_2": FilteredSource(  # same filter timestamps as above
            ref_id="id_2",
            type=ExternalType.TIMESERIES_FLOAT,
            filters={
                "timestampFrom": "2018-09-01T00:00:00Z",
                "timestampTo": "2020-01-01T00:00:00Z",
            },
        ),
        "inp_3": FilteredSource(  # same filter timestamps as above
            ref_id="id_3",
            type=ExternalType.TIMESERIES_FLOAT,
            filters={
                "timestampFrom": "2018-09-01T00:00:00Z",
                "timestampTo": "2020-01-01T00:00:00Z",
            },
        ),
        "inp_4": FilteredSource(
            ref_id="id_1",
            type=ExternalType.TIMESERIES_FLOAT,
            filters={
                "timestampFrom": "2017-09-01T00:00:00Z",  # different timestamp
                "timestampTo": "2020-01-01T00:00:00Z",
            },
        ),
    }

    with mock.patch(
        "hetdesrun.adapters.generic_rest.load_ts_data.load_ts_data_from_adapter",
        new=mock_load_generic_rest_ts_data,
    ):
        loaded_data = await load_grouped_timeseries_data_together(
            ts_data_to_load,
            adapter_key="test",
        )

        # returns Series for input:
        assert isinstance(loaded_data["inp_1"], pd.Series)
        assert isinstance(loaded_data["inp_3"], pd.Series)  # even if no data available!
        # proper separation into series:
        assert len(loaded_data["inp_1"]) == 2
        assert len(loaded_data["inp_2"]) == 2
        assert len(loaded_data["inp_3"]) == 0
        assert len(loaded_data["inp_4"]) == 2

        ts_data_to_load["inp_1"].filters["timestampFrom"] = None

        with pytest.raises(AdapterClientWiringInvalidError):
            loaded_data = await load_grouped_timeseries_data_together(
                ts_data_to_load,
                adapter_key="test",
            )


@pytest.mark.asyncio
async def test_end_to_end_load_only_ts_data():
    with mock.patch(
        "hetdesrun.adapters.generic_rest.load_ts_data.load_ts_data_from_adapter",
        new=mock_load_generic_rest_ts_data,
    ):
        loaded_data = await load_data(
            {
                "inp_1": FilteredSource(
                    ref_id="id_1",
                    type="timeseries(float)",
                    filters={
                        "timestampFrom": "2018-09-01T00:00:00Z",
                        "timestampTo": "2020-01-01T00:00:00Z",
                    },
                )
            },
            adapter_key="end_to_end_only_ts_data",
        )

        assert len(loaded_data) == 1
        assert len(loaded_data["inp_1"]) == 2
        assert isinstance(loaded_data["inp_1"], pd.Series)

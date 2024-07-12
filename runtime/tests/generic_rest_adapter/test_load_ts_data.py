import io
from unittest import mock

import pandas as pd
import pytest
import requests

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
        resp_mock.raw = io.StringIO(
            """\n
            {"timeseriesId": "1", "timestamp": "2020-03-11T13:45:18.194000000Z", "value": 42.3}
            {"timeseriesId": "1", "timestamp": "2020-03-11T14:45:18.194000000Z", "value": 41.7}
            {"timeseriesId": "1", "timestamp": "2020-03-11T15:45:18.194000000Z", "value": 15.89922333}
            """
        )
        resp_mock.headers = {}

        filtered_sources = [
            FilteredSource(
                ref_id="1",
                type="timeseries(float)",
                filters={
                    "timestampFrom": "2018-09-01T00:00:00Z",
                    "timestampTo": "2020-01-01T00:00:00Z",
                    "filter_key": "filter_value",
                },
            ),
        ]
        filter_params = frozenset(
            {
                ("filter_key", "filter_value"),
                ("from", "2018-09-01T00:00:00Z"),
                ("to", "2020-01-01T00:00:00Z"),
            }
        )
        with mock.patch(
            "hetdesrun.adapters.generic_rest.load_framelike.requests.Session.get",
            return_value=resp_mock,
        ) as get_request_mock:
            df = await load_ts_data_from_adapter(
                filtered_sources,
                filter_params=filter_params,
                adapter_key="test_load_ts_generic_adapter_key",
            )

            assert df.shape == (3, 3)
            assert df["timeseriesId"].dtype == "string"

            assert get_request_mock.call_count == 1
            kwargs = get_request_mock.call_args.kwargs
            assert len(kwargs["params"]) == 4
            assert ("id", "1") in kwargs["params"]
            assert ("filter_key", "filter_value") in kwargs["params"]
            assert ("from", "2018-09-01T00:00:00Z") in kwargs["params"]
            assert ("to", "2020-01-01T00:00:00Z") in kwargs["params"]

            resp_mock.status_code = 400
            resp_mock.text = "my adapter error"
            with pytest.raises(AdapterConnectionError, match="my adapter error"):
                await load_ts_data_from_adapter(
                    filtered_sources,
                    filter_params=filter_params,
                    adapter_key="test_load_ts_generic_adapter_key",
                )

            resp_mock.status_code = 404
            resp_mock.text = "errorCode"
            resp_mock.json = mock.Mock(return_value={"errorCode": "RESULT_EMPTY"})

            df = await load_ts_data_from_adapter(
                filtered_sources,
                filter_params=filter_params,
                adapter_key="test_load_ts_generic_adapter_key",
            )

            assert df.shape == (0, 3)

            resp_mock.status_code = 200
            resp_mock.raw = io.StringIO("")
            df = await load_ts_data_from_adapter(
                filtered_sources,
                filter_params=filter_params,
                adapter_key="test_load_ts_generic_adapter_key",
            )

            assert df.shape == (0, 3)


async def mock_load_generic_rest_ts_data(*args, **kwargs):
    data_df = pd.DataFrame(
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
    data_df.attrs = {"id_1": {"a": "b"}, "id_3": {"c": 5}}
    return data_df


@pytest.mark.asyncio
async def test_load_grouped_timeseries_data_together():
    ts_data_to_load = {
        "inp_1": FilteredSource(
            ref_id="id_1",
            type=ExternalType.TIMESERIES_FLOAT,
            filters={
                "timestampFrom": "2018-09-01T00:00:00Z",
                "timestampTo": "2020-01-01T00:00:00Z",
                "filter_key": "filter_value",
            },
        ),
        "inp_2": FilteredSource(  # same filter as above
            ref_id="id_2",
            type=ExternalType.TIMESERIES_FLOAT,
            filters={
                "timestampFrom": "2018-09-01T00:00:00Z",
                "timestampTo": "2020-01-01T00:00:00Z",
                "filter_key": "filter_value",
            },
        ),
        "inp_3": FilteredSource(  # same filter timestamps as above, but no additional filter
            ref_id="id_3",
            type=ExternalType.TIMESERIES_FLOAT,
            filters={
                "timestampFrom": "2018-09-01T00:00:00Z",
                "timestampTo": "2020-01-01T00:00:00Z",
            },
        ),
        "inp_4": FilteredSource(  # different filter timestamps, but same additional filter
            ref_id="id_1",
            type=ExternalType.TIMESERIES_FLOAT,
            filters={
                "timestampFrom": "2017-09-01T00:00:00Z",
                "timestampTo": "2020-01-01T00:00:00Z",
                "filter_key": "filter_value",
            },
        ),
    }

    with mock.patch(
        "hetdesrun.adapters.generic_rest.load_ts_data.load_ts_data_from_adapter",
        new=mock.AsyncMock(wraps=mock_load_generic_rest_ts_data),
    ) as load_ts_from_adapter_mock:
        await load_grouped_timeseries_data_together(
            ts_data_to_load,
            adapter_key="test",
        )

        assert load_ts_from_adapter_mock.await_count == 3
        args_0, kwargs_0 = load_ts_from_adapter_mock.await_args_list[0]
        assert len(args_0) == 2
        assert len(args_0[0]) == 2
        assert isinstance(args_0[0][0], FilteredSource)
        assert args_0[0][0].ref_id == "id_1"
        assert "from" in args_0[0][0].filters
        assert "filter_key" in args_0[0][0].filters
        assert args_0[0][0].filters["from"] == "2018-09-01T00:00:00Z"
        assert args_0[0][1].ref_id == "id_2"
        assert "from" in args_0[0][1].filters
        assert "filter_key" in args_0[0][1].filters
        assert args_0[0][1].filters["from"] == "2018-09-01T00:00:00Z"
        assert len(args_0[1]) == 3
        assert ("from", "2018-09-01T00:00:00Z") in args_0[1]
        assert ("to", "2020-01-01T00:00:00Z") in args_0[1]
        assert ("filter_key", "filter_value") in args_0[1]
        assert len(kwargs_0) == 1
        assert kwargs_0["adapter_key"] == "test"

        args_1, kwargs_1 = load_ts_from_adapter_mock.await_args_list[1]
        assert len(args_1) == 2
        assert len(args_1[0]) == 1
        assert isinstance(args_1[0][0], FilteredSource)
        assert args_1[0][0].ref_id == "id_3"
        assert "from" in args_1[0][0].filters
        assert "filter_key" not in args_1[0][0].filters
        assert args_1[0][0].filters["from"] == "2018-09-01T00:00:00Z"
        assert len(args_1[1]) == 2
        assert ("from", "2018-09-01T00:00:00Z") in args_1[1]
        assert ("to", "2020-01-01T00:00:00Z") in args_1[1]
        assert len(kwargs_1) == 1
        assert kwargs_1["adapter_key"] == "test"

        args_2, kwargs_2 = load_ts_from_adapter_mock.await_args_list[2]
        assert len(args_2) == 2
        assert len(args_2[0]) == 1
        assert isinstance(args_1[0][0], FilteredSource)
        assert args_2[0][0].ref_id == "id_1"
        assert "from" in args_2[0][0].filters
        assert "filter_key" in args_2[0][0].filters
        assert args_2[0][0].filters["from"] == "2017-09-01T00:00:00Z"
        assert len(args_2[1]) == 3
        assert ("from", "2017-09-01T00:00:00Z") in args_2[1]
        assert ("to", "2020-01-01T00:00:00Z") in args_2[1]
        assert ("filter_key", "filter_value") in args_2[1]
        assert len(kwargs_2) == 1
        assert kwargs_2["adapter_key"] == "test"


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


@pytest.mark.asyncio
async def test_end_to_end_load_ts_data_with_attrs():
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
        assert len(loaded_data["inp_1"].attrs) == 1
        assert loaded_data["inp_1"].attrs["a"] == "b"


@pytest.mark.asyncio
async def test_end_to_end_load_empty_ts_data_with_attrs():
    with mock.patch(
        "hetdesrun.adapters.generic_rest.load_ts_data.load_ts_data_from_adapter",
        new=mock_load_generic_rest_ts_data,
    ):
        loaded_data = await load_data(
            {
                "inp_1": FilteredSource(
                    ref_id="id_3",
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
        assert len(loaded_data["inp_1"]) == 0
        assert isinstance(loaded_data["inp_1"], pd.Series)
        assert len(loaded_data["inp_1"].attrs) == 1
        assert loaded_data["inp_1"].attrs["c"] == 5


@pytest.mark.asyncio
async def test_end_to_end_load_ts_with_exception():
    with mock.patch(
        "hetdesrun.adapters.generic_rest.load_framelike.get_generic_rest_adapter_base_url",
        return_value="https://hetida.de",
    ):
        with (
            mock.patch(
                "hetdesrun.adapters.generic_rest.load_framelike.requests.Session.get",
                return_value=mock.Mock(status_code=422, text="my adapter error"),
            ),
            pytest.raises(AdapterConnectionError, match="my adapter error"),
        ):
            await load_data(
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

        with (
            mock.patch(
                "hetdesrun.adapters.generic_rest.load_framelike.requests.Session.get",
                side_effect=requests.HTTPError("my http error"),
            ),
            pytest.raises(AdapterConnectionError, match="my http error"),
        ):
            await load_data(
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

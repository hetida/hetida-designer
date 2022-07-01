from unittest import mock

import numpy as np
import pandas as pd
import pytest

from hetdesrun.adapters.generic_rest import send_data
from hetdesrun.adapters.generic_rest.external_types import ExternalType
from hetdesrun.models.data_selection import FilteredSink


@pytest.mark.asyncio
async def test_end_to_end_send_only_timeseries_data():

    response = mock.Mock()
    response.status_code = 200
    post_mock = mock.AsyncMock(return_value=response)

    with mock.patch(
        "hetdesrun.adapters.generic_rest.send_framelike.get_generic_rest_adapter_base_url",
        return_value="https://hetida.de",
    ):

        with mock.patch(
            "hetdesrun.adapters.generic_rest.send_ts_data.AsyncClient.post",
            new=post_mock,
        ):

            # one timeseries
            await send_data(
                {
                    "inp_1": FilteredSink(
                        ref_id="sink_id_1", type="timeseries(float)", filters={}
                    )
                },
                {
                    "inp_1": pd.Series(
                        [1.2, 3.4, 5.9],
                        index=pd.to_datetime(
                            [
                                "2020-01-15T00:00:00.000Z",
                                "2020-01-15T01:00:00.000Z",
                                "2020-01-15T02:00:00.000Z",
                            ]
                        ),
                    )
                },
                adapter_key="test_end_to_end_send_only_timeseries_data_adapter_key",
            )
            assert post_mock.called  # we got through to actually posting!

            func_name, args, kwargs = post_mock.mock_calls[0]
            assert kwargs["params"] == [("timeseriesId", "sink_id_1")]
            assert kwargs["json"] == [
                {"timestamp": "2020-01-15T00:00:00.000000000Z", "value": 1.2},
                {"timestamp": "2020-01-15T01:00:00.000000000Z", "value": 3.4},
                {"timestamp": "2020-01-15T02:00:00.000000000Z", "value": 5.9},
            ]

            # more than one timeseries
            await send_data(
                {
                    "inp_1": FilteredSink(
                        ref_id="sink_id_1", type="timeseries(float)", filters={}
                    ),
                    "inp_2": FilteredSink(
                        ref_id="sink_id_2",
                        type=ExternalType.TIMESERIES_STR,
                        filters={},
                    ),
                },
                {
                    "inp_1": pd.Series(
                        [1.2, 3.4, np.nan],
                        index=pd.to_datetime(
                            [
                                "2020-01-15T00:00:00.000Z",
                                "2020-01-15T01:00:00.000Z",
                                "2020-01-15T02:00:00.000Z",
                            ]
                        ),
                    ),
                    "inp_2": pd.Series(
                        ["first", "second"],
                        index=pd.to_datetime(
                            [
                                "2020-01-15T00:00:00.000Z",
                                "2020-01-15T01:00:00.000Z",
                            ]
                        ),
                    ),
                },
                adapter_key="test_end_to_end_send_only_timeseries_data_adapter_key",
            )

            # note: can be async!
            func_name_1, args_1, kwargs_1 = post_mock.mock_calls[1]
            func_name_2, args_2, kwargs_2 = post_mock.mock_calls[2]
            assert (len(kwargs_1["json"]) == 3) or (len(kwargs_2["json"]) == 3)
            assert (len(kwargs_1["json"]) == 2) or (len(kwargs_2["json"]) == 2)

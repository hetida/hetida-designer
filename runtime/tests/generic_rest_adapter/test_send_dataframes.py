from unittest import mock

import numpy as np
import pandas as pd
import pytest

from hetdesrun.adapters.generic_rest import send_data
from hetdesrun.adapters.generic_rest.external_types import ExternalType
from hetdesrun.models.data_selection import FilteredSink


@pytest.mark.asyncio
async def test_end_to_end_send_only_dataframe_data():

    response = mock.Mock()
    response.status_code = 200
    post_mock = mock.AsyncMock(return_value=response)

    with mock.patch(
        "hetdesrun.adapters.generic_rest.send_framelike.get_generic_rest_adapter_base_url",
        return_value="https://hetida.de",
    ):

        with mock.patch(
            "hetdesrun.adapters.generic_rest.send_dataframe.AsyncClient.post",
            new=post_mock,
        ):

            # one frame
            await send_data(
                {
                    "inp_1": FilteredSink(
                        ref_id="sink_id_1", type="dataframe", filters={}
                    )
                },
                {"inp_1": pd.DataFrame({"a": [1.2, 3.4, 5.9], "b": [2.9, 8.7, 2.2]})},
                adapter_key="test_end_to_end_send_only_dataframe_data_adapter_key",
            )
            assert post_mock.called  # we got through to actually posting!

            func_name, args, kwargs = post_mock.mock_calls[0]
            assert kwargs["params"] == [("id", "sink_id_1")]
            assert kwargs["json"] == [
                {"a": 1.2, "b": 2.9},
                {"a": 3.4, "b": 8.7},
                {"a": 5.9, "b": 2.2},
            ]

            # more than one frame
            await send_data(
                {
                    "inp_1": FilteredSink(
                        ref_id="sink_id_1", type="dataframe", filters={}
                    ),
                    "inp_2": FilteredSink(
                        ref_id="sink_id_2",
                        type=ExternalType.DATAFRAME,
                        filters={},
                    ),
                },
                {
                    "inp_1": pd.DataFrame({"a": [1.2, 3.4, 5.9], "b": [2.9, 8.7, 2.2]}),
                    "inp_2": pd.DataFrame({"c": [1.9, np.nan]}),
                },
                adapter_key="test_end_to_end_send_only_dataframe_data_adapter_key",
            )

            # note: can be async!
            func_name_1, args_1, kwargs_1 = post_mock.mock_calls[1]
            func_name_2, args_2, kwargs_2 = post_mock.mock_calls[2]
            assert (len(kwargs_1["json"]) == 3) or (len(kwargs_2["json"]) == 3)
            assert (len(kwargs_1["json"]) == 2) or (len(kwargs_2["json"]) == 2)

            # one dataframe frame with timestamps and attributes
            df = pd.DataFrame(
                {
                    "a": [1.2, 3.4, 5.9],
                    "b": [2.9, 8.7, 2.2],
                    "timestamp": [
                        pd.Timestamp("2020-08-03 15:30:00+0000", tz="UTC"),
                        pd.Timestamp("2020-12-01 07:15:00+0000", tz="UTC"),
                        pd.Timestamp("2021-01-05 09:20:00+0000", tz="UTC"),
                    ],
                }
            )
            df_attrs = {"c": "test"}
            df.attrs = df_attrs
            await send_data(
                {
                    "inp_1": FilteredSink(
                        ref_id="sink_id_1", type="dataframe", filters={}
                    )
                },
                {"inp_1": df},
                adapter_key="test_end_to_end_send_only_dataframe_data_adapter_key",
            )
            assert post_mock.called  # we got through to actually posting!

            func_name, args, kwargs = post_mock.mock_calls[3]
            assert kwargs["params"] == [("id", "sink_id_1")]
            assert kwargs["json"] == [
                {"a": 1.2, "b": 2.9, "timestamp": "2020-08-03T15:30:00+00:00"},
                {"a": 3.4, "b": 8.7, "timestamp": "2020-12-01T07:15:00+00:00"},
                {"a": 5.9, "b": 2.2, "timestamp": "2021-01-05T09:20:00+00:00"},
            ]
            assert "Data-Attributes" in kwargs["headers"]

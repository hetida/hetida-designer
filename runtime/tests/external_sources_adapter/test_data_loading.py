import json
from unittest import mock

import httpx
import pandas as pd
import pytest

from hetdesrun.adapters.external_sources import load_data
from hetdesrun.adapters.external_sources.sources import load_open_meteo
from hetdesrun.models.data_selection import FilteredSource


@pytest.fixture
def mocked_open_meteo_api_call_response(resp_json):
    with mock.patch(
        "hetdesrun.adapters.external_sources.sources.open_meteo_api_call",
        return_value=httpx.Response(200, json=resp_json),
    ) as mocked_call_response:
        yield mocked_call_response


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "resp_json",
    [
        {
            "latitude": 51.4817,
            "longitude": 7.2165,
            "hourly": {
                "time": ["2024-07-12T01:00:00+00:00"],
                "temperature_2m": [32.0],
                "precipitation_probability": [42],
                "precipitation": [55],
            },
        }
    ],
)
async def test_load_open_meteo(mocked_open_meteo_api_call_response):
    loaded_data = await load_open_meteo(
        "open-meteo-forecast",
        filters={
            "timestampFrom": "2024-07-18T01:12:36+00:00",
            "timestampTo": "2024-07-19T06:45:22+00:00",
            "query_params": json.dumps(
                {
                    "latitude": 51.4817,
                    "longitude": 7.2165,
                    "hourly": "temperature_2m,precipitation_probability,precipitation,weather_code",
                    "start_date": "2024-07-11",
                    "end_date": "2024-07-18",
                }
            ),
        },
    )

    assert isinstance(loaded_data, pd.DataFrame)
    assert len(loaded_data) == 3


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "resp_json",
    [
        {
            "latitude": 51.4817,
            "longitude": 7.2165,
            "hourly": {
                "time": ["2024-07-12T01:00:00+00:00", "2024-07-12T02:00:00+00:00"],
                "temperature_2m": [32.0, 33.0],
                "precipitation_probability": [42, 55],
                "precipitation": [55, 22],
            },
        }
    ],
)
async def test_load_data_from_open_meteo_dapter(mocked_open_meteo_api_call_response):
    loaded_data_by_inp = await load_data(
        {
            "test_inp": FilteredSource(
                ref_id="open-meteo-forecast",
                ref_id_type="SOURCE",
                filters={
                    "timestampFrom": "2024-07-18T01:12:36+00:00",
                    "timestampTo": "2024-07-19T06:45:22+00:00",
                    "query_params": json.dumps(
                        {
                            "latitude": 51.4817,
                            "longitude": 7.2165,
                            "hourly": (
                                "temperature_2m,precipitation_probability,precipitation,weather_code"
                            ),
                            "start_date": "2024-07-11",
                            "end_date": "2024-07-18",
                        }
                    ),
                },
            )
        },
        adapter_key="external-sources",
    )

    assert "test_inp" in loaded_data_by_inp
    assert len(loaded_data_by_inp) == 1

    assert isinstance(loaded_data_by_inp["test_inp"], pd.DataFrame)
    assert len(loaded_data_by_inp["test_inp"]) == 6

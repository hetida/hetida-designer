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
async def test_load_data_from_open_meteo_adapter(mocked_open_meteo_api_call_response):
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


@pytest.fixture
def mocked_energy_charts_info_prices_api_call_response(resp_json):
    with mock.patch(
        "hetdesrun.adapters.external_sources.sources.energy_chart_api_call",
        return_value=httpx.Response(200, json=resp_json),
    ) as mocked_call_response:
        yield mocked_call_response


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "resp_json",
    [
        {
            "license_info": (
                "CC BY 4.0 (creativecommons.org/licenses/by/4.0)"
                " from Bundesnetzagentur | SMARD.de"
            ),
            "unix_seconds": [
                1721268000,
                1721271600,
                1721275200,
                1721278800,
                1721282400,
                1721286000,
                1721289600,
                1721293200,
                1721296800,
                1721300400,
                1721304000,
                1721307600,
                1721311200,
                1721314800,
                1721318400,
                1721322000,
                1721325600,
                1721329200,
                1721332800,
                1721336400,
                1721340000,
                1721343600,
                1721347200,
                1721350800,
                1721354400,
                1721358000,
                1721361600,
                1721365200,
                1721368800,
            ],
            "price": [
                79.27,
                92.1,
                120.88,
                107.27,
                96.74,
                79.22,
                63.84,
                47.13,
                35.01,
                33.96,
                37.01,
                48.78,
                67.56,
                85.48,
                92,
                130.18,
                227.6,
                184.46,
                119.54,
                101.92,
                90.11,
                80.45,
                79.91,
                79.29,
                83.38,
                91.38,
                115.6,
                110.72,
                98.4,
            ],
            "unit": "EUR/MWh",
            "deprecated": False,
        }
    ],
)
async def test_load_data_from_energy_chart_info_prices(
    mocked_energy_charts_info_prices_api_call_response,
):
    loaded_data_by_inp = await load_data(
        {
            "test_inp": FilteredSource(
                ref_id="energy-charts-info-prices",
                ref_id_type="SOURCE",
                filters={
                    "timestampFrom": "2024-07-18T01:12:36+00:00",
                    "timestampTo": "2024-07-19T06:45:22+00:00",
                    "bzn": "DE-LU",
                },
            )
        },
        adapter_key="external-sources",
    )

    assert "test_inp" in loaded_data_by_inp
    assert len(loaded_data_by_inp) == 1

    assert isinstance(loaded_data_by_inp["test_inp"], pd.DataFrame)
    assert len(loaded_data_by_inp["test_inp"]) == 29

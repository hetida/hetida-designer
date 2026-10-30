import datetime
import functools
import json
import logging
from collections.abc import Callable
from typing import Any, Literal

import pandas as pd
from httpx import AsyncClient, Response
from pydantic import BaseModel, ValidationError

from hetdesrun.adapters.exceptions import AdapterHandlingException
from hetdesrun.adapters.external_sources.config import get_external_sources_adapter_config
from hetdesrun.adapters.external_sources.models import ExternalSourcesStructureSource
from hetdesrun.adapters.generic_rest.external_types import ExternalType
from hetdesrun.adapters.sql_adapter.load_table import extract_time_range

logger = logging.getLogger(__name__)

sources: dict[
    str, ExternalSourcesStructureSource
] = {}  # source id -> ExternalSourcesStructureSource

source_load_functions: dict[str, Callable] = {}  # source_id -> load func


class OpenMeteoParams(BaseModel):
    query_params: dict[str, Any]  # | tuple[tuple[str, str], ...]


# Open Meteo Source
sources["open-meteo-forecast"] = ExternalSourcesStructureSource(
    id="open-meteo-forecast",
    name="Open Meteo Forecast Data",
    type=ExternalType.MULTITSFRAME,
    path="open meteo forecast data",
    filters={
        "query_params": {
            "name": "query params",
            "type": "free_text",
            "required": True,
            "description": "json dict of query parameters for the open meteo api",
        }
    },
)

sources["open-meteo-archive"] = ExternalSourcesStructureSource(
    id="open-meteo-archive",
    name="Open Meteo Historical Weather Data",
    type=ExternalType.MULTITSFRAME,
    path="open meteo historical weather data",
    filters={
        "query_params": {
            "name": "query params",
            "type": "free_text",
            "required": True,
            "description": "json dict of query parameters for the open meteo api",
        }
    },
)

sources["open-meteo-historical-forecast"] = ExternalSourcesStructureSource(
    id="open-meteo-historical-forecast",
    name="Open Meteo Historical Forecast Data",
    type=ExternalType.MULTITSFRAME,
    path="open meteo historical forecast data",
    filters={
        "query_params": {
            "name": "query params",
            "type": "free_text",
            "required": True,
            "description": "json dict of query parameters for the open meteo api",
        }
    },
)


sources["energy-charts-info-prices"] = ExternalSourcesStructureSource(
    id="energy-charts-info-prices",
    name="Energy-Charts.info Dayahead Prices EUR/MWh",
    type=ExternalType.MULTITSFRAME,
    path="energy-charts.info api /prices",
    filters={
        "bzn": {
            "name": "bidding zone",
            "type": "free_text",
            "required": True,
            "description": "bidding zone code, e.g. DE-LU",
        }
    },
)


def multitsframe_metadata(
    metrics: list[dict[str, Any]],
    from_datetime: datetime.datetime,
    to_datetime: datetime.datetime,
    query_timestamp: datetime.datetime,
) -> dict[str, Any]:
    """Metadata of a loaded multitsframe following the metadata conventions

    metrics are the metadata entries of the queried metrics, identified by their id in the
    metric column. query_timestamp is the time of the request, since the external source
    delivers its state at that time, e.g. its latest forecast.
    """
    return {
        "dataset_metadata": {
            "metric_key": "id",
            "queried_metrics": [metric["id"] for metric in metrics],
            "ref_interval_start_timestamp": from_datetime.astimezone(datetime.UTC).isoformat(),
            "ref_interval_end_timestamp": to_datetime.astimezone(datetime.UTC).isoformat(),
            "ref_interval_type": "closed",
            "query_timestamp": query_timestamp.astimezone(datetime.UTC).isoformat(),
        },
        "metrics": metrics,
    }


OPENMETEO_FREQUENCY_KEYS = ("hourly", "daily", "minutely_15")


def openmeteo_metrics(datasets: list[dict]) -> list[dict[str, Any]]:
    """The metadata of the weather variables of open meteo datasets

    The variables occur in the metric column, also for several coordinates, which the latitude
    and longitude columns distinguish. Their units are those open meteo provides for them.
    """
    metrics_by_id: dict[str, dict[str, Any]] = {}
    for dataset in datasets:
        for key in OPENMETEO_FREQUENCY_KEYS:
            units = dataset.get(f"{key}_units") or {}
            for variable in dataset.get(key) or {}:
                if variable == "time" or variable in metrics_by_id:
                    continue
                unit = units.get(variable)
                metrics_by_id[variable] = {
                    "id": variable,
                    "name": variable,
                    "value_dimensions": [
                        {
                            "column": "value",
                            "unit": unit if isinstance(unit, str) else None,
                            "measurement": None,
                        },
                        {"column": "latitude", "unit": "°", "measurement": "latitude"},
                        {"column": "longitude", "unit": "°", "measurement": "longitude"},
                    ],
                }
    return list(metrics_by_id.values())


def openmeteo_table_to_multitsframe(parsed_pandas_df: pd.DataFrame) -> pd.DataFrame:
    time_column = pd.to_datetime(parsed_pandas_df["time"], utc=True)
    parsed_pandas_df["time"] = time_column

    metric_cols = parsed_pandas_df.columns.drop("time")

    multi_ts_frame_df = parsed_pandas_df.melt(id_vars=["time"], value_vars=metric_cols).rename(
        {"time": "timestamp", "variable": "metric", "value": "value"}, axis="columns"
    )

    return multi_ts_frame_df


def extract_openmeteo_data(
    dataset: dict, key: Literal["hourly", "daily", "minutely_15"]
) -> tuple[pd.DataFrame, str, float, float]:
    """Extract relevant timeseries data from an openmeteo dataset for a coordinate pair"""
    if not key in dataset:
        return (
            pd.DataFrame(columns=["timestamp", "metric", "value", "latitude", "longitude"]),
            key,
            dataset["latitude"],
            dataset["longitude"],
        )

    try:
        parsed_df = pd.DataFrame.from_dict(dataset[key])
    except ValueError as e:
        msg = "Pandas could not parse response json object hourly data."
        logger.error(msg)
        raise AdapterHandlingException(msg) from e

    try:
        resulting_multitsframe = openmeteo_table_to_multitsframe(parsed_df)
    except Exception as e:
        msg = "Failed transforming data into a multitsframe."
        logger.error(msg)
        raise AdapterHandlingException(msg) from e

    resulting_multitsframe["latitude"] = dataset["latitude"]
    resulting_multitsframe["longitude"] = dataset["longitude"]
    return (resulting_multitsframe, key, dataset["latitude"], dataset["longitude"])


def append_dataset(
    dataset: pd.DataFrame,
    key: Literal["hourly", "daily", "minutely_15"],
    mutable_df_list: list[pd.DataFrame],
    mutable_metadata_list: list[dict],
) -> None:
    """Extract timeseries data and metadata from a dataset and append both to separate lists"""
    metadata_set = {
        key: val for key, val in dataset.items() if key not in ["hourly", "daily", "minutely_15"]
    }
    multi_df, freq_key, lat, lon = extract_openmeteo_data(dataset, key)
    mutable_df_list.append(multi_df)
    mutable_metadata_list.append(
        {"latitude": lat, "longitude": lon, "frequency": freq_key, "metadata": metadata_set}
    )


async def open_meteo_api_call(
    base_url: str,
    open_meteo_params: OpenMeteoParams,
    async_client: AsyncClient | None = None,
) -> Response:
    if async_client is None:
        async_client = AsyncClient(timeout=15)
    async with async_client as client:
        response = await client.get(base_url, params=open_meteo_params.query_params)
    return response


async def load_open_meteo(  # noqa: PLR0915
    source_id: str,
    filters: dict[str, str],
    base_url: str = "https://api.open-meteo.com/v1/forecast",
) -> pd.DataFrame:
    query_params_str = filters.get("query_params", "")

    logger.debug(
        "Start loading open meteo data for source id %s from url %s with filters %s",
        source_id,
        base_url,
        filters,
    )

    try:
        open_meteo_params = OpenMeteoParams(query_params=json.loads(query_params_str))
    except (ValueError, TypeError, ValidationError) as e:
        msg = f"Could not parse open meteo query_params filter string: {query_params_str}"
        logger.error(msg)
        raise AdapterHandlingException(msg) from e

    # use dates from multitsframe built-in timestampFrom and timestampTo filters,
    # possibly overriding content from query parameters filter

    from_datetime, to_datetime = extract_time_range(filters)
    open_meteo_params.query_params["start_date"] = from_datetime.date().isoformat()
    open_meteo_params.query_params["end_date"] = to_datetime.date().isoformat()

    from_datetime = from_datetime.replace(minute=0, second=0, microsecond=0)
    to_datetime = to_datetime.replace(minute=0, second=0, microsecond=0)
    open_meteo_params.query_params["start_hour"] = from_datetime.replace(tzinfo=None).isoformat(
        timespec="minutes"
    )
    open_meteo_params.query_params["end_hour"] = to_datetime.replace(tzinfo=None).isoformat(
        timespec="minutes"
    )

    open_meteo_params.query_params["timeformat"] = "iso8601"
    open_meteo_params.query_params["timezone"] = "UTC"

    possible_api_key = get_external_sources_adapter_config().openmeteo_api_key
    if possible_api_key is not None:
        open_meteo_params.query_params["apikey"] = possible_api_key

    query_timestamp = datetime.datetime.now(tz=datetime.UTC)
    try:
        response = await open_meteo_api_call(base_url, open_meteo_params)
    except Exception as e:
        msg = "Failed request to OpenMeteo"
        logger.error(msg)
        raise AdapterHandlingException(msg) from e

    if response.status_code != 200:
        msg = (
            f"Open Meteo forecast api with query parameters from {query_params_str}"
            " produced an error."
            f" Http Status Code: {str(response.status_code)}"
        )
        logger.error(msg)
        raise AdapterHandlingException(msg)

    try:
        resp_json = response.json()
    except ValueError as e:
        msg = f"Could not parse open meteo forecast api response json:\n{response.text}"
        logger.error(msg)
        raise AdapterHandlingException(msg) from e

    # multiple coordinates will come as list. Enforcing this as common format:
    if not isinstance(resp_json, list):
        resp_json = [resp_json]

    gathered_multitsframes: list[pd.DataFrame] = []
    gathered_multitsframes.append(
        pd.DataFrame(columns=["timestamp", "metric", "value", "latitude", "longitude"])
    )
    gathered_metadata: list[dict] = []

    for dataset in resp_json:
        if not any(key in dataset for key in OPENMETEO_FREQUENCY_KEYS):
            msg = (
                "No actual timeseries data in one of the datasets: "
                "No hourly, daily or minutely_15 entry in json."
            )
            logger.error(msg)
            raise AdapterHandlingException(msg)
        append_dataset(dataset, "hourly", gathered_multitsframes, gathered_metadata)
        append_dataset(dataset, "daily", gathered_multitsframes, gathered_metadata)
        append_dataset(dataset, "minutely_15", gathered_multitsframes, gathered_metadata)

    resulting_multitsframe = pd.concat([df for df in gathered_multitsframes if len(df) != 0])

    if resulting_multitsframe.empty:
        # ensure correct columns present
        attrs = resulting_multitsframe.attrs
        resulting_multitsframe = pd.DataFrame(
            columns=["timestamp", "metric", "value", "latitude", "longitude"]
        )
        resulting_multitsframe.attrs = attrs

    # guarantee unique index:
    resulting_multitsframe = resulting_multitsframe.reset_index(drop=True)

    resulting_multitsframe.attrs["hetida-designer_filters"] = filters

    resulting_multitsframe.attrs["gathered_openmeteo_metadata"] = gathered_metadata

    resulting_multitsframe.attrs |= multitsframe_metadata(
        openmeteo_metrics(resp_json), from_datetime, to_datetime, query_timestamp
    )
    return resulting_multitsframe


possible_api_key = get_external_sources_adapter_config().openmeteo_api_key
open_meteo_url = (
    "https://api.open-meteo.com/v1"
    if possible_api_key is None
    else "https://customer-api.open-meteo.com/v1"
)


source_load_functions["open-meteo-forecast"] = functools.partial(
    load_open_meteo, base_url=f"{open_meteo_url}/forecast"
)

source_load_functions["open-meteo-archive"] = functools.partial(
    load_open_meteo, base_url=f"{open_meteo_url}/archive"
)

source_load_functions["open-meteo-historical-forecast"] = functools.partial(
    load_open_meteo, base_url=f"{open_meteo_url}/forecast"
)


async def energy_chart_api_call(
    bzn: str,
    from_datetime_str: str,
    to_datetime_str: str,
    base_url: str = "https://api.energy-charts.info/price",
    async_client: AsyncClient | None = None,
) -> Response:
    if async_client is None:
        async_client = AsyncClient(timeout=15)
    async with async_client as client:
        response = await client.get(
            base_url, params={"bzn": bzn, "start": from_datetime_str, "end": to_datetime_str}
        )
    return response


async def load_energy_charts_info_prices(
    source_id: str,  # noqa: ARG001
    filters: dict[str, str],
) -> pd.DataFrame:
    from_datetime, to_datetime = extract_time_range(filters)

    bzn = filters.get("bzn")

    if bzn is None:
        msg = "Loading Price data from energy charts requires a bidding zone (bzn)."
        raise AdapterHandlingException(msg)

    query_timestamp = datetime.datetime.now(tz=datetime.UTC)
    try:
        response = await energy_chart_api_call(
            bzn=bzn,
            from_datetime_str=from_datetime.isoformat(),
            to_datetime_str=to_datetime.isoformat(),
        )
    except Exception as e:
        msg = "Failed request to Energy-Charts.info price endpoint"
        logger.error(msg)
        raise AdapterHandlingException(msg) from e

    if response.status_code != 200:
        msg = (
            f"Energy-Charts.info price endpoint with bzn {bzn}"
            " produced an error."
            f" Http Status Code: {str(response.status_code)}"
        )
        logger.error(msg)
        raise AdapterHandlingException(msg)

    try:
        resp_json = response.json()
    except ValueError as e:
        msg = f"Could not parse open meteo forecast api response json:\n{response.text}"
        logger.error(msg)
        raise AdapterHandlingException(msg) from e

    result_df = pd.DataFrame(columns=["timestamp", "metric", "value"])
    result_df.attrs = {
        "energy-charts-info-price-metadata": {
            "license-info": (
                "Please see "
                "https://api.energy-charts.info/#/prices/day_ahead_price_price_get"
                " for details on license of data per bidding zone."
            ),
            "license": resp_json.get("license", None),
            "unit": resp_json.get("unit", None),
            "deprecated": resp_json.get("deprecated", None),
        },
    } | multitsframe_metadata(
        [
            {
                "id": "dayahead-price",
                "name": "Day-ahead price",
                "value_dimensions": [
                    {
                        "column": "value",
                        "unit": unit if isinstance(unit := resp_json.get("unit"), str) else None,
                        "measurement": "price",
                    }
                ],
            }
        ],
        from_datetime,
        to_datetime,
        query_timestamp,
    )

    result_df["timestamp"] = pd.to_datetime(resp_json.get("unix_seconds", []), unit="s", utc=True)
    result_df["metric"] = "dayahead-price"
    result_df["value"] = resp_json.get("price", [])
    result_df["value"] = result_df["value"].astype(float)

    result_df.attrs["hetida-designer_filters"] = filters

    result_df = result_df.reset_index(drop=True)

    return result_df


source_load_functions["energy-charts-info-prices"] = load_energy_charts_info_prices

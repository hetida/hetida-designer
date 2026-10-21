"""Metadata attached to the provided data

The metadata follows the hetida designer metadata conventions. They are specified by the
schemas SeriesMetadata, SingleTSFrameMetadata and MultiTSFrameMetadata of the hetida designer
openapi.json.
"""

import datetime
from typing import Any

from demo_adapter_python.demo_data.sources import get_sources

# as provided by the metadata of the plant thing nodes
TEMPERATURE_UNIT_BY_PLANT = {"plantA": "°F", "plantB": "°C"}
PRESSURE_UNIT_BY_PLANT = {"plantA": "psi", "plantB": "bar"}

TEMPERATURE_METRICS = {
    "Pickling Outfeed Temperature": "picklingUnit.outfeed.temp",
    "Pickling Influx Temperature": "picklingUnit.influx.temp",
    "Milling Outfeed Temperature": "millingUnit.outfeed.temp",
    "Milling Influx Temperature": "millingUnit.influx.temp",
}


def utc_isoformat(timestamp: datetime.datetime) -> str:
    """Isoformat of a timestamp in UTC as required by the metadata conventions

    Naive timestamps are considered to be UTC.
    """
    if timestamp.tzinfo is None:
        return timestamp.replace(tzinfo=datetime.UTC).isoformat()
    return timestamp.astimezone(datetime.UTC).isoformat()


def dataset_metadata(
    metric_key: str,
    queried_metrics: list[str],
    from_timestamp: datetime.datetime,
    to_timestamp: datetime.datetime,
    single_metric: str | None = None,
) -> dict[str, Any]:
    return {
        "metric_key": metric_key,
        **({"single_metric": single_metric} if single_metric is not None else {}),
        "queried_metrics": queried_metrics,
        "ref_interval_start_timestamp": utc_isoformat(from_timestamp),
        "ref_interval_end_timestamp": utc_isoformat(to_timestamp),
        "ref_interval_type": "closed",
    }


def plant_of(source_id: str) -> str | None:
    for plant in ("plantA", "plantB", "plantC"):
        if f".{plant}." in f".{source_id}.":
            return plant
    return None


def source_name(source_id: str) -> str:
    """The name of the source with this id, the id itself for unknown sources"""
    for source in get_sources(include_sub_objects=True):
        if source["id"] == source_id:
            return str(source["name"])
    return source_id


def value_dimension(timeseries_id: str, column: str = "value") -> dict[str, Any]:
    """The value dimension of a timeseries, whose unit and measurement depend on its id"""
    plant = plant_of(timeseries_id)
    if timeseries_id.endswith(("temp", "temp_with_state")):
        unit = TEMPERATURE_UNIT_BY_PLANT.get(plant or "")
        measurement = "temperature"
    elif timeseries_id.endswith("press"):
        unit = PRESSURE_UNIT_BY_PLANT.get(plant or "")
        measurement = "pressure"
    elif timeseries_id.endswith("anomaly_score"):
        unit = None  # dimensionless
        measurement = "anomaly score"
    else:
        unit = None
        measurement = None
    return {
        "column": column,
        "unit": unit,
        "measurement": measurement,
        "value_data_type": "float",
    }


def metric_metadata(
    timeseries_id: str, value_dimensions: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
    return {
        "id": timeseries_id,
        "name": source_name(timeseries_id),
        "value_dimensions": (
            value_dimensions if value_dimensions is not None else [value_dimension(timeseries_id)]
        ),
        "default_aggregation_method": (
            "MAX" if timeseries_id.endswith("anomaly_score") else "MEAN"
        ),
    }


def series_metadata(
    ts_id: str, from_timestamp: datetime.datetime, to_timestamp: datetime.datetime
) -> dict[str, Any]:
    """Metadata of a timeseries provided via the /timeseries endpoint"""
    return {
        "dataset_metadata": dataset_metadata(
            "id", [ts_id], from_timestamp, to_timestamp, single_metric=ts_id
        ),
        "metrics": [metric_metadata(ts_id)],
    }


def temperatures_metadata(
    mtsf_id: str, from_timestamp: datetime.datetime, to_timestamp: datetime.datetime
) -> dict[str, Any]:
    """Metadata of the temperatures multitsframe of a plant

    Its metric column contains the names of the temperature timeseries, so metric_key is
    "name", while "id" is the id of the respective timeseries.
    """
    plant_id = mtsf_id.removesuffix(".temperatures")
    return {
        "dataset_metadata": dataset_metadata(
            "name", list(TEMPERATURE_METRICS), from_timestamp, to_timestamp
        ),
        "metrics": [
            metric_metadata(f"{plant_id}.{timeseries_suffix}") | {"name": name}
            for name, timeseries_suffix in TEMPERATURE_METRICS.items()
        ],
    }


def stored_multitsframe_metadata(
    metrics: list[str], from_timestamp: datetime.datetime, to_timestamp: datetime.datetime
) -> dict[str, Any]:
    """Metadata of a multitsframe written to this adapter before

    Nothing is known about the written metrics besides their values in the metric column.
    """
    return {
        "dataset_metadata": dataset_metadata("id", metrics, from_timestamp, to_timestamp),
        "metrics": [
            {
                "id": metric,
                "name": metric,
                "value_dimensions": [{"column": "value", "unit": None, "measurement": None}],
            }
            for metric in metrics
        ],
    }


def temp_with_state_metadata(
    stsf_id: str, from_timestamp: datetime.datetime, to_timestamp: datetime.datetime
) -> dict[str, Any]:
    """Metadata of a temperature singletsframe with the state of each value"""
    return {
        "dataset_metadata": dataset_metadata(
            "id", [stsf_id], from_timestamp, to_timestamp, single_metric=stsf_id
        ),
        "metrics": [
            metric_metadata(
                stsf_id,
                value_dimensions=[
                    value_dimension(stsf_id) | {"name": "temperature"},
                    {
                        "column": "state",
                        "name": "state",
                        "unit": None,
                        "measurement": None,
                        "value_data_type": "string",
                    },
                ],
            )
        ],
    }

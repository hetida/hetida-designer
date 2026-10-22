"""Metadata attached to the provided data

The metadata follows the hetida designer metadata conventions. They are specified by the
schemas SeriesMetadata, SingleTSFrameMetadata and MultiTSFrameMetadata of the hetida designer
openapi.json.
"""

import datetime
from typing import Any

from demo_adapter_python.demo_data.sources import get_sources

# Plant A is located in Bremen (Germany), plant B in Pittsburgh (USA), each with the units and
# the time zone of its location. Units and locations are also provided by the metadata of the
# plant thing nodes.
LOCATION_BY_PLANT = {
    "plantA": {"lat": 53.073635, "long": 8.806422},
    "plantB": {"lat": 40.440624, "long": -79.995888},
}
TEMPERATURE_UNIT_BY_PLANT = {"plantA": "°C", "plantB": "°F"}
PRESSURE_UNIT_BY_PLANT = {"plantA": "bar", "plantB": "psi"}
TIMEZONE_BY_PLANT = {"plantA": "Europe/Berlin", "plantB": "America/New_York"}

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


def find_source(source_id: str) -> dict[str, Any] | None:
    for source in get_sources(include_sub_objects=True):
        if source["id"] == source_id:
            return source
    return None


def source_name(source_id: str) -> str:
    """The name of the source with this id, the id itself for unknown sources"""
    source = find_source(source_id)
    return str(source["name"]) if source is not None else source_id


def plant_timezone(source_id: str) -> dict[str, Any]:
    """The time zone of the plant of a source as default_timezone metadata field

    Empty for sources not belonging to a plant with known location.
    """
    timezone = TIMEZONE_BY_PLANT.get(plant_of(source_id) or "")
    return {"default_timezone": timezone} if timezone is not None else {}


def source_location(source_id: str) -> dict[str, Any]:
    """The path of a known source in the hierarchy as metric metadata field

    E.g. ["Plant A", "Pickling Unit", "Influx"] for the source path "Plant A / Pickling Unit /
    Influx". Empty for unknown sources.
    """
    source = find_source(source_id)
    return {"path": str(source["path"]).split(" / ")} if source is not None else {}


def simulated_recording(frequency: str = "") -> dict[str, Any]:
    """Recording information of the simulated values, which are generated hourly

    If they are resampled to another frequency, each value is the first one of its interval.
    """
    if frequency == "":
        return {"origin": "simulated", "recording_mode": "periodic", "data_frequency": "1h"}
    return {
        "origin": "simulated",
        "recording_mode": "periodic",
        "data_frequency": frequency,
        "recording_aggregation_method": "FIRST",
    }


# decimal places to display the values with
DECIMALS_BY_UNIT = {"°C": 1, "°F": 1, "bar": 2, "psi": 1}
ANOMALY_SCORE_DECIMALS = 3


def value_dimension(timeseries_id: str, column: str = "value") -> dict[str, Any]:
    """The value dimension of a timeseries, whose unit and measurement depend on its id"""
    plant = plant_of(timeseries_id)
    decimals = None
    if timeseries_id.endswith(("temp", "temp_with_state")):
        unit = TEMPERATURE_UNIT_BY_PLANT.get(plant or "")
        measurement = "temperature"
    elif timeseries_id.endswith("press"):
        unit = PRESSURE_UNIT_BY_PLANT.get(plant or "")
        measurement = "pressure"
    elif timeseries_id.endswith("anomaly_score"):
        unit = None  # dimensionless
        measurement = "anomaly score"
        decimals = ANOMALY_SCORE_DECIMALS
    else:
        unit = None
        measurement = None
    if unit is not None:
        decimals = DECIMALS_BY_UNIT.get(unit)
    return {
        "column": column,
        "unit": unit,
        "measurement": measurement,
        "value_data_type": "float",
        **({"decimals": decimals} if decimals is not None else {}),
    }


def metric_metadata(
    timeseries_id: str,
    value_dimensions: list[dict[str, Any]] | None = None,
    recording: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Metadata of a timeseries, with recording information like simulated_recording()"""
    return {
        "id": timeseries_id,
        "name": source_name(timeseries_id),
        "value_dimensions": (
            value_dimensions if value_dimensions is not None else [value_dimension(timeseries_id)]
        ),
        "default_aggregation_method": (
            "MAX" if timeseries_id.endswith("anomaly_score") else "MEAN"
        ),
        **plant_timezone(timeseries_id),
        **source_location(timeseries_id),
        **(recording or {}),
    }


def series_metadata(
    ts_id: str,
    from_timestamp: datetime.datetime,
    to_timestamp: datetime.datetime,
    recording: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Metadata of a timeseries provided via the /timeseries endpoint"""
    return {
        "dataset_metadata": dataset_metadata(
            "id", [ts_id], from_timestamp, to_timestamp, single_metric=ts_id
        ),
        "metrics": [metric_metadata(ts_id, recording=recording)],
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
            metric_metadata(f"{plant_id}.{timeseries_suffix}", recording=simulated_recording())
            | {"name": name}
            for name, timeseries_suffix in TEMPERATURE_METRICS.items()
        ],
    }


def stored_multitsframe_metadata(
    mtsf_id: str,
    metrics: list[str],
    from_timestamp: datetime.datetime,
    to_timestamp: datetime.datetime,
) -> dict[str, Any]:
    """Metadata of a multitsframe written to this adapter before

    Nothing is known about the written metrics besides their values in the metric column. As
    data of a plant, they have the time zone of the plant, which applies to all of them.
    """
    return {
        "dataset_metadata": dataset_metadata("id", metrics, from_timestamp, to_timestamp)
        | plant_timezone(mtsf_id),
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
                recording=simulated_recording(),
            )
        ],
    }

"""Metadata attached to the provided data

The metadata follows the hetida designer metadata conventions. It is built via the models of
hdhelpers.metadata.conventions, which reject metadata violating the conventions, and sent in its
JSON form (model_dump(mode="json")). The models are also specified by the schemas SeriesMetadata,
SingleTSFrameMetadata and MultiTSFrameMetadata of the hetida designer openapi.json.
"""

import datetime
from typing import Any

from hdhelpers.metadata.conventions import (
    AggregationMethod,
    IntervalType,
    MetricMetadata,
    MultiTSFrameDatasetMetadata,
    MultiTSFrameMetadata,
    RecordingMode,
    SeriesMetadata,
    SingleMetricDatasetMetadata,
    SingleTSFrameMetadata,
    ValueDataType,
    ValueDimensionMetadata,
)

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


def utc(timestamp: datetime.datetime) -> datetime.datetime:
    """A timestamp in UTC as required by the metadata conventions

    Naive timestamps are considered to be UTC.
    """
    if timestamp.tzinfo is None:
        return timestamp.replace(tzinfo=datetime.UTC)
    return timestamp.astimezone(datetime.UTC)


def ref_interval(
    from_timestamp: datetime.datetime, to_timestamp: datetime.datetime
) -> dict[str, Any]:
    """The queried interval as fields of the dataset metadata"""
    return {
        "ref_interval_start_timestamp": utc(from_timestamp),
        "ref_interval_end_timestamp": utc(to_timestamp),
        "ref_interval_type": IntervalType.CLOSED,
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


def plant_timezone(source_id: str) -> str | None:
    """The time zone of the plant of a source

    None for sources not belonging to a plant with known location.
    """
    return TIMEZONE_BY_PLANT.get(plant_of(source_id) or "")


def source_path(source_id: str) -> list[str] | None:
    """The path of a known source in the hierarchy

    E.g. ["Plant A", "Pickling Unit", "Influx"] for the source path "Plant A / Pickling Unit /
    Influx". None for unknown sources.
    """
    source = find_source(source_id)
    return str(source["path"]).split(" / ") if source is not None else None


def simulated_recording(frequency: str = "") -> dict[str, Any]:
    """Recording information of the simulated values, which are generated hourly

    If they are resampled to another frequency, each value is the first one of its interval.
    """
    if frequency == "":
        return {
            "origin": "simulated",
            "recording_mode": RecordingMode.PERIODIC,
            "data_frequency": "1h",
        }
    return {
        "origin": "simulated",
        "recording_mode": RecordingMode.PERIODIC,
        "data_frequency": frequency,
        "recording_aggregation_method": AggregationMethod.FIRST,
    }


# decimal places to display the values with
DECIMALS_BY_UNIT = {"°C": 1, "°F": 1, "bar": 2, "psi": 1}
ANOMALY_SCORE_DECIMALS = 3


def value_dimension(
    timeseries_id: str, column: str = "value", **fields: Any
) -> ValueDimensionMetadata:
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
        unit = ""  # dimensionless
        measurement = "anomaly score"
        decimals = ANOMALY_SCORE_DECIMALS
    else:
        unit = None  # unknown
        measurement = None
    if unit is not None and unit in DECIMALS_BY_UNIT:
        decimals = DECIMALS_BY_UNIT[unit]
    return ValueDimensionMetadata(
        column=column,
        unit=unit,
        measurement=measurement,
        value_data_type=ValueDataType.FLOAT,
        decimals=decimals,
        **fields,
    )


def metric_metadata(
    timeseries_id: str,
    name: str | None = None,
    value_dimensions: list[ValueDimensionMetadata] | None = None,
    recording: dict[str, Any] | None = None,
) -> MetricMetadata:
    """Metadata of a timeseries, with recording information like simulated_recording()

    Its name is the name of its source by default.
    """
    return MetricMetadata(
        id=timeseries_id,
        name=name if name is not None else source_name(timeseries_id),
        value_dimensions=(
            value_dimensions if value_dimensions is not None else [value_dimension(timeseries_id)]
        ),
        default_aggregation_method=(
            AggregationMethod.MAX
            if timeseries_id.endswith("anomaly_score")
            else AggregationMethod.MEAN
        ),
        default_timezone=plant_timezone(timeseries_id),
        path=source_path(timeseries_id),
        **(recording or {}),
    )


def series_metadata(
    ts_id: str,
    from_timestamp: datetime.datetime,
    to_timestamp: datetime.datetime,
    recording: dict[str, Any] | None = None,
) -> SeriesMetadata:
    """Metadata of a timeseries provided via the /timeseries endpoint"""
    return SeriesMetadata(
        dataset_metadata=SingleMetricDatasetMetadata(
            metric_key="id",
            single_metric=ts_id,
            queried_metrics=[ts_id],
            **ref_interval(from_timestamp, to_timestamp),
        ),
        metrics=[metric_metadata(ts_id, recording=recording)],
    )


def temperatures_metadata(
    mtsf_id: str, from_timestamp: datetime.datetime, to_timestamp: datetime.datetime
) -> MultiTSFrameMetadata:
    """Metadata of the temperatures multitsframe of a plant

    Its metric column contains the names of the temperature timeseries, so metric_key is
    "name", while "id" is the id of the respective timeseries.
    """
    plant_id = mtsf_id.removesuffix(".temperatures")
    return MultiTSFrameMetadata(
        dataset_metadata=MultiTSFrameDatasetMetadata(
            metric_key="name",
            queried_metrics=list(TEMPERATURE_METRICS),
            **ref_interval(from_timestamp, to_timestamp),
        ),
        metrics=[
            metric_metadata(
                f"{plant_id}.{timeseries_suffix}", name=name, recording=simulated_recording()
            )
            for name, timeseries_suffix in TEMPERATURE_METRICS.items()
        ],
    )


def stored_multitsframe_metadata(
    mtsf_id: str,
    metrics: list[str],
    from_timestamp: datetime.datetime,
    to_timestamp: datetime.datetime,
) -> MultiTSFrameMetadata:
    """Metadata of a multitsframe written to this adapter before

    Nothing is known about the written metrics besides their values in the metric column. As
    data of a plant, they have the time zone of the plant, which applies to all of them.
    """
    return MultiTSFrameMetadata(
        dataset_metadata=MultiTSFrameDatasetMetadata(
            metric_key="id",
            queried_metrics=metrics,
            default_timezone=plant_timezone(mtsf_id),
            **ref_interval(from_timestamp, to_timestamp),
        ),
        metrics=[
            MetricMetadata(
                id=metric,
                name=metric,
                value_dimensions=[
                    ValueDimensionMetadata(column="value", unit=None, measurement=None)
                ],
            )
            for metric in metrics
        ],
    )


def temp_with_state_metadata(
    stsf_id: str, from_timestamp: datetime.datetime, to_timestamp: datetime.datetime
) -> SingleTSFrameMetadata:
    """Metadata of a temperature singletsframe with the state of each value"""
    return SingleTSFrameMetadata(
        dataset_metadata=SingleMetricDatasetMetadata(
            metric_key="id",
            single_metric=stsf_id,
            queried_metrics=[stsf_id],
            **ref_interval(from_timestamp, to_timestamp),
        ),
        metrics=[
            metric_metadata(
                stsf_id,
                value_dimensions=[
                    value_dimension(stsf_id, name="temperature"),
                    ValueDimensionMetadata(
                        column="state",
                        name="state",
                        unit="",  # no quantity, i.e. dimensionless
                        measurement=None,
                        value_data_type=ValueDataType.STRING,
                    ),
                ],
                recording=simulated_recording(),
            )
        ],
    )

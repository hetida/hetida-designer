from copy import deepcopy
from typing import Any

import numpy as np
import pandas as pd
import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from hetdesrun.models.metadata_conventions import (
    MULTITSFRAME_METADATA_EXAMPLE,
    SERIES_METADATA_EXAMPLE,
    SINGLETSFRAME_METADATA_EXAMPLE,
    MetadataConventionIssue,
    MetadataIssueSeverity,
    check_metadata_conventions,
)

SIGNAL_ID = "7ab8c419-8745-4714-b588-57c0c772cc95"


def value_dimension(column: str = "value", **fields: Any) -> dict[str, Any]:
    return {"column": column, "unit": None, "measurement": None} | fields


def metric(metric_id: str, **fields: Any) -> dict[str, Any]:
    return {
        "id": metric_id,
        "name": f"name of {metric_id}",
        "value_dimensions": [value_dimension()],
    } | fields


def dataset_metadata(**fields: Any) -> dict[str, Any]:
    return {
        "metric_key": "id",
        "queried_metrics": [],
        "ref_interval_start_timestamp": "2026-10-18T00:00:00Z",
        "ref_interval_end_timestamp": "2026-10-19T00:00:00Z",
        "ref_interval_type": "closed",
    } | fields


def series_metadata(**metric_fields: Any) -> dict[str, Any]:
    return {
        "dataset_metadata": dataset_metadata(single_metric="a", queried_metrics=["a"]),
        "metrics": [metric("a", **metric_fields)],
    }


def multitsframe_metadata(*metric_ids: str) -> dict[str, Any]:
    return {
        "dataset_metadata": dataset_metadata(queried_metrics=list(metric_ids)),
        "metrics": [metric(metric_id) for metric_id in metric_ids],
    }


def with_dataset_metadata(metadata: dict[str, Any], **fields: Any) -> dict[str, Any]:
    changed = deepcopy(metadata)
    changed["dataset_metadata"] |= fields
    return changed


def remove(metadata: dict[str, Any], *path: str | int) -> dict[str, Any]:
    removed = deepcopy(metadata)
    obj: Any = removed
    for part in path[:-1]:
        obj = obj[part]
    del obj[path[-1]]
    return removed


# a comment as the hetida platform sends it: Jackson serializes Instants as UTC isoformat strings
# with Z and includes null fields
platform_comment: dict[str, Any] = {
    "id": "0b5f0f0e-6d1c-4f7e-9a51-1f3c2a9e8d11",
    "start_date": "2026-10-18T06:00:00Z",
    "end_date": "2026-10-18T07:30:00Z",
    "created_at": "2026-10-18T08:12:45.123Z",
    "edited_at": None,
    "content": "Pump maintenance",
    "username": "jdoe",
    "tags": ["maintenance"],
    "replies": [
        {
            "id": "5e1c7d2a-8b3f-4c6e-9d0a-2f4b6c8e0a13",
            "created_at": "2026-10-18T09:00:00Z",
            "edited_at": "2026-10-18T09:05:00.500Z",
            "content": "Done, pump runs again",
            "username": "asmith",
        }
    ],
}

# the metadata the hetida platform sends for a timeseries of a SERIES read
platform_series_metadata: dict[str, Any] = {
    "dataset_metadata": {
        "metric_key": "id",
        "single_metric": SIGNAL_ID,
        "queried_metrics": [SIGNAL_ID],
        "signal_group": None,
        "ref_interval_start_timestamp": "2026-10-18T00:00:00Z",
        "ref_interval_end_timestamp": "2026-10-19T00:00:00Z",
        "ref_interval_type": "closed",
        "ref_data_frequency": None,
        "ref_data_frequency_offset": None,
        "invalidation_interval_start": None,
        "invalidation_interval_end": None,
        "invalidation_interval_type": None,
        "invalidate_dataset": None,
        "delete_invalidated": None,
        "only_invalidate": None,
        "ref_dataset_discrete": None,
        "invalidation_timestamp": None,
        "new_data_invalidation_date": None,
    },
    "metrics": [
        {
            "id": SIGNAL_ID,
            "external_id": "water.north.level",
            "name": "Water-lvl-north",
            "display_name": None,
            "description": None,
            # property values of the platform, possibly as strings
            "inherited": {"signal_role": "level", "latitude": "51.43"},
            "comments": [
                platform_comment,
                # a comment on a single point in time without tags and replies
                platform_comment
                | {
                    "start_date": "2026-10-18T12:00:00Z",
                    "end_date": "2026-10-18T12:00:00Z",
                    "tags": [],
                    "replies": [],
                },
            ],
            "value_dimensions": [
                {
                    "column": "value",
                    "name": "Water-lvl-north",
                    "display_name": None,
                    "short_display_name": None,
                    "description": None,
                    "unit": "m",
                    "measurement": "level",
                    "value_data_type": "float",
                }
            ],
            "default_aggregation_method": "AVG",
        }
    ],
}

# the metadata the hetida platform sends for a MULTITSFRAME read of a signal group
platform_multitsframe_metadata: dict[str, Any] = {
    "dataset_metadata": platform_series_metadata["dataset_metadata"]
    | {
        "single_metric": None,
        "queried_metrics": [SIGNAL_ID, "pump"],
        "signal_group": {"id": "3c2e1d4f", "name": "Pumps north", "description": None},
    },
    "metrics": [
        platform_series_metadata["metrics"][0] | {"display_name": "Water level"},
        platform_series_metadata["metrics"][0]
        | {
            "id": "pump",
            "external_id": None,
            "comments": [],
            "value_dimensions": [value_dimension()],
            "default_aggregation_method": None,
        },
    ],
}


def multitsframe(attrs: dict[str, Any], metrics: list[str], **columns: list) -> pd.DataFrame:
    frame = pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-10-18T06:00:00Z", periods=len(metrics), freq="1h"),
            "metric": metrics,
            "value": np.arange(len(metrics), dtype=float),
        }
        | columns
    )
    frame.attrs = deepcopy(attrs)
    return frame


def series(attrs: dict[str, Any]) -> pd.Series:
    ser = pd.Series([1.0, 2.0], index=pd.date_range("2026-10-18T06:00:00Z", periods=2, freq="1h"))
    ser.attrs = deepcopy(attrs)
    return ser


def singletsframe(attrs: dict[str, Any]) -> pd.DataFrame:
    frame = pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-10-18T06:00:00Z", periods=2, freq="1h"),
            "value": [21.3, 21.5],
            "state": [0, 1],
        }
    )
    frame.attrs = deepcopy(attrs)
    return frame


def issues_as_tuples(
    issues: list[MetadataConventionIssue],
) -> list[tuple[MetadataIssueSeverity, str]]:
    return [(issue.severity, issue.location) for issue in issues]


def errors_of(issues: list[MetadataConventionIssue]) -> list[str]:
    return [issue.location for issue in issues if issue.severity == MetadataIssueSeverity.ERROR]


@pytest.mark.parametrize(
    ("obj", "data_type"),
    [
        (SERIES_METADATA_EXAMPLE, "SERIES"),
        (SINGLETSFRAME_METADATA_EXAMPLE, "SINGLETSFRAME"),
        (MULTITSFRAME_METADATA_EXAMPLE, "MULTITSFRAME"),
        (platform_series_metadata, "SERIES"),
        (platform_multitsframe_metadata, "MULTITSFRAME"),
        (multitsframe_metadata(), "MULTITSFRAME"),
        (series(platform_series_metadata), None),
        (series(series_metadata()), None),
        (multitsframe(platform_multitsframe_metadata, [SIGNAL_ID, "pump"]), None),
        (multitsframe(multitsframe_metadata("a", "b"), ["a", "b", "a"]), None),
        (singletsframe(SINGLETSFRAME_METADATA_EXAMPLE), None),
    ],
)
def test_conforming_metadata(obj: Any, data_type: Any) -> None:
    assert check_metadata_conventions(obj, data_type) == []


@pytest.mark.parametrize(
    ("data_type", "metadata", "location"),
    [
        ("SERIES", {}, "dataset_metadata"),
        ("SERIES", remove(series_metadata(), "metrics"), "metrics"),
        (
            "SERIES",
            remove(series_metadata(), "dataset_metadata", "metric_key"),
            "dataset_metadata.metric_key",
        ),
        (
            "SERIES",
            remove(series_metadata(), "dataset_metadata", "queried_metrics"),
            "dataset_metadata.queried_metrics",
        ),
        (
            "SERIES",
            remove(series_metadata(), "dataset_metadata", "single_metric"),
            "dataset_metadata.single_metric",
        ),
        ("SERIES", remove(series_metadata(), "metrics", 0, "id"), "metrics[0].id"),
        ("SERIES", remove(series_metadata(), "metrics", 0, "name"), "metrics[0].name"),
        (
            "SERIES",
            remove(series_metadata(), "metrics", 0, "value_dimensions"),
            "metrics[0].value_dimensions",
        ),
        (
            "SERIES",
            remove(series_metadata(), "metrics", 0, "value_dimensions", 0, "column"),
            "metrics[0].value_dimensions[0].column",
        ),
        (
            "SERIES",
            remove(series_metadata(), "metrics", 0, "value_dimensions", 0, "unit"),
            "metrics[0].value_dimensions[0].unit",
        ),
        (
            "SERIES",
            remove(series_metadata(), "metrics", 0, "value_dimensions", 0, "measurement"),
            "metrics[0].value_dimensions[0].measurement",
        ),
        ("SINGLETSFRAME", remove(series_metadata(), "metrics", 0, "name"), "metrics[0].name"),
        (
            "MULTITSFRAME",
            remove(multitsframe_metadata("a"), "dataset_metadata", "queried_metrics"),
            "dataset_metadata.queried_metrics",
        ),
    ],
)
def test_required_fields(data_type: Any, metadata: dict[str, Any], location: str) -> None:
    issues = check_metadata_conventions(metadata, data_type)

    assert location in errors_of(issues)
    assert next(issue for issue in issues if issue.location == location).message == (
        "Field required"
    )


@pytest.mark.parametrize("data_type", ["SERIES", "SINGLETSFRAME"])
@pytest.mark.parametrize("metric_count", [0, 2])
def test_single_metric_types_have_exactly_one_metric(data_type: Any, metric_count: int) -> None:
    metadata = series_metadata()
    metadata["metrics"] = [metric(f"m{index}") for index in range(metric_count)]

    assert "metrics" in errors_of(check_metadata_conventions(metadata, data_type))


def test_value_dimensions_must_not_be_empty() -> None:
    assert "metrics[0].value_dimensions" in errors_of(
        check_metadata_conventions(series_metadata(value_dimensions=[]), "SERIES")
    )


def test_ref_interval_is_required_unless_discrete() -> None:
    metadata = with_dataset_metadata(
        series_metadata(),
        ref_interval_start_timestamp=None,
        ref_interval_end_timestamp=None,
        ref_interval_type=None,
    )

    assert errors_of(check_metadata_conventions(metadata, "SERIES")) == [
        "dataset_metadata.ref_interval_start_timestamp",
        "dataset_metadata.ref_interval_end_timestamp",
        "dataset_metadata.ref_interval_type",
    ]

    metadata["dataset_metadata"]["ref_dataset_discrete"] = True
    assert check_metadata_conventions(metadata, "SERIES") == []


@pytest.mark.parametrize(
    ("metadata", "location", "message_part"),
    [
        ([1, 2], "", "object"),
        (
            with_dataset_metadata(series_metadata(), ref_interval_type="half_open"),
            "dataset_metadata.ref_interval_type",
            "closed",
        ),
        (
            with_dataset_metadata(
                series_metadata(), ref_interval_start_timestamp="2026-10-18T00:00:00+02:00"
            ),
            "dataset_metadata.ref_interval_start_timestamp",
            "ending with Z or +00:00, got '2026-10-18T00:00:00+02:00'.",
        ),
        (
            with_dataset_metadata(series_metadata(), only_invalidate="true"),
            "dataset_metadata.only_invalidate",
            "boolean",
        ),
        (series_metadata(id=42), "metrics[0].id", "string"),
        (series_metadata(name=None), "metrics[0].name", "string"),
        (
            series_metadata(value_dimensions=[value_dimension(unit=3)]),
            "metrics[0].value_dimensions[0].unit",
            "string",
        ),
        (
            series_metadata(default_aggregation_method="mean"),
            "metrics[0].default_aggregation_method",
            "MEAN",
        ),
        (
            series_metadata(comments=[{"created_at": "2026-10-18T08:12:45"}]),
            "metrics[0].comments[0].created_at",
            "UTC isoformat timestamp",
        ),
        (
            series_metadata(comments=[platform_comment | {"tags": "maintenance"}]),
            "metrics[0].comments[0].tags",
            "array",
        ),
        (
            series_metadata() | {"metrics": {"a": {"unit": "m"}}},
            "metrics",
            "older metadata convention",
        ),
    ],
)
def test_structure_errors(metadata: Any, location: str, message_part: str) -> None:
    issues = check_metadata_conventions(metadata, "SERIES")

    assert issues_as_tuples(issues) == [(MetadataIssueSeverity.ERROR, location)]
    assert message_part in issues[0].message


@pytest.mark.parametrize(
    "method", ["MEAN", "AVG", "MEDIAN", "SUM", "MIN", "MAX", "FIRST", "LAST", "COUNT", None]
)
def test_aggregation_methods(method: Any) -> None:
    metadata = series_metadata(default_aggregation_method=method)

    assert check_metadata_conventions(metadata, "SERIES") == []


def test_inherited_properties_are_arbitrary() -> None:
    metadata = series_metadata(inherited={"latitude": "51.43", "longitude": 7.58, "unit": None})

    assert check_metadata_conventions(metadata, "SERIES") == []


def test_recording_and_location_information() -> None:
    metadata = with_dataset_metadata(
        series_metadata(
            path=["Waterworks North", "Gauge North"],
            origin="OPC_UA",
            recording_mode="periodic",
            data_frequency="15min",
            data_frequency_offset="0s",
            recording_aggregation_method="AVG",
        ),
        query_timestamp="2026-10-19T00:05:00Z",
        default_aggregation_interval="1h",
    )

    assert check_metadata_conventions(metadata, "SERIES") == []


@pytest.mark.parametrize(
    "metadata",
    [
        # the frequency of the dataset defines the aggregated intervals
        with_dataset_metadata(
            series_metadata(recording_mode="periodic", recording_aggregation_method="MAX"),
            ref_data_frequency="1h",
        ),
        series_metadata(
            recording_mode="on_change",
            data_frequency="1D",
            value_dimensions=[value_dimension(deadband=0)],
        ),
        series_metadata(recording_mode="irregular"),
        series_metadata(data_frequency="P1D"),
    ],
)
def test_consistent_recording_information(metadata: dict[str, Any]) -> None:
    assert check_metadata_conventions(metadata, "SERIES") == []


@pytest.mark.parametrize(
    ("metadata", "location", "message_part"),
    [
        (series_metadata(path="Plant A/Unit"), "metrics[0].path", "array"),
        (series_metadata(path=["Plant A", 3]), "metrics[0].path[1]", "string"),
        (series_metadata(recording_mode="continuous"), "metrics[0].recording_mode", "periodic"),
        (
            series_metadata(recording_aggregation_method="mean"),
            "metrics[0].recording_aggregation_method",
            "MEAN",
        ),
        (
            series_metadata(value_dimensions=[value_dimension(deadband=-0.1)]),
            "metrics[0].value_dimensions[0].deadband",
            "greater than or equal to 0",
        ),
        (
            with_dataset_metadata(series_metadata(), query_timestamp="2026-10-19T02:05:00+02:00"),
            "dataset_metadata.query_timestamp",
            "UTC isoformat timestamp",
        ),
        (
            with_dataset_metadata(series_metadata(), default_aggregation_interval=60),
            "dataset_metadata.default_aggregation_interval",
            "string",
        ),
    ],
)
def test_recording_and_location_structure_errors(
    metadata: Any, location: str, message_part: str
) -> None:
    issues = check_metadata_conventions(metadata, "SERIES")

    assert issues_as_tuples(issues) == [(MetadataIssueSeverity.ERROR, location)]
    assert message_part in issues[0].message


@pytest.mark.parametrize(
    ("metadata", "location", "message_part"),
    [
        (
            with_dataset_metadata(series_metadata(), ref_data_frequency="every 5 minutes"),
            "dataset_metadata.ref_data_frequency",
            "not a Pandas date offset alias",
        ),
        (
            with_dataset_metadata(series_metadata(), ref_data_frequency_offset=""),
            "dataset_metadata.ref_data_frequency_offset",
            "not a Pandas date offset alias",
        ),
        (
            with_dataset_metadata(series_metadata(), default_aggregation_interval="1month"),
            "dataset_metadata.default_aggregation_interval",
            "not a Pandas date offset alias",
        ),
        (
            series_metadata(data_frequency="hourly"),
            "metrics[0].data_frequency",
            "not a Pandas date offset alias",
        ),
        (
            series_metadata(data_frequency="1h", data_frequency_offset="4 mins later"),
            "metrics[0].data_frequency_offset",
            "not a Pandas date offset alias",
        ),
        (
            series_metadata(
                recording_mode="on_change", recording_aggregation_method="MEAN", data_frequency="1h"
            ),
            "metrics[0].recording_aggregation_method",
            "Only meaningful for recording_mode periodic",
        ),
        (
            series_metadata(recording_aggregation_method="MEAN", data_frequency="1h"),
            "metrics[0].recording_aggregation_method",
            "Only meaningful for recording_mode periodic",
        ),
        (
            series_metadata(recording_mode="periodic", recording_aggregation_method="MEAN"),
            "metrics[0].recording_aggregation_method",
            "Requires data_frequency",
        ),
    ],
)
def test_recording_consistency_errors(
    metadata: dict[str, Any], location: str, message_part: str
) -> None:
    issues = check_metadata_conventions(metadata, "SERIES")

    assert issues_as_tuples(issues) == [(MetadataIssueSeverity.ERROR, location)]
    assert message_part in issues[0].message


@pytest.mark.parametrize("recording_mode", [None, "periodic", "irregular"])
def test_deadband_without_on_change_recording_warns(recording_mode: Any) -> None:
    metadata = series_metadata(
        recording_mode=recording_mode, value_dimensions=[value_dimension(deadband=0.5)]
    )

    issues = check_metadata_conventions(metadata, "SERIES")

    assert issues_as_tuples(issues) == [
        (MetadataIssueSeverity.WARNING, "metrics[0].value_dimensions[0].deadband")
    ]


@pytest.mark.parametrize(
    "metadata",
    [
        with_dataset_metadata(
            series_metadata(), ref_interval_start_timestamp=pd.Timestamp("2026-01-01", tz="UTC")
        ),
        series_metadata(inherited={"elevation": float("nan")}),
    ],
)
def test_metadata_not_json_serializable(metadata: dict[str, Any]) -> None:
    issues = check_metadata_conventions(metadata, "SERIES")

    assert issues_as_tuples(issues) == [(MetadataIssueSeverity.ERROR, "")]
    assert "JSON serializable" in issues[0].message


@pytest.mark.parametrize(
    ("data_type", "metadata", "location"),
    [
        (
            "MULTITSFRAME",
            with_dataset_metadata(multitsframe_metadata("a"), metric_key="external_id"),
            "metrics[0]",
        ),
        ("MULTITSFRAME", multitsframe_metadata("a", "b", "a"), "metrics"),
        (
            "SERIES",
            series_metadata(value_dimensions=[value_dimension(), value_dimension()]),
            "metrics[0].value_dimensions",
        ),
        (
            "MULTITSFRAME",
            multitsframe_metadata("a")
            | {"value_dimensions_shared": [{"column": "value"}, {"column": "value"}]},
            "value_dimensions_shared",
        ),
        (
            "MULTITSFRAME",
            with_dataset_metadata(multitsframe_metadata("a", "b"), single_metric="a"),
            "dataset_metadata.single_metric",
        ),
        (
            "SERIES",
            with_dataset_metadata(series_metadata(), single_metric="b"),
            "dataset_metadata.single_metric",
        ),
        (
            "SERIES",
            with_dataset_metadata(
                series_metadata(), only_invalidate=True, invalidate_dataset=False
            ),
            "dataset_metadata.only_invalidate",
        ),
        (
            "SERIES",
            with_dataset_metadata(
                series_metadata(), invalidation_interval_end="2026-01-01T00:00:00Z"
            ),
            "dataset_metadata.invalidation_interval_start",
        ),
        (
            "SERIES",
            with_dataset_metadata(
                series_metadata(), ref_interval_start_timestamp="2026-10-20T00:00:00.000000000Z"
            ),
            "dataset_metadata.ref_interval_start_timestamp",
        ),
        (
            "SERIES",
            series_metadata(comments=[platform_comment | {"end_date": None}]),
            "metrics[0].comments[0].end_date",
        ),
        (
            "SERIES",
            series_metadata(comments=[platform_comment | {"start_date": "2026-10-18T08:00:00Z"}]),
            "metrics[0].comments[0].start_date",
        ),
        # a SERIES has the value dimension "value", which must be described
        (
            "SERIES",
            series_metadata(value_dimensions=[value_dimension("temperature")]),
            "metrics[0].value_dimensions",
        ),
    ],
)
def test_consistency_errors(data_type: Any, metadata: dict[str, Any], location: str) -> None:
    assert errors_of(check_metadata_conventions(metadata, data_type)) == [location]


def test_consistency_is_only_checked_for_valid_structure() -> None:
    metadata = with_dataset_metadata(multitsframe_metadata("a", "a"), ref_interval_type="half_open")

    assert issues_as_tuples(check_metadata_conventions(metadata, "MULTITSFRAME")) == [
        (MetadataIssueSeverity.ERROR, "dataset_metadata.ref_interval_type")
    ]


def test_metadata_without_data_requires_data_type() -> None:
    with pytest.raises(ValueError, match="data type is required"):
        check_metadata_conventions(series_metadata())


def test_multitsframe_inconsistent_with_metadata() -> None:
    metadata = multitsframe_metadata("a", "b")
    metadata["dataset_metadata"]["queried_metrics"] = ["a"]
    metadata["metrics"][0]["value_dimensions"].append(value_dimension("quality"))

    issues = check_metadata_conventions(multitsframe(metadata, ["a", "b", "c"], state=[0, 1, 0]))

    assert issues_as_tuples(issues) == [
        (MetadataIssueSeverity.ERROR, "metrics"),
        (MetadataIssueSeverity.ERROR, "dataset_metadata.queried_metrics"),
        (MetadataIssueSeverity.ERROR, "metrics[0].value_dimensions"),
        (MetadataIssueSeverity.ERROR, "metrics[1].value_dimensions"),
        (MetadataIssueSeverity.WARNING, "metrics[0].value_dimensions[1].column"),
    ]
    assert '"c"' in issues[0].message
    assert '"b", "c"' in issues[1].message
    assert '"state"' in issues[2].message
    assert '"quality"' in issues[4].message


def test_multitsframe_metric_listing_is_shortened() -> None:
    metric_ids = [f"m{i:02}" for i in range(15)]
    metadata = multitsframe_metadata("a")
    metadata["dataset_metadata"]["queried_metrics"] = ["a", *metric_ids]

    issues = check_metadata_conventions(multitsframe(metadata, ["a", *metric_ids]))

    assert issues_as_tuples(issues) == [(MetadataIssueSeverity.ERROR, "metrics")]
    assert '"m09" and 5 more' in issues[0].message


def test_singletsframe_inconsistent_with_metadata() -> None:
    metadata = deepcopy(SINGLETSFRAME_METADATA_EXAMPLE)
    del metadata["metrics"][0]["value_dimensions"][1]
    metadata["value_dimensions_shared"] = [{"column": "quality"}]

    assert issues_as_tuples(check_metadata_conventions(singletsframe(metadata))) == [
        (MetadataIssueSeverity.ERROR, "metrics[0].value_dimensions"),
        (MetadataIssueSeverity.WARNING, "value_dimensions_shared[0].column"),
    ]


@pytest.mark.parametrize(
    ("metadata", "location", "message_part"),
    [
        (
            series_metadata(displayName="A"),
            "metrics[0].displayName",
            'Did you mean "display_name"?',
        ),
        (
            series_metadata(value_dimensions=[value_dimension(measurment="level")]),
            "metrics[0].value_dimensions[0].measurment",
            'Did you mean "measurement"?',
        ),
        (series_metadata(unit="m"), "metrics[0].unit", "under value_dimensions instead"),
        (
            with_dataset_metadata(series_metadata(), ref_metrics=["a"]),
            "dataset_metadata.ref_metrics",
            "Additional fields are allowed",
        ),
        (
            series_metadata(comments=[platform_comment | {"author": "jdoe"}]),
            "metrics[0].comments[0].author",
            "Additional fields are allowed",
        ),
        (series_metadata() | {"anomalies": []}, "anomalies", "Additional fields are allowed"),
    ],
)
def test_unknown_fields(metadata: dict[str, Any], location: str, message_part: str) -> None:
    issues = check_metadata_conventions(metadata, "SERIES")

    assert issues_as_tuples(issues) == [(MetadataIssueSeverity.WARNING, location)]
    assert message_part in issues[0].message


def test_custom_metric_key_field_is_not_unknown() -> None:
    metadata = with_dataset_metadata(
        series_metadata(externalTimeSeriesId="a"), metric_key="externalTimeSeriesId"
    )

    assert check_metadata_conventions(metadata, "SERIES") == []


def test_unknown_fields_explain_missing_required_fields() -> None:
    metadata = series_metadata()
    metadata["metrics"][0]["valueDimensions"] = metadata["metrics"][0].pop("value_dimensions")

    issues = check_metadata_conventions(metadata, "SERIES")

    assert issues_as_tuples(issues) == [
        (MetadataIssueSeverity.ERROR, "metrics[0].value_dimensions"),
        (MetadataIssueSeverity.WARNING, "metrics[0].valueDimensions"),
    ]
    assert 'Did you mean "value_dimensions"?' in issues[1].message


def test_deprecated_channel_id() -> None:
    metadata = multitsframe_metadata("a", "b")
    metadata["metrics"][0]["channel_id"] = "abc"
    metadata["metrics"][1] |= {"signal_id": "def", "channel_id": None}

    issues = check_metadata_conventions(metadata, "MULTITSFRAME")

    assert issues_as_tuples(issues) == [(MetadataIssueSeverity.WARNING, "metrics[0].channel_id")]
    assert '"signal_id"' in issues[0].message


@pytest.mark.filterwarnings(
    "ignore:Duplicate Operation ID receive_execution_response__callback_url__post "
    "for function receive_execution_response:UserWarning"
)
def test_metadata_conventions_in_openapi(app_without_auth: FastAPI) -> None:
    openapi = app_without_auth.openapi()
    component_schemas = openapi["components"]["schemas"]

    assert {
        "SeriesMetadata",
        "SingleTSFrameMetadata",
        "MultiTSFrameMetadata",
        "SingleMetricDatasetMetadata",
        "MultiTSFrameDatasetMetadata",
        "MetricMetadata",
        "ValueDimensionMetadata",
        "SharedValueDimensionMetadata",
        "InheritedMetricMetadata",
        "MetricComment",
        "AggregationMethod",
        "IntervalType",
        "RecordingMode",
    } <= set(component_schemas)
    assert component_schemas["SeriesMetadata"]["examples"] == [SERIES_METADATA_EXAMPLE]
    assert component_schemas["MultiTSFrameMetadata"]["examples"] == [MULTITSFRAME_METADATA_EXAMPLE]
    assert set(component_schemas["MetricMetadata"]["required"]) == {
        "id",
        "name",
        "value_dimensions",
    }
    assert set(component_schemas["ValueDimensionMetadata"]["required"]) == {
        "column",
        "unit",
        "measurement",
    }
    assert "else" in component_schemas["SingleMetricDatasetMetadata"]
    assert component_schemas["MetricMetadata"]["properties"]["channel_id"]["deprecated"] is True
    assert [
        schema["$ref"]
        for schema in component_schemas["WrappedTimeseriesData"]["properties"]["__metadata__"][
            "anyOf"
        ]
    ] == [
        "#/components/schemas/SeriesMetadata",
        "#/components/schemas/SingleTSFrameMetadata",
        "#/components/schemas/MultiTSFrameMetadata",
    ]
    assert "/api/metadata-conventions/check/{data_type}" in openapi["paths"]


CHECK_URL = "/api/metadata-conventions/check/"

multitsframe_data = {
    "timestamp": ["2026-10-18T00:00:00Z", "2026-10-18T00:00:00Z", "2026-10-18T01:00:00Z"],
    "metric": [SIGNAL_ID, "pump", "other"],
    "value": [2.5, 120.0, 80.0],
}


@pytest.mark.asyncio
async def test_check_endpoint(async_test_client: AsyncClient, mocked_clean_test_db_session) -> None:
    async with async_test_client as ac:
        conforming = await ac.post(
            CHECK_URL + "MULTITSFRAME",
            json={
                "__hd_wrapped_data_object__": "DATAFRAME",
                "__metadata__": platform_multitsframe_metadata,
                "__data__": {key: values[:2] for key, values in multitsframe_data.items()},
            },
        )
        inconsistent = await ac.post(
            CHECK_URL + "MULTITSFRAME",
            json={
                "__hd_wrapped_data_object__": "DATAFRAME",
                "__metadata__": platform_multitsframe_metadata,
                "__data__": multitsframe_data,
            },
        )
        with_warning = await ac.post(
            CHECK_URL + "SERIES",
            json={
                "__hd_wrapped_data_object__": "SERIES",
                "__metadata__": series_metadata(units="m"),
                "__data__": {
                    "index": ["2026-10-18T00:00:00Z", "2026-10-18T00:00:00Z"],
                    "data": [1.0, 2.0],
                },
                "__data_parsing_options__": {"orient": "split"},
            },
        )
        unparsable_data = await ac.post(
            CHECK_URL + "SINGLETSFRAME",
            json={
                "__hd_wrapped_data_object__": "DATAFRAME",
                "__metadata__": [],
                "__data__": {"value": [1.0, 2.0]},
            },
        )
        only_metadata = await ac.post(
            CHECK_URL + "SERIES",
            json={
                "__hd_wrapped_data_object__": "SERIES",
                "__metadata__": series_metadata(value_dimensions=[value_dimension("temp")]),
            },
        )

    assert conforming.status_code == 200
    assert conforming.json() == {"valid": True, "issues": []}

    assert inconsistent.status_code == 200
    assert inconsistent.json()["valid"] is False
    assert [issue["location"] for issue in inconsistent.json()["issues"]] == [
        "__metadata__.metrics",
        "__metadata__.dataset_metadata.queried_metrics",
    ]

    assert with_warning.status_code == 200
    assert with_warning.json()["valid"] is True
    assert [(issue["severity"], issue["location"]) for issue in with_warning.json()["issues"]] == [
        ("warning", "__metadata__.metrics[0].units")
    ]

    assert unparsable_data.status_code == 200
    assert unparsable_data.json()["valid"] is False
    assert [
        (issue["severity"], issue["location"]) for issue in unparsable_data.json()["issues"]
    ] == [
        ("error", "__data__"),
        ("error", "__metadata__"),
    ]
    assert "timestamp" in unparsable_data.json()["issues"][0]["message"]

    assert only_metadata.status_code == 200
    assert only_metadata.json()["valid"] is False
    assert [(issue["severity"], issue["location"]) for issue in only_metadata.json()["issues"]] == [
        ("error", "__metadata__.metrics[0].value_dimensions"),
        ("warning", "__metadata__.metrics[0].value_dimensions[0].column"),
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("data_type", "wrapped_data"),
    [
        ("SERIES", {"__hd_wrapped_data_object__": "DATAFRAME", "__metadata__": {}}),
        ("MULTITSFRAME", {"__hd_wrapped_data_object__": "SERIES", "__metadata__": {}}),
        ("DATAFRAME", {"__hd_wrapped_data_object__": "DATAFRAME", "__metadata__": {}}),
        ("SERIES", {"__hd_wrapped_data_object__": "SERIES", "__metadata": {}}),
        # misspelled optional field, which would be ignored silently otherwise
        ("SERIES", {"__hd_wrapped_data_object__": "SERIES", "__metadata__": {}, "__data": [1.0]}),
        ("SERIES", {"__metadata__": {}, "__data__": [1.0]}),
    ],
)
async def test_check_endpoint_rejects_requests_not_in_wrapped_format(
    async_test_client: AsyncClient,
    mocked_clean_test_db_session,
    data_type: str,
    wrapped_data: dict[str, Any],
) -> None:
    async with async_test_client as ac:
        response = await ac.post(CHECK_URL + data_type, json=wrapped_data)

    assert response.status_code == 422

"""Documentation for Convert Series to SingleTSFrame

# Convert Series to SingleTSFrame

## Description
Convert a Series into a SingleTSFrame.

## Inputs
* **series** (Pandas Series): The input Series must have an index of timestamps or of ISO 8601 timestamp strings. It is converted to UTC.
* **value_column_name** (String, optional): Name of the value column of the resulting SingleTSFrame. Default: "value".

## Outputs
* **singletsframe** (SingleTSFrame): The output SingleTSFrame constructed from the series, consisting of a "timestamp" column and one value column.

## Details
A SERIES and a SINGLETSFRAME both represent a single timeseries. The difference is that a SERIES is one-dimensional and carries its timestamps in the index, while a SINGLETSFRAME carries its timestamps in a "timestamp" column and can have arbitrarily many value dimensions. This component therefore moves the index into a "timestamp" column and the values into a single value column.

The attributes (`.attrs`) of the series are carried over, since the [metadata conventions](https://hetida.github.io/hetida-designer/user_guide/attached_metadata/) identify the single metric the same way for both types, namely via `dataset_metadata.single_metric`. If no `single_metric` is set in the metadata, it is determined so that it matches the metric under `metrics`, i.e. its field named by `dataset_metadata.metric_key` (defaulting to "id"):

* If the metadata has a single metric with this field, its value is used.
* Otherwise the series name is used, if the series has one. It is also set in this field of a single metric lacking it. If this field has another value, the series name is set in the field `metric` of the metric instead, and `metric_key` becomes "metric".

The determined `single_metric` is added to `queried_metrics`, too. If **value_column_name** is not "value", the value dimension "value" of the metadata is renamed accordingly, so that metadata following the conventions for a SERIES follows them for the resulting SINGLETSFRAME, too.

Raises a ComponentInputValidationException if the index of the series cannot be interpreted as timestamps.

## Examples
The json input of a typical call of this component is
```
{
    "series": {
        "2019-08-01T15:42:36.000Z": 5.7,
        "2019-08-01T15:45:36.000Z": 3.1
    }
}
```
"""

import copy

import pandas as pd

from hdutils import ComponentInputValidationException

# Field of the metric holding the series name if the field identifying the metric has another
# value, which is kept this way
METRIC_NAME_FIELD = "metric"


def identify_single_metric(attrs, series_name):
    """Set single_metric of the dataset metadata if it is missing

    It is determined consistently with the metadata conventions: the metric_key field (default
    "id") of the single metric under metrics if it is a string, otherwise series_name, which is
    then also set in this field of the single metric if missing, or in METRIC_NAME_FIELD
    becoming the metric_key if the field has another value. The single metric is added to
    queried_metrics. Nothing is set if neither a metric nor series_name identify it, or if
    there are several metrics. Changes attrs in place.
    """
    dataset_metadata = attrs.get("dataset_metadata")
    if dataset_metadata is None and series_name is not None:
        dataset_metadata = attrs["dataset_metadata"] = {}
    if not isinstance(dataset_metadata, dict) or dataset_metadata.get("single_metric") is not None:
        return

    metric_key = dataset_metadata.get("metric_key")
    if not isinstance(metric_key, str):
        metric_key = "id"
    metrics = attrs.get("metrics")
    metric = (
        metrics[0]
        if isinstance(metrics, list) and len(metrics) == 1 and isinstance(metrics[0], dict)
        else None
    )
    if metric is not None and isinstance(metric.get(metric_key), str):
        single_metric = metric[metric_key]
    elif series_name is None or (isinstance(metrics, list) and len(metrics) > 1):
        return
    else:
        single_metric = str(series_name)
        if metric is not None and metric.get(metric_key) is None:
            metric[metric_key] = single_metric
        elif metric is not None:
            metric[METRIC_NAME_FIELD] = single_metric
            dataset_metadata["metric_key"] = METRIC_NAME_FIELD

    dataset_metadata["single_metric"] = single_metric
    queried_metrics = dataset_metadata.get("queried_metrics")
    if not isinstance(queried_metrics, list):
        dataset_metadata["queried_metrics"] = [single_metric]
    elif single_metric not in queried_metrics:
        queried_metrics.append(single_metric)


def rename_value_dimension(attrs, column, new_column):
    """Rename a value dimension in metadata following the metadata conventions

    Renames it in the value dimensions of all metrics and in the shared value dimensions.
    Changes attrs in place.
    """
    metrics = attrs.get("metrics") if isinstance(attrs.get("metrics"), list) else []
    for value_dimensions in [
        *(metric.get("value_dimensions") for metric in metrics if isinstance(metric, dict)),
        attrs.get("value_dimensions_shared"),
    ]:
        for value_dimension in value_dimensions if isinstance(value_dimensions, list) else []:
            if isinstance(value_dimension, dict) and value_dimension.get("column") == column:
                value_dimension["column"] = new_column


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "series": {"data_type": "SERIES"},
        "value_column_name": {"data_type": "STRING", "default_value": "value"},
    },
    "outputs": {
        "singletsframe": {"data_type": "SINGLETSFRAME"},
    },
    "name": "Convert Series to SingleTSFrame",
    "category": "Connectors",
    "description": "Convert a Series into a SingleTSFrame",
    "version_tag": "1.0.0",
    "id": "e5f84360-d059-443d-a5c6-d86ff2d2e405",
    "revision_group_id": "e058c62a-78d8-4e0a-bb2c-349e28e8f507",
    "state": "RELEASED",
    "released_timestamp": "2026-08-05T10:00:00+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, series, value_column_name="value"):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    if value_column_name in (None, "") or value_column_name == "timestamp":
        raise ComponentInputValidationException(
            'The value_column_name must be a non-empty string other than "timestamp".',
            invalid_component_inputs=["value_column_name"],
        )

    try:
        timestamps = pd.to_datetime(series.index, utc=True, format="ISO8601")
    except (ValueError, TypeError) as error:
        raise ComponentInputValidationException(
            "The index of the series cannot be interpreted as timestamps:\n" + str(error),
            invalid_component_inputs=["series"],
        ) from error

    singletsframe = pd.DataFrame(
        {"timestamp": timestamps, value_column_name: series.to_numpy()}
    ).sort_values("timestamp")
    singletsframe = singletsframe.reset_index(drop=True)

    attrs = copy.deepcopy(series.attrs) if series.attrs else {}
    identify_single_metric(attrs, series.name)
    if value_column_name != "value":
        rename_value_dimension(attrs, "value", value_column_name)
    singletsframe.attrs = attrs

    return {"singletsframe": singletsframe}


# Testing
try:
    import pytest
except ImportError:
    pass
else:
    from hetdesrun.models.metadata_conventions import check_metadata_conventions

    @pytest.fixture
    def series():
        series = pd.Series(
            [5.7, 3.1],
            index=pd.to_datetime(["2019-08-01T15:45:36.000Z", "2019-08-01T15:42:36.000Z"]),
            name="abc.temp",
        )
        series.attrs = {"dataset_metadata": {"metric_key": "external_id"}}
        return series

    def test_conversion_sorts_and_names_columns(series):
        singletsframe = main(series=series)["singletsframe"]

        assert list(singletsframe.columns) == ["timestamp", "value"]  # noqa: S101
        assert list(singletsframe["value"]) == [3.1, 5.7]  # noqa: S101
        assert isinstance(singletsframe["timestamp"].dtype, pd.DatetimeTZDtype)  # noqa: S101
        assert str(singletsframe["timestamp"].dt.tz) == "UTC"  # noqa: S101

    def test_series_name_becomes_single_metric(series):
        singletsframe = main(series=series)["singletsframe"]

        assert singletsframe.attrs["dataset_metadata"]["single_metric"] == "abc.temp"  # noqa: S101
        assert singletsframe.attrs["dataset_metadata"]["metric_key"] == "external_id"  # noqa: S101
        # input attrs must not be modified
        assert "single_metric" not in series.attrs["dataset_metadata"]  # noqa: S101

    def test_existing_single_metric_is_kept(series):
        series.attrs["dataset_metadata"]["single_metric"] = "already.set"

        singletsframe = main(series=series)["singletsframe"]

        assert singletsframe.attrs["dataset_metadata"]["single_metric"] == "already.set"  # noqa: S101

    def test_custom_value_column_name(series):
        singletsframe = main(series=series, value_column_name="temperature")["singletsframe"]

        assert list(singletsframe.columns) == ["timestamp", "temperature"]  # noqa: S101

    @pytest.fixture
    def series_metadata():
        # following the metadata conventions for a SERIES
        return {
            "dataset_metadata": {
                "metric_key": "id",
                "single_metric": "abc.temp",
                "queried_metrics": ["abc.temp"],
                "ref_interval_start_timestamp": "2019-08-01T15:00:00Z",
                "ref_interval_end_timestamp": "2019-08-01T16:00:00Z",
                "ref_interval_type": "closed",
            },
            "metrics": [
                {
                    "id": "abc.temp",
                    "name": "Temperature",
                    "value_dimensions": [
                        {"column": "value", "unit": "°C", "measurement": "temperature"}
                    ],
                }
            ],
            "value_dimensions_shared": [{"column": "value", "description": "Measured"}],
        }

    @pytest.mark.parametrize("value_column_name", ["value", "temperature"])
    def test_metadata_follows_conventions(series, series_metadata, value_column_name):
        series.attrs = series_metadata
        assert check_metadata_conventions(series) == []  # noqa: S101

        singletsframe = main(series=series, value_column_name=value_column_name)["singletsframe"]

        assert check_metadata_conventions(singletsframe, "SINGLETSFRAME") == []  # noqa: S101
        value_dimension = singletsframe.attrs["metrics"][0]["value_dimensions"][0]
        assert value_dimension["column"] == value_column_name  # noqa: S101
        assert singletsframe.attrs["value_dimensions_shared"][0]["column"] == (  # noqa: S101
            value_column_name
        )
        # input attrs must not be modified
        assert series.attrs == series_metadata  # noqa: S101

    @pytest.mark.parametrize("metric_key", ["id", "external_id"])
    def test_single_metric_of_metadata_is_preferred_to_series_name(
        series, series_metadata, metric_key
    ):
        series_metadata["metrics"][0]["external_id"] = "abc.temp.external"
        series_metadata["dataset_metadata"]["metric_key"] = metric_key
        del series_metadata["dataset_metadata"]["single_metric"]
        series_metadata["dataset_metadata"]["queried_metrics"] = []
        series.attrs = series_metadata
        expected_single_metric = series_metadata["metrics"][0][metric_key]

        singletsframe = main(series=series)["singletsframe"]

        assert check_metadata_conventions(singletsframe, "SINGLETSFRAME") == []  # noqa: S101
        dataset_metadata = singletsframe.attrs["dataset_metadata"]
        assert dataset_metadata["single_metric"] == expected_single_metric  # noqa: S101
        assert dataset_metadata["queried_metrics"] == [expected_single_metric]  # noqa: S101
        assert singletsframe.attrs["metrics"] == series_metadata["metrics"]  # noqa: S101
        # input attrs must not be modified
        assert "single_metric" not in series.attrs["dataset_metadata"]  # noqa: S101

    def test_series_name_is_set_in_metric_without_identifying_field(series, series_metadata):
        del series_metadata["dataset_metadata"]["single_metric"]
        del series_metadata["dataset_metadata"]["queried_metrics"]
        del series_metadata["metrics"][0]["id"]
        series.attrs = series_metadata

        singletsframe = main(series=series)["singletsframe"]

        assert check_metadata_conventions(singletsframe, "SINGLETSFRAME") == []  # noqa: S101
        assert singletsframe.attrs["dataset_metadata"]["single_metric"] == "abc.temp"  # noqa: S101
        assert singletsframe.attrs["dataset_metadata"]["queried_metrics"] == [  # noqa: S101
            "abc.temp"
        ]
        assert singletsframe.attrs["metrics"][0]["id"] == "abc.temp"  # noqa: S101

    def test_series_name_does_not_replace_identifying_field(series, series_metadata):
        del series_metadata["dataset_metadata"]["single_metric"]
        # no string, so the metric cannot be identified by it
        series_metadata["metrics"][0]["id"] = 7
        series.attrs = series_metadata

        singletsframe = main(series=series)["singletsframe"]

        assert singletsframe.attrs["dataset_metadata"]["metric_key"] == "metric"  # noqa: S101
        assert singletsframe.attrs["dataset_metadata"]["single_metric"] == "abc.temp"  # noqa: S101
        assert singletsframe.attrs["metrics"][0]["metric"] == "abc.temp"  # noqa: S101
        assert singletsframe.attrs["metrics"][0]["id"] == 7  # noqa: S101

    def test_no_single_metric_for_several_metrics(series, series_metadata):
        del series_metadata["dataset_metadata"]["single_metric"]
        series_metadata["metrics"].append(series_metadata["metrics"][0] | {"id": "other"})
        series.attrs = series_metadata

        singletsframe = main(series=series)["singletsframe"]

        assert "single_metric" not in singletsframe.attrs["dataset_metadata"]  # noqa: S101

    def test_invalid_value_column_name(series):
        with pytest.raises(ComponentInputValidationException):
            main(series=series, value_column_name="timestamp")

    def test_unparsable_index():
        series = pd.Series([1.0, 2.0], index=["not a timestamp", "neither is this"])

        with pytest.raises(ComponentInputValidationException):
            main(series=series)

    def test_non_iso_timestamps_raise():
        # would otherwise be parsed month first, i.e. as 8th of January
        series = pd.Series([1.0, 2.0], index=["01.08.2019 15:45", "02.08.2019 15:42"])

        with pytest.raises(ComponentInputValidationException):
            main(series=series)


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "series",
            "filters": {
                "value": '{\n    "2019-08-01T15:42:36.000Z": 5.7,\n    "2019-08-01T15:45:36.000Z": 3.1\n}'
            },
        },
        {
            "workflow_input_name": "value_column_name",
            "use_default_value": True,
            "filters": {"value": "value"},
        },
    ]
}
RELEASE_WIRING = {
    "input_wirings": [
        {
            "workflow_input_name": "series",
            "filters": {
                "value": '{\n    "2019-08-01T15:42:36.000Z": 5.7,\n    "2019-08-01T15:45:36.000Z": 3.1\n}'
            },
        },
        {
            "workflow_input_name": "value_column_name",
            "use_default_value": True,
            "filters": {"value": "value"},
        },
    ]
}

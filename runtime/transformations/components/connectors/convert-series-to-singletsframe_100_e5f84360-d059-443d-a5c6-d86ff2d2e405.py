"""Documentation for Convert Series to SingleTSFrame

# Convert Series to SingleTSFrame

## Description
Convert a Series into a SingleTSFrame.

## Inputs
* **series** (Pandas Series): The input Series must have an index that can be interpreted as timestamps. It is converted to UTC.
* **value_column_name** (String, optional): Name of the value column of the resulting SingleTSFrame. Default: "value".

## Outputs
* **singletsframe** (SingleTSFrame): The output SingleTSFrame constructed from the series, consisting of a "timestamp" column and one value column.

## Details
A SERIES and a SINGLETSFRAME both represent a single timeseries. The difference is that a SERIES is one-dimensional and carries its timestamps in the index, while a SINGLETSFRAME carries its timestamps in a "timestamp" column and can have arbitrarily many value dimensions. This component therefore moves the index into a "timestamp" column and the values into a single value column.

The attributes (`.attrs`) of the series are carried over unchanged, since the [metadata conventions](https://hetida.github.io/hetida-designer/user_guide/attached_metadata/) identify the single metric the same way for both types, namely via `dataset_metadata.single_metric`. If the series has a name and no `single_metric` is set in the metadata, the series name is used as `single_metric`.

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
        timestamps = pd.to_datetime(series.index, utc=True)
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
    if series.name is not None:
        dataset_metadata = attrs.setdefault("dataset_metadata", {})
        if isinstance(dataset_metadata, dict) and dataset_metadata.get("single_metric") is None:
            dataset_metadata["single_metric"] = str(series.name)
    singletsframe.attrs = attrs

    return {"singletsframe": singletsframe}


# Testing
try:
    import pytest
except ImportError:
    pass
else:

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

    def test_invalid_value_column_name(series):
        with pytest.raises(ComponentInputValidationException):
            main(series=series, value_column_name="timestamp")

    def test_unparsable_index():
        series = pd.Series([1.0, 2.0], index=["not a timestamp", "neither is this"])

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

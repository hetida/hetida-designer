"""Documentation for Convert DataFrame to SingleTSFrame

# Convert DataFrame to SingleTSFrame

## Description
Convert a DataFrame into a SingleTSFrame.

## Inputs
* **dataframe** (Pandas DataFrame): The input DataFrame. Either it has a column named "timestamp" or its index is used as timestamps. In both cases the timestamps are converted to UTC.

## Outputs
* **singletsframe** (SingleTSFrame): The output SingleTSFrame with a "timestamp" column and all remaining columns as value dimensions.

## Details
Every column of the DataFrame besides the timestamps becomes a value dimension of the resulting SingleTSFrame. In contrast to "Convert DataFrame to MultiTSFrame" the columns are *not* interpreted as metrics — all columns are understood as different value dimensions of one and the same timeseries.

The attributes (`.attrs`) are carried over unchanged. So the metadata of a SingleTSFrame converted into a DataFrame before, e.g. via "Convert SingleTSFrame to DataFrame", is kept. Metadata of other DataFrames does not necessarily follow the [metadata conventions](https://hetida.github.io/hetida-designer/user_guide/attached_metadata/) for a SINGLETSFRAME.

Raises a ComponentInputValidationException if the timestamps cannot be parsed or if the DataFrame has no value column at all.

## Examples
The json input of a typical call of this component is
```
{
    "dataframe": [
        {
            "timestamp": "2019-08-01T15:42:36.000Z",
            "value": 5.7,
            "state": "ok"
        },
        {
            "timestamp": "2019-08-01T15:48:36.000Z",
            "value": 3.1,
            "state": "suspicious"
        }
    ]
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
        "dataframe": {"data_type": "DATAFRAME"},
    },
    "outputs": {
        "singletsframe": {"data_type": "SINGLETSFRAME"},
    },
    "name": "Convert DataFrame to SingleTSFrame",
    "category": "Connectors",
    "description": "Convert a DataFrame into a SingleTSFrame",
    "version_tag": "1.0.0",
    "id": "13f13124-1f22-4e84-a203-5c52dfd2e096",
    "revision_group_id": "38fcb014-cefe-4655-b754-be26c93c036b",
    "state": "RELEASED",
    "released_timestamp": "2026-08-05T10:00:00+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, dataframe):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    if "timestamp" in dataframe.columns:
        raw_timestamps = dataframe["timestamp"]
        value_frame = dataframe.drop(columns=["timestamp"])
    else:
        raw_timestamps = dataframe.index
        value_frame = dataframe

    if len(value_frame.columns) == 0:
        raise ComponentInputValidationException(
            "A SingleTSFrame requires at least one value column, but the provided DataFrame"
            " has no column besides the timestamps.",
            invalid_component_inputs=["dataframe"],
        )

    try:
        timestamps = pd.to_datetime(pd.Series(list(raw_timestamps)), utc=True)
    except (ValueError, TypeError) as error:
        raise ComponentInputValidationException(
            "The timestamps of the DataFrame cannot be parsed:\n" + str(error),
            invalid_component_inputs=["dataframe"],
        ) from error

    singletsframe = value_frame.reset_index(drop=True)
    singletsframe.insert(0, "timestamp", timestamps)
    singletsframe = singletsframe.sort_values("timestamp").reset_index(drop=True)
    singletsframe.attrs = copy.deepcopy(dataframe.attrs) if dataframe.attrs else {}

    return {"singletsframe": singletsframe}


# Testing
try:
    import pytest
except ImportError:
    pass
else:
    from hetdesrun.models.metadata_conventions import check_metadata_conventions

    @pytest.fixture
    def dataframe_with_timestamp_column():
        return pd.DataFrame(
            {
                "timestamp": ["2019-08-01T15:45:36.000Z", "2019-08-01T15:42:36.000Z"],
                "value": [1.2, 1.0],
                "state": ["ok", "suspicious"],
            }
        )

    def test_timestamp_column_is_used(dataframe_with_timestamp_column):
        singletsframe = main(dataframe=dataframe_with_timestamp_column)["singletsframe"]

        assert list(singletsframe.columns) == ["timestamp", "value", "state"]  # noqa: S101
        assert list(singletsframe["value"]) == [1.0, 1.2]  # noqa: S101
        assert isinstance(singletsframe["timestamp"].dtype, pd.DatetimeTZDtype)  # noqa: S101
        assert str(singletsframe["timestamp"].dt.tz) == "UTC"  # noqa: S101

    def test_index_is_used_if_no_timestamp_column(dataframe_with_timestamp_column):
        dataframe = dataframe_with_timestamp_column.set_index("timestamp")

        singletsframe = main(dataframe=dataframe)["singletsframe"]

        assert list(singletsframe.columns) == ["timestamp", "value", "state"]  # noqa: S101
        assert list(singletsframe["value"]) == [1.0, 1.2]  # noqa: S101

    @pytest.mark.parametrize("timestamps_as_index", [False, True])
    def test_singletsframe_metadata_is_kept(dataframe_with_timestamp_column, timestamps_as_index):
        dataframe = (
            dataframe_with_timestamp_column.set_index("timestamp")
            if timestamps_as_index
            else dataframe_with_timestamp_column
        )
        # following the metadata conventions for a SINGLETSFRAME
        dataframe.attrs = {
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
                        {"column": "value", "unit": "°C", "measurement": "temperature"},
                        {"column": "state", "unit": None, "measurement": None},
                    ],
                }
            ],
        }

        singletsframe = main(dataframe=dataframe)["singletsframe"]

        assert singletsframe.attrs == dataframe.attrs  # noqa: S101
        assert check_metadata_conventions(singletsframe, "SINGLETSFRAME") == []  # noqa: S101

    def test_no_value_column_raises():
        dataframe = pd.DataFrame({"timestamp": ["2019-08-01T15:45:36.000Z"]})

        with pytest.raises(ComponentInputValidationException):
            main(dataframe=dataframe)

    def test_unparsable_timestamps_raise():
        dataframe = pd.DataFrame({"timestamp": ["not a timestamp"], "value": [1.0]})

        with pytest.raises(ComponentInputValidationException):
            main(dataframe=dataframe)


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "dataframe",
            "filters": {
                "value": '[\n    {\n        "timestamp": "2019-08-01T15:42:36.000Z",\n        "value": 5.7,\n        "state": "ok"\n    },\n    {\n        "timestamp": "2019-08-01T15:48:36.000Z",\n        "value": 3.1,\n        "state": "suspicious"\n    }\n]'
            },
        }
    ]
}
RELEASE_WIRING = {
    "input_wirings": [
        {
            "workflow_input_name": "dataframe",
            "filters": {
                "value": '[\n    {\n        "timestamp": "2019-08-01T15:42:36.000Z",\n        "value": 5.7,\n        "state": "ok"\n    },\n    {\n        "timestamp": "2019-08-01T15:48:36.000Z",\n        "value": 3.1,\n        "state": "suspicious"\n    }\n]'
            },
        }
    ]
}

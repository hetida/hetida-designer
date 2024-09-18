"""Create a time series with the provided fixed value for all gap timestamps.

# Fixed Replacement Value

## Description
Create a time series with the provided fixed value for all gap timestamps.

## Inputs
- **gap_timestamps** (Pandas Series):
    Either the values or the index must be of a datetime64 dtype.

- **replacement_value** (float):
    The value which is used for generating the new data points in replacement_value_series.

## Outputs
- **replacement_value_series** (Pandas Series):
    Series with index chosen from `gap_timestamps` and values identical to `replacement_value`.

## Details
- Raises `ComponentInputValidationException`:
    - If neither the values nor the index of `gap_timestamps` are of a datetime64 dtype.
    - If both the values and the index of `gap_timestamps` are of a datetime64 dtype, but not
    identical.

## Examples
The index of `replacement_value_series` can be retrieved from the index of the input series.
Example input:
```
{
    "gap_timestamps": {
        "2020-01-01T01:15:27.000Z": 42.2,
        "2020-01-03T08:20:03.000Z": 18.7,
        "2020-01-03T08:20:04.000Z": 25.9
    },
    "replacement_value": 37.0
}
```
The index of `replacement_value_series` can also be retrieved from the values of the input series.
Example input:
```
{
    "gap_timestamps": {
        "1": "2020-01-01T01:15:27.000Z",
        "2": "2020-01-03T08:20:03.000Z",
        "3": "2020-01-03T08:20:04.000Z"
    },
    "replacement_value": 37.0
}
```
In both cases, the output is:
```
{
    "replacement_value_series": {
        "__hd_wrapped_data_object__":"SERIES",
        "__metadata__":{},
        "__data__":{
            "2020-01-01T01:15:27.000Z":37,
            "2020-01-03T08:20:03.000Z":37,
            "2020-01-03T08:20:04.000Z":37
        }
    }
}
```
"""

import pandas as pd

from hdutils import ComponentInputValidationException

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "gap_timestamps": {"data_type": "SERIES"},
        "replacement_value": {"data_type": "FLOAT"},
    },
    "outputs": {
        "replacement_value_series": {"data_type": "SERIES"},
    },
    "name": "Fixed Replacement Value",
    "category": "Data Quality",
    "description": "Create a timeseries with the provided fixed value for all gap timestamps.",
    "version_tag": "1.0.0",
    "id": "82024fd1-b1a0-409d-a337-1db4330aa268",
    "revision_group_id": "2f66114c-2df9-4a03-b93e-60dc908e9cf4",
    "state": "RELEASED",
    "released_timestamp": "2023-11-23T16:20:56.654832+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, gap_timestamps, replacement_value):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    """Create a time series with the provided fixed value for all gap timestamps.

    Checks, if `gap_timestamps.index` or `gap_timestamps.to_numpy()` contain non conflicting
    DateTimeIndex like data. Returns a series of data points with index chosen from
    `gap_timestamps` and values identical to the replacement_value.
    """

    index_of_expected_dtype = pd.api.types.is_datetime64_any_dtype(gap_timestamps.index.dtype)
    values_of_expected_dtype = pd.api.types.is_datetime64_any_dtype(gap_timestamps.dtype)

    if not index_of_expected_dtype and not values_of_expected_dtype:
        raise ComponentInputValidationException(
            "No index or data of dtype datetime64 was found.",
            error_code=422,
            invalid_component_inputs=["gap_timestamps"],
        )

    if (
        index_of_expected_dtype
        and values_of_expected_dtype
        and not (gap_timestamps.index.to_numpy() == gap_timestamps.to_numpy()).all()
    ):
        raise ComponentInputValidationException(
            "Found conflicting timestamp data for replacement values.",
            error_code=422,
            invalid_component_inputs=["gap_timestamps"],
        )

    if not index_of_expected_dtype:
        return_series_index = gap_timestamps.to_numpy()
    else:
        return_series_index = gap_timestamps.index

    return {
        "replacement_value_series": pd.Series(data=replacement_value, index=return_series_index)
    }


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "gap_timestamps",
            "filters": {
                "value": '{\n    "2020-01-01T01:15:27.000Z": 10.0,\n    "2020-01-02T16:20:00.000Z": 20.0,\n    "2020-01-03T08:20:04.000Z": 30.0\n}'
            },
        },
        {"workflow_input_name": "replacement_value", "filters": {"value": "37.0"}},
    ]
}
RELEASE_WIRING = {
    "input_wirings": [
        {
            "workflow_input_name": "gap_timestamps",
            "filters": {
                "value": '{\n    "2020-01-01T01:15:27.000Z": 10.0,\n    "2020-01-02T16:20:00.000Z": 20.0,\n    "2020-01-03T08:20:04.000Z": 30.0\n}'
            },
        },
        {"workflow_input_name": "replacement_value", "filters": {"value": "37.0"}},
    ]
}

"""Check if the data points of the series lie within the value ranges.

# Value Range Check

## Description
For each data point of the series, it is checked for all value ranges whether it lies within them.

## Inputs
- **timeseries_data** (Pandas Series):
    Series to perform the value range check for. Expects values to be of dtype float or int.

- **value_range_dict** (dict):
    Dictionary of value ranges to check. Expected input shape is:
```
        {
           "value_range_name_1": {
                "min_value": float,
                "min_value_inclusive": bool,
                "max_value": float,
                "max_value_inclusive": bool
            },
            ...
        }
```
    The names of the value ranges must neither be "_violates_any", "_violates_all" or "_timestamp"
    nor end with "_IS_ABOVE" or "_IS_BELOW".

## Outputs
- **is_included_frame** (Pandas DataFrame):
    Data frame with a boolean table. Column names are the range names taken from
    `value_range_dict`. For each range name, there are two additional columns with names
    "[range name]_IS_ABOVE" and "[range name]_IS_BELOW". Entries show whether the condition of
    the column are fulfilled by the value corresponding to the index of the row.

## Details
- Raises `ComponentInputValidationException`:
    - If timeseries_data.dtype is neither int nor float
    - If both values of a value range are inclusive and min_value > max_value
    - If at least one value of a value range is not inclusive and min_value >= max_value
    - If the input dictionary doesn't match input of ValueRange constructor
    - If at least one name of a value range ends with "_IS_BELOW" or "_IS_ABOVE"
    - If at least one name of a value range is "_violates_all", "_violates_any", or "_timestamp"

## Examples

Expected json input is of shape:
```
{
    "timeseries_data": {
        "2020-01-01T01:15:27.000Z": 10.0,
        "2020-01-02T16:20:00.000Z": 20.0,
        "2020-01-03T08:20:04.000Z": 30.0
    },
    "value_range_dict": {
        "[10,20]": {
            "min_value": 10.0,
            "max_value": 20.0,
            "min_value_inclusive": true,
            "max_value_inclusive": true
            },
        "(20,30)": {
            "min_value": 20.0,
            "max_value": 30.0,
            "min_value_inclusive": false,
            "max_value_inclusive": false
            }
    }
}
```
Expected output of the above call is:
```
{
    "is_included_frame": {
        "__hd_wrapped_data_object__":"DATAFRAME",
        "__metadata__":{},"
        __data__":{
            "[10,20]":{
                "2020-01-01T01:15:27.000Z":true,
                "2020-01-02T16:20:00.000Z":true,
                "2020-01-03T08:20:04.000Z":false
            },
            "(20,30)":{
                "2020-01-01T01:15:27.000Z":false,
                "2020-01-02T16:20:00.000Z":false,
                "2020-01-03T08:20:04.000Z":false
            },
            "_violates_all":{
                "2020-01-01T01:15:27.000Z":false,
                "2020-01-02T16:20:00.000Z":false,
                "2020-01-03T08:20:04.000Z":true
            },
            "_violates_any":{
                "2020-01-01T01:15:27.000Z":true,
                "2020-01-02T16:20:00.000Z":true,
                "2020-01-03T08:20:04.000Z":true
            },
            "[10,20]_IS_BELOW":{
                "2020-01-01T01:15:27.000Z":false,
                "2020-01-02T16:20:00.000Z":false,
                "2020-01-03T08:20:04.000Z":false
            },
            "[10,20]_IS_ABOVE":{
                "2020-01-01T01:15:27.000Z":false,
                "2020-01-02T16:20:00.000Z":false,
                "2020-01-03T08:20:04.000Z":true
            },
            "(20,30)_IS_BELOW":{
                "2020-01-01T01:15:27.000Z":true,
                "2020-01-02T16:20:00.000Z":true,
                "2020-01-03T08:20:04.000Z":false
            },
            "(20,30)_IS_ABOVE":{
                "2020-01-01T01:15:27.000Z":false,
                "2020-01-02T16:20:00.000Z":false,
                "2020-01-03T08:20:04.000Z":true
            },
            "_timestamp":{
                "2020-01-01T01:15:27.000Z":"2020-01-01T01:15:27.000Z",
                "2020-01-02T16:20:00.000Z":"2020-01-02T16:20:00.000Z",
                "2020-01-03T08:20:04.000Z":"2020-01-03T08:20:04.000Z"
            }
        }
    }
}
```
"""

import pandas as pd
from pydantic import BaseModel, ValidationError, root_validator

from hdutils import ComponentInputValidationException


class ValueRange(BaseModel):
    min_value: float
    min_value_inclusive: bool = True
    max_value: float
    max_value_inclusive: bool = True

    @root_validator(skip_on_failure=True)
    def verify_value_ranges(cls, values: dict) -> dict:
        try:
            min_value = values["min_value"]
            min_value_inclusive = values["min_value_inclusive"]
            max_value = values["max_value"]
            max_value_inclusive = values["max_value_inclusive"]
        except KeyError as error:
            raise ValueError("") from error
        if max_value < min_value:
            raise ValueError(
                "To be valid, a value range must be non-empty, i.e. min_value may not "
                "be bigger than max_value."
            )

        if (min_value_inclusive is False or max_value_inclusive is False) and not (
            min_value < max_value
        ):
            raise ValueError(
                "To be valid, a value range must be non-empty, i.e min_value must "
                "be smaller than max_value."
            )
        return values


def check_value_ranges(
    timeseries_data: pd.Series, value_range_dict: dict[str, ValueRange]
) -> pd.DataFrame:
    """Checks if the values of the `timeseries_data` are in given value ranges.

    Parameters:
    -----------
    timeseries_data:
        Expects float or int values. Index will be used for output data frame.

    value_range_dict:
       Contains value ranges that are used for checking the values in `timeseries_data`.
    """

    is_included_default_values = {range_name: False for range_name in value_range_dict}
    is_included_default_values["_violates_all"] = True
    is_included_default_values["_violates_any"] = False

    is_included_frame = pd.DataFrame(data=is_included_default_values, index=timeseries_data.index)

    for range_name, value_range in value_range_dict.items():
        if value_range.min_value_inclusive is True:
            is_included_frame[range_name + "_IS_BELOW"] = timeseries_data < value_range.min_value
        else:
            is_included_frame[range_name + "_IS_BELOW"] = timeseries_data <= value_range.min_value

        if value_range.max_value_inclusive is True:
            is_included_frame[range_name + "_IS_ABOVE"] = timeseries_data > value_range.max_value
        else:
            is_included_frame[range_name + "_IS_ABOVE"] = timeseries_data >= value_range.max_value

        is_included_frame[range_name] = (~is_included_frame[range_name + "_IS_BELOW"]) & (
            ~is_included_frame[range_name + "_IS_ABOVE"]
        )

    is_included_frame["_violates_all"] = (~is_included_frame[list(value_range_dict.keys())]).all(
        axis=1
    )
    is_included_frame["_violates_any"] = (~is_included_frame[list(value_range_dict.keys())]).any(
        axis=1
    )

    is_included_frame["_timestamp"] = is_included_frame.index

    return is_included_frame


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "timeseries_data": {"data_type": "SERIES"},
        "value_range_dict": {"data_type": "ANY"},
    },
    "outputs": {
        "is_included_frame": {"data_type": "DATAFRAME"},
    },
    "name": "Value Range Check",
    "category": "Data Quality",
    "description": "For each data point of the series, it is checked for all value ranges whether it lies within them.",  # noqa: E501
    "version_tag": "1.0.0",
    "id": "3cf8e12d-2fea-40d9-bc4b-015bddf66828",
    "revision_group_id": "83dabdfc-2d34-4e72-8010-4d61db8a9d6a",
    "state": "RELEASED",
    "released_timestamp": "2023-11-23T16:20:56.654831+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, timeseries_data, value_range_dict):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.

    if timeseries_data.dtype not in [int, float]:
        raise ComponentInputValidationException(
            "To determine whether time series entries are in a value range,"
            f" their dtype must be float or int, while it is {timeseries_data.dtype}",
            error_code=422,
            invalid_component_inputs=["timeseries_data"],
        )

    timeseries_data_no_nan = timeseries_data.dropna()

    error_dict = {}

    value_ranges: dict[str, ValueRange] = {}

    for range_name, value_range in value_range_dict.items():
        if range_name.endswith(("_IS_BELOW", "_IS_ABOVE")):
            error_dict[range_name] = "Range names must not end with '_IS_BELOW' or '_IS_ABOVE'! "
        if range_name in ("_violates_all", "_violates_any", "_timestamp"):
            error_dict[range_name] = (
                "Range names must not be '_violates_all', '_violates_any', or" " '_timestamp'!"
            )
        try:
            value_ranges[range_name] = ValueRange(**value_range)
        except (ValueError, ValidationError) as error:
            error_dict[range_name] = str(error)

    if len(error_dict) != 0:
        raise ComponentInputValidationException(
            "There were input validation errors for the value_range_dict:\n"
            + "\n".join(
                range_name + ": " + error_string for range_name, error_string in error_dict.items()
            ),
            error_code=422,
            invalid_component_inputs=["value_range_dict"],
        )

    return {"is_included_frame": check_value_ranges(timeseries_data_no_nan, value_ranges)}


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "timeseries_data",
            "filters": {
                "value": '{\n    "2020-01-01T01:15:27.000Z": 10.0,\n    "2020-01-02T16:20:00.000Z": 20.0,\n    "2020-01-03T08:20:04.000Z": 30.0\n}'
            },
        },
        {
            "workflow_input_name": "value_range_dict",
            "filters": {
                "value": '{\n    "[10,20]": {\n        "min_value": 10.0,\n        "max_value": 20.0,\n        "min_value_inclusive": true,\n        "max_value_inclusive": true\n    },\n    "(20,30)": {\n        "min_value": 20.0,\n        "max_value": 30.0,\n        "min_value_inclusive": false,\n        "max_value_inclusive": false\n    }\n}'
            },
        },
    ]
}
RELEASE_WIRING = {
    "input_wirings": [
        {
            "workflow_input_name": "timeseries_data",
            "filters": {
                "value": '{\n    "2020-01-01T01:15:27.000Z": 10.0,\n    "2020-01-02T16:20:00.000Z": 20.0,\n    "2020-01-03T08:20:04.000Z": 30.0\n}'
            },
        },
        {
            "workflow_input_name": "value_range_dict",
            "filters": {
                "value": '{\n    "[10,20]": {\n        "min_value": 10.0,\n        "max_value": 20.0,\n        "min_value_inclusive": true,\n        "max_value_inclusive": true\n    },\n    "(20,30)": {\n        "min_value": 20.0,\n        "max_value": 30.0,\n        "min_value_inclusive": false,\n        "max_value_inclusive": false\n    }\n}'
            },
        },
    ]
}

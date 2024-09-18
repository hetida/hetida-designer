"""Documentation for component "Correct Time Intervals With Fixed Values"

# Correct Time Intervals With Fixed Values

## Description
Correct all data points in provided time intervals from a time series with a correction value for
each time interval.

## Inputs
- **series** (Pandas Series):
    Expects DateTimeIndex. Expects dtype to be float or int.

- **list_of_time_intervals** (Any):
    List of time intervals, that specify when each interval begins and ends, and which correction
    value to use. An example of a JSON input for a time interval is:
    ```
    [
        {
            "start": "2020-01-01T01:15:27.000Z",
            "end": "2020-01-01T01:15:27.000Z",
            "start_inclusive": true,
            "end_inclusive": true,
            "correction_value": 37.0
        }
    ]
    ```
    The `start` and `end` attributes set the boundary timestamps for the respective time interval.
    The corresponding boolean attributes `start_inclusive` and `end_inclusive` define whether the
    respective boundary is inclusive or not. These attributes are optional. Their values in the
    example represent the default values. All entries of `series` that lie within the time interval
    are replaced by the `correction_value`.

## Outputs
- **corrected** (Pandas Series):
    The Series with corrected values.

## Details
If a data point lies within multiple time intervals, it will be changed to the `correction_value`
of the last time interval in `time_interval_dict`.

- Raises `ComponentInputValidationException`:
    - If the index of `series` is not a DateTimeIndex.
    - If `list_of_time_intervals` contains any invalid entries.

## Examples

An example JSON input for a call of this component is:
```
{
    "series": {
        "2020-01-01T01:15:27.000Z": 42.2,
        "2020-01-03T08:20:03.000Z": 18.7,
        "2020-01-03T08:20:04.000Z": 25.9
    },
    "list_of_time_intervals": [
        {
            "start": "2020-01-01T01:15:27.000Z",
            "end": "2020-01-01T01:15:27.000Z",
            "start_inclusive": true,
            "end_inclusive": true,
            "correction_value": 37
        },
        {
            "start": "2020-01-03T08:20:02.000Z",
            "end": "2020-01-03T08:20:04.000Z",
            "start_inclusive": false,
            "end_inclusive": false,
            "correction_value": 42.0
        }
    ]
}
```
The expected output of the above call is:
```
{
    "corrected":{
        "__hd_wrapped_data_object__":"SERIES",
        "__metadata__":{},
        "__data__":{
            "2020-01-01T01:15:27.000Z":37.0,
            "2020-01-03T08:20:03.000Z":42.0,
            "2020-01-03T08:20:04.000Z":25.9
        }
    }
}
```
"""

import pandas as pd
from pydantic import BaseModel, ValidationError, root_validator

from hdutils import ComponentInputValidationException


class TimeInterval(BaseModel):
    start: str
    end: str
    correction_value: float
    start_inclusive: bool = True
    end_inclusive: bool = True

    @root_validator(skip_on_failure=True)
    def verify_value_ranges(cls, values: dict) -> dict:
        start = values["start"]
        start_inclusive = values["start_inclusive"]
        end = values["end"]
        end_inclusive = values["end_inclusive"]
        if end < start:
            raise ValueError(
                "To be valid, a time interval must be non-empty, i.e. the start timestamp "
                "may not be later than the end timestamp."
            )
        if (start_inclusive is False or end_inclusive is False) and (start == end):
            raise ValueError(
                "To be valid, a time interval must be non-empty, i.e the start timestamp must be "
                "not equal to the end timestamp, when at least one boundary is not inclusive."
            )
        return values


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "series": {"data_type": "SERIES"},
        "list_of_time_intervals": {"data_type": "ANY"},
    },
    "outputs": {
        "corrected": {"data_type": "SERIES"},
    },
    "name": "Correct Time Intervals With Fixed Values",
    "category": "Filters",
    "description": "Correct all data points in provided time intervals from a time series with a correction value for each time interval.",  # noqa: E501
    "version_tag": "1.0.0",
    "id": "504a01aa-12a2-472b-995c-0676af66b07c",
    "revision_group_id": "92d2ded2-c6ca-42a1-a15b-a8e9cf6ca635",
    "state": "RELEASED",
    "released_timestamp": "2023-11-09T08:04:31.787859+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, series, list_of_time_intervals):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.

    if not isinstance(series.index, pd.DatetimeIndex):
        raise ComponentInputValidationException(
            "The index of the provided series does not have the datatype DatetimeIndex.",
            error_code="not a time-series like object",
            invalid_component_inputs=["series"],
        )

    timestamps = series.index

    in_intervals = pd.Series(False, index=timestamps)

    corrected = series.copy(deep=True)

    error_dict = {}

    time_intervals: list[TimeInterval] = []

    for count, interval in enumerate(list_of_time_intervals):
        try:
            time_intervals.append(TimeInterval(**interval))
        except (ValueError, ValidationError) as error:
            error_dict[count] = str(error)

    if len(error_dict) != 0:
        raise ComponentInputValidationException(
            "There were input validation errors for the list_of_time_intervals:\n"
            + "\n".join(
                f"TimeInterval {interval_index}" + ": " + error_string
                for interval_index, error_string in error_dict.items()
            ),
            error_code=422,
            invalid_component_inputs=["list_of_time_intervals"],
        )

    for interval in time_intervals:
        after_start = (
            timestamps >= interval.start
            if interval.start_inclusive is True
            else timestamps > interval.start
        )

        before_end = (
            timestamps <= interval.end
            if interval.end_inclusive is True
            else timestamps < interval.end
        )

        in_interval = pd.Series(after_start & before_end, index=timestamps)
        in_intervals = in_intervals | in_interval

        corrected[in_interval] = interval.correction_value

    return {"corrected": corrected}


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "series",
            "filters": {
                "value": '{\n    "2020-01-01T01:15:27.000Z": 42.2,\n    "2020-01-03T08:20:03.000Z": 18.7,\n    "2020-01-03T08:20:04.000Z": 25.9\n}'
            },
        },
        {
            "workflow_input_name": "list_of_time_intervals",
            "filters": {
                "value": '[\n    {\n        "start": "2020-01-01T01:15:27.000Z",\n        "end": "2020-01-01T01:15:27.000Z",\n        "start_inclusive": true,\n        "end_inclusive": true,\n        "correction_value": 37\n    },\n    {\n        "start": "2020-01-03T08:20:02.000Z",\n        "end": "2020-01-03T08:20:04.000Z",\n        "start_inclusive": false,\n        "end_inclusive": false,\n        "correction_value": 42.0\n    }\n]'
            },
        },
    ]
}
RELEASE_WIRING = {
    "input_wirings": [
        {
            "workflow_input_name": "series",
            "filters": {
                "value": '{\n    "2020-01-01T01:15:27.000Z": 42.2,\n    "2020-01-03T08:20:03.000Z": 18.7,\n    "2020-01-03T08:20:04.000Z": 25.9\n}'
            },
        },
        {
            "workflow_input_name": "list_of_time_intervals",
            "filters": {
                "value": '[\n    {\n        "start": "2020-01-01T01:15:27.000Z",\n        "end": "2020-01-01T01:15:27.000Z",\n        "start_inclusive": true,\n        "end_inclusive": true,\n        "correction_value": 37\n    },\n    {\n        "start": "2020-01-03T08:20:02.000Z",\n        "end": "2020-01-03T08:20:04.000Z",\n        "start_inclusive": false,\n        "end_inclusive": false,\n        "correction_value": 42.0\n    }\n]'
            },
        },
    ]
}

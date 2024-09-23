"""Documentation for component "Select Time Intervals"

# Select Time Intervals

## Description
Select all data points in provided time intervals from a time series. Returns a filter series.

## Inputs

- **series** (Pandas Series):
    Expects DateTimeIndex.

- **list_of_time_intervals** (Any):
    List of time intervals, that specify when the respective interval begins and ends, and which
    correction value to use. An example of a JSON input for a time interval is:
    [
        {
            "start": "2020-01-01T01:15:27.000Z",
            "end": "2020-01-01T01:15:27.000Z",
            "start_inclusive": true,
            "end_inclusive": true
        }
    ]
    The `start` and `end` attributes set the boundary timestamps for the respective time interval.
    The corresponding boolean value `_inclusive` sets whether the respective boundary is inclusive
    or not. The two latter entries are optional, the example displays their default values.


## Outputs
- **filter_series** (Pandas Series):
    Filter series generated from `series`.
    Entries are representing whether the value corresponding to the timestamp of the index is in any
    of the value intervals provided in the `list_of_time_intervals`.

## Details

- Raises 'ComponentInputValidationException`:
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
            "end_inclusive": true
        },
        {
            "start": "2020-01-03T08:20:02.000Z",
            "end": "2020-01-03T08:20:04.000Z",
            "start_inclusive": false,
            "end_inclusive": false
        }
    ]
}
```
The expected output of the above call is:
```
{
    "filter_series":{
        "__hd_wrapped_data_object__":"SERIES",
        "__metadata__":{},
        "__data__":{
            "2020-01-01T01:15:27.000Z":true,
            "2020-01-03T08:20:03.000Z":true,
            "2020-01-03T08:20:04.000Z":false
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
        if (start_inclusive is False or end_inclusive is False) and not (start < end):
            raise ValueError(
                "To be valid, a time interval must be non-empty, i.e the start timestamp must be "
                "earlier than the end timestamp."
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
        "filter_series": {"data_type": "SERIES"},
    },
    "name": "Select Time Intervals",
    "category": "Filters",
    "description": "Select all data points in provided time intervals from a time series.",
    "version_tag": "1.0.0",
    "id": "994e8607-5eaa-43b1-b057-73d8d14e90dd",
    "revision_group_id": "ffb36ac0-e351-45f1-93cb-5f3f26e0da78",
    "state": "RELEASED",
    "released_timestamp": "2023-11-09T07:44:10.808744+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, series, list_of_time_intervals):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.

    if not isinstance(series.index, pd.DatetimeIndex):
        raise ComponentInputValidationException(
            "The index of the provided series does not have data type DateTimeIndex.",
            error_code=422,
            invalid_component_inputs=["series"],
        )

    timestamps = series.index
    error_dict = {}

    time_intervals: list[TimeInterval] = []

    for count, interval in enumerate(list_of_time_intervals):
        try:
            time_intervals.append(TimeInterval(**interval))
        except (ValueError, ValidationError) as error:
            error_dict[f"TimeInterval {count}"] = str(error)

    if len(error_dict) != 0:
        raise ComponentInputValidationException(
            "There were input validation errors for the list_of_time_intervals:\n"
            + "\n".join(
                interval_name + ": " + error_string
                for interval_name, error_string in error_dict.items()
            ),
            error_code=422,
            invalid_component_inputs=["list_of_time_intervals"],
        )

    in_intervals = pd.Series(False, index=timestamps)

    for interval in time_intervals:
        start_inclusive = interval.start_inclusive
        end_inclusive = interval.end_inclusive

        above_start = (
            timestamps >= interval.start if start_inclusive else timestamps > interval.start
        )

        below_end = timestamps <= interval.end if end_inclusive else timestamps < interval.end

        in_interval = pd.Series(above_start & below_end, index=timestamps)
        in_intervals = in_intervals | in_interval

    return {"filter_series": in_intervals}


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
                "value": '[\n    {\n        "start": "2020-01-01T01:15:27.000Z",\n        "end": "2020-01-01T01:15:27.000Z",\n        "start_inclusive": true,\n        "end_inclusive": true\n    },\n    {\n        "start": "2020-01-03T08:20:02.000Z",\n        "end": "2020-01-03T08:20:04.000Z",\n        "start_inclusive": false,\n        "end_inclusive": false\n    }\n]'
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
                "value": '[\n    {\n        "start": "2020-01-01T01:15:27.000Z",\n        "end": "2020-01-01T01:15:27.000Z",\n        "start_inclusive": true,\n        "end_inclusive": true\n    },\n    {\n        "start": "2020-01-03T08:20:02.000Z",\n        "end": "2020-01-03T08:20:04.000Z",\n        "start_inclusive": false,\n        "end_inclusive": false\n    }\n]'
            },
        },
    ]
}

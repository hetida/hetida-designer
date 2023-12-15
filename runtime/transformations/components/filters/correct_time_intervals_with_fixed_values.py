"""Documentation for component "Correct time intervals with fixed values"

# Correct time intervals with fixed values

## Description
Correct all data points in provided time intervals from a time series with a correction value for
each time interval.

## Inputs
- **series** (Pandas Series):
    Expects DateTimeIndex. Expects dtype to be float or int.

- **list_of_time_intervals** (dict):
    List of time intervals, that specify when each interval begins and ends, and which correction
    value to use. Supported dict properties:
    - **start**: Timestamp
    - **end**: Timestamp
    - **correction_value**: Float
    - *(optional)* **start_inclusive**: Boolean
    - *(optional)* **end_inclusive**: Boolean

## Outputs
- **corrected** (Pandas Series):
    The Series with corrected values.

## Details
- If a data point lies within multiple time intervals, it will be changed to the `correction_value`
of the last time interval in `time_interval_dict`.
- Raises `ComponentInputValidationException`:
    - If the index of `series` is not a DateTimeIndex.
    - If `series` does not contain any valid entries.
    - If `list_of_time_intervals` contains any invalid entries.

## Examples

Example json input for a call of this component is:
```
{   "series": {
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
Output of the above call is:
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

from hetdesrun.runtime.exceptions import ComponentInputValidationException


class TimeInterval(BaseModel):
    start: str
    end: str
    correction_value: float
    start_inclusive: bool = True
    end_inclusive: bool = True

    @root_validator()
    def verify_value_ranges(cls, values: dict) -> dict:
        try:
            start = values["start"]
            start_inclusive = values["start_inclusive"]
            end = values["end"]
            end_inclusive = values["end_inclusive"]
            correction_value = values["correction_value"]
        except KeyError as error:
            raise ValueError("") from error
        if pd.isna(correction_value) is True:
            raise ValueError(
                "The correction_value must be a valid number, "
                f"while it is: {correction_value}"
            )
        if end < start:
            raise ValueError(
                "To be valid, a time interval must be non-empty, i.e. the start timestamp "
                "may not be bigger than the end timestamp."
            )

        if (start_inclusive is False or end_inclusive is False) and not (start < end):
            raise ValueError(
                "To be valid, a time interval must be non-empty, i.e the start timestamp must be "
                "smaller than the end timestamp."
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
    "name": "Correct time intervals with fixed values",
    "category": "Filters",
    "description": (
        "Correct all data points in provided time intervals from a time series with a "
        "correction value for each time interval."
    ),
    "version_tag": "0.1.0",
    "id": "504a01aa-12a2-472b-995c-0676af66b07c",
    "revision_group_id": "92d2ded2-c6ca-42a1-a15b-a8e9cf6ca635",
    "state": "RELEASED",
    "released_timestamp": "2023-11-09T08:04:31.787859+00:00",
    "disabled_timestamp": None,
}


def main(*, series: pd.Series, list_of_time_intervals):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.

    series_or_multitsframe_no_nan = series.dropna()
    if series_or_multitsframe_no_nan.empty is True:
        raise ComponentInputValidationException(
            "To determine whether time series entries are in a value interval,"
            "the input series must not be empty.",
            error_code="not a time-series like object",
            invalid_component_inputs=["series"],
        )

    if isinstance(series_or_multitsframe_no_nan, pd.Series) and isinstance(
        series_or_multitsframe_no_nan.index, pd.DatetimeIndex
    ):
        timestamps = series_or_multitsframe_no_nan.index
    else:
        raise ComponentInputValidationException(
            "Could not find timestamps in provided object",
            error_code="not a time-series like object",
            invalid_component_inputs=["series"],
        )

    in_intervals = pd.Series(False, index=timestamps)

    corrected = series_or_multitsframe_no_nan.copy(deep=True)

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

    for interval in time_intervals:
        start_inclusive = interval.start_inclusive
        end_inclusive = interval.end_inclusive

        if start_inclusive is True:
            above_start = timestamps >= interval.start
        else:
            above_start = timestamps > interval.start

        below_end = (
            timestamps <= interval.end
            if end_inclusive is True
            else timestamps < interval.end
        )

        in_interval = pd.Series(above_start & below_end, index=timestamps)
        in_intervals = in_intervals | in_interval

        corrected[in_interval] = interval.correction_value

    return {"corrected": corrected}


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "series",
            "adapter_id": "direct_provisioning",
            "use_default_value": False,
            "filters": {
                "value": (
                    "{\n"
                    '    "2020-01-01T01:15:27.000Z": 42.2,\n'
                    '    "2020-01-03T08:20:03.000Z": 18.7,\n'
                    '    "2020-01-03T08:20:04.000Z": 25.9\n'
                    "}"
                )
            },
        },
        {
            "workflow_input_name": "list_of_time_intervals",
            "adapter_id": "direct_provisioning",
            "use_default_value": False,
            "filters": {
                "value": (
                    "[\n"
                    "    {\n"
                    '        "start": "2020-01-01T01:15:27.000Z",\n'
                    '        "end": "2020-01-01T01:15:27.000Z",\n'
                    '        "start_inclusive": true,\n'
                    '        "end_inclusive": true,\n'
                    '        "correction_value": 37\n'
                    "    },\n"
                    "    {\n"
                    '        "start": "2020-01-03T08:20:02.000Z",\n'
                    '        "end": "2020-01-03T08:20:04.000Z",\n'
                    '        "start_inclusive": false,\n'
                    '        "end_inclusive": false,\n'
                    '        "correction_value": 42.0\n'
                    "    }\n"
                    "]"
                )
            },
        },
    ],
}

"""Documentation for component "Gap Detection Intervals"

# Gap Detection Intervals

## Description

Detects gaps in the given timeseries that are larger than the expected frequency and returns a
DataFrame with information about the gaps.

## Inputs

- **timeseries** (Series):
  Expects index of data type DateTimeIndex.

- **interval_start_timestamp_str** (String, default value: null):
  Desired start date of the processing range. Expexcts ISO 8601 format.
  Alternatively, the **timeseries** can have an attribute "ref_interval_start_timestamp" (or "from")
  that will be used instead.
  If neither is defined, the processing range begins with the first data point in **timeseries**.
  The start date must not be later than the end date.

- **interval_end_timestamp_str** (String, default value: null):
  Desired end date of the processing range. Expexcts ISO 8601 format.
  Alternatively, the **timeseries** can have an attribute "ref_interval_end_timestamp" (or "to")
  that will be used instead.
  If neither is defined, the processing range ends with the last data point in **timeseries**.
  The start date must not be later than the end date.

- **auto_frequency_determination** (Boolean, default value: true):
  If true, the function will automatically determine the expected frequency based on the
  **timeseries** index and **expected_frequency_str** must not be set.
  If false, a *expected_frequency_str** must be set.
  If "ref_frequency" is contained in the attributes of **timeseries** this value will be used for
  the **expected_frequency_str** and **auto_frequency_determination** will be set to false.

- **auto_freq_end_timestamp_str** (String, default value: null):
  Only relevant when **auto_frequency_determination** is true.
  Expects a date string  between **interval_start_timestamp** and **interval_end_timestamp** inISO
  8601 format.
  The desired end date for the training data used to determine the step unit.
  If not specified, the entire
  processing range is used as training data.

- **percentile** (Float, default value: 0.5):
  Only relevant when **auto_frequency_determination** is true.
  Expects a positive value smaller than or equal to 1. The percentile value to use for automatic
  determination of the expected gapsize between two consecutive data points. The value should be
  selected according to the expected ratio of gaps to regular steps. I.e. if it is to be expected
  that more than 50% of the time steps are gaps, the value should be reduced; if fewer gaps are to
  be expected, the value can be adjusted upwards accordingly.

- **interpolation_method** (String, default value: nearest):
  Only relevant when **auto_frequency_determination** is true.
  Is used to determine the percentile value via the Pandas method `quantile`.
  Thus, must be one of "linear", "lower", "higher", "midpoint", "nearest".

- **min_amount_datapoints** (Int, default value: 11):
  Only relevant when **auto_frequency_determination** is True.
  Expects a positive value. Minimum amount of datapoints required. Effects the expectable precision
  of the automatically determined expected frequency.

- **expected_frequency_str** (String, default value: null):
  Must not be set if **auto_frequency_determination** is true, but must be set if
  **auto_frequency_determination** is false.
  The expected time step between consecutive timestamps in the time series. Must be a frequency
  string, e.g. "D" or "60s".

- **expected_frequency_factor** (Float, default value: 1.0):
  Expects a positive value. The value is used to define when a step between two consecutive data
  points is recognized as a gap. I.e. a value of 1.0 means that all steps larger than the
  specified or determined expected frequency are recognized as gaps, while a value of 2.0 means that
  intevals are only recognized as gaps if they are more than twice as large as the specified or
  determined expected frequency.

- **fill_value** (Any, default value: None):
  Is used as value if the start date (end date, respectively) is not contained in the **timeseries**
  and must be added.
  In this case, this value appears in the column "value_to_left" ("value_to_right", respectively)
  in the DataFrame output **gap_info** if there is a gap at the start or end of the **timeseries**.

## Outputs

- **gap_info** (DataFrame):
  A DataFrame containing the beginning and end timestamps of gaps larger than the specified or
  determined expected frequency.
  Columns are:
  - "start" (Timestamp): Start index of the gap.
  - "end" (Timestamp): End index of the gap.
  - "start_inclusive" (Boolean): Defines whether the start boundary is inclusive or not.
  - "end_inclusive" (Boolean): Defines whether the start boundary is inclusive or not.
  - "gap_size" (Timedelta): Size of the gap
  - "value_to_left" (Float/Int): If existing, last value before the gap, otherwise None
  - "value_to_right" (Float/Int): If existing, first value after the gap, otherwise None
  - "mean_left_right" (Float/Int): The mean value of the `value_to_left` and `value_to_right`.
    None, if at least one of these values is None.

## Details

If **interval_start_timestamp_str** (or **interval_end_timestamp_str**) is not zero, check whether
it is contained in the **time series** and add it if necessary, and remove all data points with an
earlier (or later) index in order to reduce the **time series** to the processing range.

To detect gaps, the time intervals between consecutive data points are determined.
If **auto_frequency_determination** is set to true, determine the expected frequency using the
**percentile**-th quantile of the time intervals in the training range.
The training range is determined by the **interval_start_timestamp_str** and the
**auto_freq_end_timestamp_str**.
If the latter is not defined, the full processing range is used as the training range.
If **auto_frequency_determination` is set to false, the expected_frequency is defined by the
**expected_frequency_str**.
If a time interval is greater than the product of the **expected_frequency_factor** and the expected
frequency, it is considered a gap.

For each gap, the output DataFrame **gap_info** contains the index of the preceding (following,
respectively) data point, the information as to whether the indices belong to the gap and, if
present, the corresponding values.
If both the value to the left and the value to the right of the gap are of the float or int data
type, the arithmetic mean of the two values is also provided.


## Examples

The input may be as minimalistic as just a timeseries:
```
{
    "timeseries": {
        "2020-01-01T01:16:00.000Z": 10.0,
        "2020-01-01T01:18:00.000Z": 10.0,
        "2020-01-01T01:19:00.000Z": 10.0,
        "2020-01-01T01:20:00.000Z": 10.0,
        "2020-01-01T01:22:00.000Z": 20.0,
        "2020-01-01T01:23:00.000Z": 20.0,
        "2020-01-01T01:25:00.000Z": 20.0,
        "2020-01-01T08:28:00.000Z": 20.0,
        "2020-01-01T08:30:00.000Z": 30.0,
        "2020-01-01T08:31:00.000Z": 30.0,
        "2020-01-01T16:34:00.000Z": 30.0
    }
}
```
The smallest intervals between subsequent timestamps is a minute, but because there are so many gaps
a percentile of 0.5 (corresponding to the median of the interval distribution) will result in a
2 minute interval as the lower limit for a gap and thus only identify the two larger gaps.
Such issues can be tackled by choosing a smaller **percentile** or **expected_frequency_factor**.
Thus the corresponding result is
```
{
    "__hd_wrapped_data_object__": "DATAFRAME",
    "__metadata__": {},
    "__data__": {
        "start": {
            "0": "2020-01-01T01:25:00.000Z",
            "1": "2020-01-01T08:31:00.000Z"
        },
        "end": {
            "0": "2020-01-01T08:28:00.000Z",
            "1": "2020-01-01T16:34:00.000Z"
        },
        "start_inclusive": {
            "0": false,
            "1": false
        },
        "end_inclusive": {
            "0": false,
            "1": false
        },
        "gap_size": {
            "0": "P0DT7H3M0S",
            "1": "P0DT8H3M0S"
        },
        "value_to_left": {
            "0": 20,
            "1": 30
        },
        "value_to_right": {
            "0": 20,
            "1": 30
        },
        "mean_left_right": {
            "0": 20,
            "1": 30
        }
    }
}
```

If the timeseres is enriched with metadata as in the following example JSON input a gap before the
first datapoint in the timeseries can be determined and the correct frequency is used
```
{
    "timeseries": {
        "__hd_wrapped_data_object__": "SERIES",
        "__metadata__": {
            "ref_interval_start_timestamp": "2020-01-01T00:16:00.000Z",
            "ref_interval_end_timestamp": "2020-01-01T16:34:00.000Z",
            "ref_frequency": "1min"
        },
        "__data__": {
            "2020-01-01T01:16:00.000Z": 10.0,
            "2020-01-01T01:18:00.000Z": 10.0,
            "2020-01-01T01:19:00.000Z": 10.0,
            "2020-01-01T01:20:00.000Z": 10.0,
            "2020-01-01T01:22:00.000Z": 20.0,
            "2020-01-01T01:23:00.000Z": 20.0,
            "2020-01-01T01:25:00.000Z": 20.0,
            "2020-01-01T08:28:00.000Z": 20.0,
            "2020-01-01T08:30:00.000Z": 30.0,
            "2020-01-01T08:31:00.000Z": 30.0,
            "2020-01-01T16:34:00.000Z": 30.0
        }
    }
}
```
The same result is obtained without using metadata by the JSON input
```
{
    "timeseries": {
        "2020-01-01T01:16:00.000Z": 10.0,
        "2020-01-01T01:18:00.000Z": 10.0,
        "2020-01-01T01:19:00.000Z": 10.0,
        "2020-01-01T01:20:00.000Z": 10.0,
        "2020-01-01T01:22:00.000Z": 20.0,
        "2020-01-01T01:23:00.000Z": 20.0,
        "2020-01-01T01:25:00.000Z": 20.0,
        "2020-01-01T08:28:00.000Z": 20.0,
        "2020-01-01T08:30:00.000Z": 30.0,
        "2020-01-01T08:31:00.000Z": 30.0,
        "2020-01-01T16:34:00.000Z": 30.0
    },
    "interval_start_timestamp_str": "2020-01-01T00:16:00.000Z",
    "interval_end_timestamp_str": "2020-01-01T16:34:00.000Z",
    "auto_frequency_determination": false,
    "expected_frequency": "1min"
}
```
The result of either of these inputs is then
```
{
    "__hd_wrapped_data_object__": "DATAFRAME",
    "__metadata__": {},
    "__data__": {
        "start": {
            "0": "2020-01-01T00:16:00.000Z",
            "1": "2020-01-01T01:16:00.000Z",
            "2": "2020-01-01T01:20:00.000Z",
            "3": "2020-01-01T01:23:00.000Z",
            "4": "2020-01-01T01:25:00.000Z",
            "5": "2020-01-01T08:28:00.000Z",
            "6": "2020-01-01T08:31:00.000Z"
        },
        "end": {
            "0": "2020-01-01T01:16:00.000Z",
            "1": "2020-01-01T01:18:00.000Z",
            "2": "2020-01-01T01:22:00.000Z",
            "3": "2020-01-01T01:25:00.000Z",
            "4": "2020-01-01T08:28:00.000Z",
            "5": "2020-01-01T08:30:00.000Z",
            "6": "2020-01-01T16:34:00.000Z"
        },
        "start_inclusive": {
            "0": false,
            "1": false,
            "2": false,
            "3": false,
            "4": false,
            "5": false,
            "6": false
        },
        "end_inclusive": {
            "0": false,
            "1": false,
            "2": false,
            "3": false,
            "4": false,
            "5": false,
            "6": false
        },
        "gap_size": {
            "0": "P0DT1H0M0S",
            "1": "P0DT0H2M0S",
            "2": "P0DT0H2M0S",
            "3": "P0DT0H2M0S",
            "4": "P0DT7H3M0S",
            "5": "P0DT0H2M0S",
            "6": "P0DT8H3M0S"
        },
        "value_to_left": {
            "0": null,
            "1": 10,
            "2": 10,
            "3": 20,
            "4": 20,
            "5": 20,
            "6": 30
        },
        "value_to_right": {
            "0": 10,
            "1": 10,
            "2": 20,
            "3": 20,
            "4": 20,
            "5": 30,
            "6": 30
        },
        "mean_left_right": {
            "0": null,
            "1": 10,
            "2": 15,
            "3": 20,
            "4": 20,
            "5": 25,
            "6": 30
        }
    }
}```
"""

from typing import Any

import numpy as np
import pandas as pd
from pydantic import BaseModel, validator

from hetdesrun.runtime.exceptions import ComponentInputValidationException


def timestamp_str_to_pd_timestamp(timestamp_str: str, input_name: str) -> pd.Timestamp:
    try:
        timestamp = pd.to_datetime(timestamp_str, utc=True)
    except ValueError as error:
        raise ComponentInputValidationException(
            str(error), error_code=422, invalid_component_inputs=[input_name]
        ) from error
    return timestamp


def freqstr2dateoffset(freqstr: str) -> pd.DateOffset:
    """Transform frequency string to Pandas DateOffset."""
    return pd.tseries.frequencies.to_offset(freqstr)


def freqstr2timedelta(freqstr: str, input_name: str) -> pd.Timedelta:
    """Transform frequency string to Pandas Timedelta."""
    try:
        return pd.to_timedelta(freqstr)
    except ValueError:
        try:
            return pd.to_timedelta(freqstr2dateoffset(freqstr))
        except TypeError as err:
            raise ComponentInputValidationException(
                f"The expected_frequency_str cannot be parsed as Pandas Timedelta: {str(err)}",
                error_code=422,
                invalid_component_inputs=[input_name],
            ) from err


class GapDetectionParameters(BaseModel):
    interval_start_timestamp_str: str | None
    interval_start_timestamp: pd.Timestamp | None = None
    interval_end_timestamp_str: str | None
    interval_end_timestamp: pd.Timestamp | None = None
    auto_frequency_determination: bool
    auto_freq_end_timestamp_str: str | None
    auto_freq_end_timestamp: pd.Timestamp | None = None
    percentile: float
    interpolation_method: str
    min_amount_datapoints: int
    expected_frequency_str: str | None
    expected_frequency: pd.Timedelta | None = None
    expected_frequency_factor: float
    fill_value: Any

    @validator("interval_start_timestamp", always=True)
    def get_interval_start_timestamp_from_interval_start_timestamp_str(
        cls, interval_start_timestamp: pd.Timestamp | None, values: dict  # noqa: ARG002
    ) -> pd.Timestamp | None:
        if values["interval_start_timestamp_str"] is None:
            return None

        return timestamp_str_to_pd_timestamp(
            values["interval_start_timestamp_str"], "interval_start_timestamp_str"
        )

    @validator("interval_end_timestamp", always=True)
    def get_interval_end_timestamp_from_interval_end_timestamp_str(
        cls, interval_end_timestamp: pd.Timestamp | None, values: dict  # noqa: ARG002
    ) -> pd.Timestamp | None:
        if values["interval_end_timestamp_str"] is None:
            return None

        return timestamp_str_to_pd_timestamp(
            values["interval_end_timestamp_str"], "interval_end_timestamp_str"
        )

    @validator("interval_end_timestamp")
    def verify_interval_end_timestamp_later_than_interval_start_timestamp(
        cls, interval_end_timestamp: pd.Timestamp | None, values: dict
    ) -> pd.Timestamp | None:
        interval_start_timestamp = values["interval_start_timestamp"]
        if (
            None not in (interval_start_timestamp, interval_end_timestamp)
            and interval_start_timestamp > interval_end_timestamp
        ):
            raise ComponentInputValidationException(
                "The value interval_start_timestamp must not be later "
                "than the interval_end_timestamp, while it is "
                f"{interval_start_timestamp} > {interval_end_timestamp}.",
                error_code=422,
                invalid_component_inputs=[
                    "interval_end_timestamp_str",
                    "interval_start_timestamp_str",
                ],
            )
        return interval_end_timestamp

    @validator("auto_freq_end_timestamp", always=True)
    def get_auto_freq_end_timestamp_from_auto_freq_end_timestamp_str(
        cls,
        auto_freq_end_timestamp: pd.Timestamp | None,  # noqa: ARG002
        values: dict,
    ) -> pd.Timestamp | None:
        if values["auto_freq_end_timestamp_str"] is None:
            return None

        return timestamp_str_to_pd_timestamp(
            values["auto_freq_end_timestamp_str"],
            "auto_freq_end_timestamp_str",
        )

    @validator("auto_freq_end_timestamp")
    def verify_auto_freq_end_timestamp_between_interval_start_and_end_timestamp(
        cls, auto_freq_end_timestamp: pd.Timestamp | None, values: dict
    ) -> pd.Timestamp | None:
        interval_start_timestamp = values["interval_start_timestamp"]
        interval_end_timestamp = values["interval_end_timestamp"]
        if auto_freq_end_timestamp is not None:
            if interval_start_timestamp > auto_freq_end_timestamp:
                raise ComponentInputValidationException(
                    "The value auto_freq_end_timestamp has to be "
                    "inbetween interval_start_timestamp and interval_end_timestamp, "
                    f"while it is {auto_freq_end_timestamp} < {interval_start_timestamp}.",
                    error_code=422,
                    invalid_component_inputs=["auto_freq_end_timestamp_str"],
                )
            if interval_end_timestamp < auto_freq_end_timestamp:
                raise ComponentInputValidationException(
                    "The value auto_freq_end_timestamp has to be "
                    "inbetween interval_start_timestamp and interval_end_timestamp, "
                    f"while it is {auto_freq_end_timestamp} > {interval_end_timestamp}.",
                    error_code=422,
                    invalid_component_inputs=["auto_freq_end_timestamp_str"],
                )
        else:
            auto_freq_end_timestamp = None
        return auto_freq_end_timestamp

    @validator("percentile")
    def verify_percentile(cls, percentile: float) -> float:
        if (percentile < 0) or (percentile > 1):
            raise ComponentInputValidationException(
                "The percentile value has to be a non-negative float less or equal to 1.",
                error_code=422,
                invalid_component_inputs=["percentile"],
            )
        return percentile

    @validator("interpolation_method")
    def verify_interpolation_method(cls, interpolation_method: str) -> str:
        if interpolation_method not in (
            "linear",
            "lower",
            "higher",
            "midpoint",
            "nearest",
        ):
            raise ComponentInputValidationException(
                "The interpolation method must be one of "
                "`linear`, `lower`, `higher`, `midpoint`, `nearest`",
                error_code=422,
                invalid_component_inputs=["interpolation_method"],
            )
        return interpolation_method

    @validator("min_amount_datapoints")
    def verify_min_amount_datapoints(cls, min_amount_datapoints: int) -> int:
        if min_amount_datapoints < 0:
            raise ComponentInputValidationException(
                "The minimum amount of datapoints has to be a non-negative integer.",
                error_code=422,
                invalid_component_inputs=["min_amount_datapoints"],
            )
        return min_amount_datapoints

    @validator("expected_frequency_str")
    def verify_expected_frequency(
        cls, expected_frequency_str: str, values: dict
    ) -> str:
        auto_frequency_determination = values["auto_frequency_determination"]
        if auto_frequency_determination is False:
            if expected_frequency_str is None:
                raise ComponentInputValidationException(
                    "A expected_frequency is required for gap detection, "
                    "if it is not automatically determined.",
                    error_code=422,
                    invalid_component_inputs=["expected_frequency_str"],
                )
        elif expected_frequency_str is not None:
            raise ComponentInputValidationException(
                "The expected_frequency must not be set, "
                "if automatical frequency determination is enabled.",
                error_code=422,
                invalid_component_inputs=["expected_frequency_str"],
            )
        return expected_frequency_str

    @validator("expected_frequency", always=True)
    def get_expected_frequency(
        cls, expected_frequency: pd.Timedelta | None, values: dict  # noqa: ARG002
    ) -> pd.Timedelta | None:
        if values["expected_frequency_str"] is None:
            return None
        return freqstr2timedelta(
            values["expected_frequency_str"], "expected_frequency_str"
        )

    @validator("expected_frequency_factor")
    def verify_expected_frequency_factor(cls, factor: float) -> float:
        if factor < 0:
            raise ComponentInputValidationException(
                "The gap size factor has to be a non-negative float.",
                error_code=422,
                invalid_component_inputs=["expected_frequency_factor"],
            )
        return factor


def add_boundary_timestamps(
    timeseries: pd.Series,
    interval_start_timestamp: pd.Timestamp,
    interval_end_timestamp: pd.Timestamp,
    fill_value: Any | None,
) -> pd.Series:
    if interval_start_timestamp not in timeseries.index:
        timeseries[interval_start_timestamp] = fill_value

    if interval_end_timestamp not in timeseries.index:
        timeseries[interval_end_timestamp] = fill_value

    timeseries = timeseries.sort_index()

    return timeseries


def constrict_series_to_interval(
    timeseries_data: pd.Series | pd.DataFrame,
    interval_start_timestamp: pd.Timestamp | None,
    interval_end_timestamp: pd.Timestamp | None,
) -> pd.Series | pd.DataFrame:
    true_array = np.ones(shape=len(timeseries_data), dtype=bool)
    series_after_start = (
        timeseries_data.index >= interval_start_timestamp
        if interval_start_timestamp is not None
        else true_array
    )
    series_before_end = (
        timeseries_data.index <= interval_end_timestamp
        if interval_start_timestamp is not None
        else true_array
    )
    return timeseries_data[series_after_start & series_before_end]


def check_amount_datapoints(series: pd.Series, min_amount_datapoints: int) -> None:
    if len(series) < min_amount_datapoints:
        raise ComponentInputValidationException(
            f"The timeseries does not contain at least {min_amount_datapoints} datapoints.",
            error_code=422,
            invalid_component_inputs=["timeseries"],
        )


def determine_expected_frequency(
    timeseries_data: pd.Series | pd.DataFrame,
    percentile: float,
    interpolation_method: str,
) -> pd.Timedelta:
    intervals = timeseries_data.index.to_series().diff().dropna()

    interval_size_percentile = intervals.quantile(
        percentile, interpolation=interpolation_method
    )

    return interval_size_percentile


def determine_normalized_interval_sizes(
    timeseries: pd.Series, expected_frequency: pd.Timedelta
) -> pd.DataFrame:
    intervals = timeseries.index.to_series().diff().to_numpy()

    expected_frequency_in_seconds = expected_frequency.total_seconds()

    normalized_interval_sizes = [
        pd.Timedelta(gap).total_seconds() / expected_frequency_in_seconds
        if pd.notna(gap)
        else None
        for gap in intervals
    ]

    result_df = pd.DataFrame(
        {"value": timeseries.to_numpy(), "gap": normalized_interval_sizes},
        index=timeseries.index,
    )

    return result_df


def identify_gaps(
    df_normalized_interval_sizes: pd.DataFrame,
    timeseries: pd.Series,
    expected_frequency_factor: float = 1.0,
) -> pd.DataFrame:
    # Identify rows where gap is greater than 1
    gap_ends = df_normalized_interval_sizes[
        df_normalized_interval_sizes["gap"] > expected_frequency_factor
    ].index.to_numpy()
    # Extract the start and end timestamps of the gaps
    gap_starts = [
        df_normalized_interval_sizes.index[index - 1]
        for index, large_gap_index in enumerate(df_normalized_interval_sizes.index)
        if large_gap_index in gap_ends
    ]

    left_values = timeseries[gap_starts].to_numpy()
    right_values = timeseries[gap_ends].to_numpy()

    # Create a DataFrame to store the results
    result_df = pd.DataFrame(
        {
            "start": gap_starts,
            "end": gap_ends,
            "start_inclusive": False,
            "end_inclusive": False,
            "gap_size": gap_ends - gap_starts,
            "value_to_left": left_values,
            "value_to_right": right_values,
            "mean_left_right": np.mean((left_values, right_values), axis=0)
            if pd.api.types.is_numeric_dtype(timeseries) is True
            else None,
        }
    )

    return result_df


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "timeseries": {"data_type": "SERIES"},
        "interval_start_timestamp_str": {"data_type": "STRING", "default_value": None},
        "interval_end_timestamp_str": {"data_type": "STRING", "default_value": None},
        "auto_frequency_determination": {"data_type": "BOOLEAN", "default_value": True},
        "auto_freq_end_timestamp_str": {
            "data_type": "STRING",
            "default_value": None,
        },
        "percentile": {"data_type": "FLOAT", "default_value": 0.5},
        "interpolation_method": {"data_type": "STRING", "default_value": "nearest"},
        "min_amount_datapoints": {"data_type": "INT", "default_value": 11},
        "expected_frequency_str": {"data_type": "STRING", "default_value": None},
        "expected_frequency_factor": {"data_type": "FLOAT", "default_value": 1.0},
        "fill_value": {"data_type": "ANY", "default_value": None},
    },
    "outputs": {
        "gap_info": {"data_type": "DATAFRAME"},
    },
    "name": "Gap Detection Intervals",
    "category": "Data Quality",
    "description": "Detects gaps in the given timeseries that are larger than the expected frequency and returns a DataFrame with information about the gaps.",  # noqa: E501
    "version_tag": "1.0.0",
    "id": "cd2a8b7f-a1af-4630-89a5-738af595472a",
    "revision_group_id": "415662ab-e4fb-4084-b752-80433d0df291",
    "state": "DRAFT",
}


def main(
    *,
    timeseries: pd.Series,
    interval_start_timestamp_str: str | None = None,
    interval_end_timestamp_str: str | None = None,
    auto_frequency_determination: bool | None = True,
    auto_freq_end_timestamp_str: str | None = None,
    percentile: float = 0.5,
    interpolation_method: str | None = "nearest",
    min_amount_datapoints: int = 11,
    expected_frequency_str: str | None = None,
    expected_frequency_factor: float = 1.0,
    fill_value: Any | None = None,
) -> dict:
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    timeseries = timeseries.sort_index().dropna()

    if interval_start_timestamp_str is None:
        if "ref_interval_start_timestamp" in timeseries.attrs:
            interval_start_timestamp_str = timeseries.attrs[
                "ref_interval_start_timestamp"
            ]
        elif "from" in timeseries.attrs:
            interval_start_timestamp_str = timeseries.attrs["from"]
    if interval_end_timestamp_str is None:
        if "ref_interval_end_timestamp" in timeseries.attrs:
            interval_end_timestamp_str = timeseries.attrs["ref_interval_end_timestamp"]
        elif "to" in timeseries.attrs:
            interval_end_timestamp_str = timeseries.attrs["to"]

    if expected_frequency_str is None and "ref_frequency" in timeseries.attrs:
        expected_frequency_str = timeseries.attrs["ref_frequency"]
        freqstr2timedelta(expected_frequency_str, 'timeseries.attrs["ref_frequency"]')
        auto_frequency_determination = False

    input_params = GapDetectionParameters(
        interval_start_timestamp_str=interval_start_timestamp_str,
        interval_end_timestamp_str=interval_end_timestamp_str,
        auto_frequency_determination=auto_frequency_determination,
        auto_freq_end_timestamp_str=auto_freq_end_timestamp_str,
        percentile=percentile,
        min_amount_datapoints=min_amount_datapoints,
        interpolation_method=interpolation_method,
        expected_frequency_str=expected_frequency_str,
        expected_frequency_factor=expected_frequency_factor,
        fill_value=fill_value,
    )
    series_with_bounds = add_boundary_timestamps(
        timeseries,
        input_params.interval_start_timestamp,
        input_params.interval_end_timestamp,
        fill_value,
    )
    constricted_series = constrict_series_to_interval(
        series_with_bounds,
        input_params.interval_start_timestamp,
        input_params.interval_end_timestamp,
    )

    if auto_frequency_determination:
        check_amount_datapoints(
            series=constricted_series,
            min_amount_datapoints=input_params.min_amount_datapoints,
        )
        if input_params.auto_freq_end_timestamp is not None:
            training_series = constrict_series_to_interval(
                timeseries,
                input_params.interval_start_timestamp,
                input_params.auto_freq_end_timestamp,
            )
        else:
            training_series = constricted_series
        input_params.expected_frequency = determine_expected_frequency(
            training_series, percentile, interpolation_method
        )

    df_with_gaps = determine_normalized_interval_sizes(
        constricted_series, input_params.expected_frequency
    )

    return {
        "gap_info": identify_gaps(
            df_with_gaps, constricted_series, expected_frequency_factor
        )
    }


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "timeseries",
            "adapter_id": "direct_provisioning",
            "filters": {
                "value": (
                    "{\n"
                    '    "2020-01-01T01:16:00.000Z": 10.0,\n'
                    '    "2020-01-01T01:18:00.000Z": 10.0,\n'
                    '    "2020-01-01T01:19:00.000Z": 10.0,\n'
                    '    "2020-01-01T01:20:00.000Z": 10.0,\n'
                    '    "2020-01-01T01:22:00.000Z": 20.0,\n'
                    '    "2020-01-01T01:23:00.000Z": 20.0,\n'
                    '    "2020-01-01T01:25:00.000Z": 20.0,\n'
                    '    "2020-01-01T08:28:00.000Z": 20.0,\n'
                    '    "2020-01-01T08:30:00.000Z": 30.0,\n'
                    '    "2020-01-01T08:31:00.000Z": 30.0,\n'
                    '    "2020-01-01T16:34:00.000Z": 30.0\n'
                    "}"
                )
            },
        },
    ],
}

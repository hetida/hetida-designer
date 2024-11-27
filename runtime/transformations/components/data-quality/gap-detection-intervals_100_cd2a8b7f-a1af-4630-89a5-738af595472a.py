"""Documentation for component "Gap Detection Intervals"

# Gap Detection Intervals

## Description

Detects gaps in the given timeseries that are larger than the expected data frequency and returns a
DataFrame with information about the gaps.

## Inputs

- **timeseries** (Series):
  Expects Pandas Series with index of datatype DateTimeIndex.

- **interval_start_timestamp** (String, default value: null):
  Desired start timestamp of the processing range. Expexcts ISO 8601 format.
  Alternatively, the **timeseries** can have metadata in the Pandas object's `.attrs` entry with key
  "ref_interval_start_timestamp" (or "from") that will be used if no **interval_start_timestamp**
  is provided.
  If neither is defined, the processing range begins with the first data point in **timeseries**.
  The start timestamp must not be later than the end timestamp.

- **interval_end_timestamp** (String, default value: null):
  Desired end timestamp of the processing range. Expexcts ISO 8601 format.
  Alternatively, the **timeseries** can have metadata in the Pandas object's `.attrs` entry with key
  "ref_interval_end_timestamp" (or "to") that will be used if no **interval_end_timestamp** is
  provided.
  If neither is defined, the processing range ends with the last data point in **timeseries**.
  The start timestamp must not be later than the end timestamp.

- **auto_frequency_determination** (Boolean, default value: true):
  If true, the function will automatically determine the expected data frequency based on the
  **timeseries** index and **expected_data_frequency** must not be set.
  If false, an **expected_data_frequency** must be set.
  If "ref_data_frequency" is contained in the attributes of **timeseries** this value will be used
  for the **expected_data_frequency** and **auto_frequency_determination** will be set to false.

- **auto_freq_percentile** (Float, default value: 0.5):
  Only relevant when **auto_frequency_determination** is true.
  Expects a positive value smaller than or equal to 1. The percentile value to use for automatic
  determination of the expected gapsize between two consecutive data points. The value should be
  selected according to the expected ratio of gaps to regular steps. I.e. if it is to be expected
  that more than 50% of the time differences are gaps, the value should be reduced; if fewer gaps
  are to be expected, the value can be adjusted upwards accordingly.

- **auto_freq_min_amount_datapoints** (Int, default value: 11):
  Only relevant when **auto_frequency_determination** is true.
  Expects a positive value. Minimum amount of datapoints required. Effects the expectable precision
  of the automatically determined expected data frequency.

- **expected_data_frequency** (String, default value: null):
  Must not be set if **auto_frequency_determination** is true, but must be set if
  **auto_frequency_determination** is false.
  The expected time difference between consecutive timestamps in the input **timeseries**. Must be a
  [date offset aliases](
    https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#timeseries-offset-aliases
  ) or a timedelta string, e.g. "D" or "60s".
  Alternatively, the **timeseries** can have metadata in the Pandas object's `.attrs` entry with key
  "ref_data_frequency" that will be used if no **expected_data_frequency** is provided.
  In that case **auto_frequency_determination** will be set to false.

- **expected_data_freq_allowed_variance_factor** (Float, default value: 1.0):
  Expects a positive value. The value is used to define when a step between two consecutive data
  points is recognized as a gap. I.e. a value of 1.0 means that all steps larger than the
  specified or determined expected data frequency are recognized as gaps, while a value of 2.0 means
  that intevals are only recognized as gaps if they are more than twice as large as the specified or
  determined expected data frequency.

- **expected_data_frequency_offset** (String, default value: null):
  Must not be set if **auto_frequency_determination** is true or the **expected_data_frequency**
  is not set.
  The time difference between the reference time  1970-01-01 00:00:00 and the timestamps of the
  input **timeseries** with the provided expected data frequency. Must be a
  [date offset aliases](
    https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#timeseries-offset-aliases
  ) or a timedelta string, e.g. "D" or "60s".

- **externally_determined_gap_timestamps** (Series, default value: null):
  Expects Pandas Series with index of datatype DateTimeIndex. The values are not considered.

- **externally_determined_gap_intervals** (DataFrame, default value: null):
  Expects Pandas DataFrame with columns "start_time", "end_time", "start_inclusive", "end_inclusive,
  which all have a datatime64 dtype.

- **deactivate_internal_gap_detection** (bool, default value: false):
  Set to `true` to disable any gap detection and only determine the gap_info for
  **externally_determined_gap_timestamps** and **externally_determined_gap_intervals**.

## Outputs

- **data_frequency** (String):
  The [date offset aliases](
    https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#timeseries-offset-aliases
  ) corresponding to the data frequency used for gap detection.
- **gap_info** (DataFrame):
  A DataFrame containing the beginning and end timestamps of gaps larger than the specified or
  determined expected data frequency.
  Columns are:
  - "start_time" (Timestamp): Start timestamp of the gap.
  - "end_time" (Timestamp): End timestamp of the gap.
  - "start_inclusive" (Boolean): Defines whether the start boundary timestamp is inclusive or not.
  - "end_inclusive" (Boolean): Defines whether the end boundary timestamp is inclusive or not.
  - "gap_size_in_seconds" (Float): Size of the gap in seconds.
  - "value_to_left" (Float/Int): If existing, last value before the gap, otherwise None.
  - "value_to_right" (Float/Int): If existing, first value after the gap, otherwise None.
  - "mean_left_right" (Float/Int): The mean value of the `value_to_left` and `value_to_right`.
    None, if at least one of these values is None.

## Details

If **interval_start_timestamp** (or **interval_end_timestamp**) is not zero, check whether
it is contained in the **timeseries** and add it if necessary, and remove all data points with an
earlier (or later) index in order to reduce the **timeseries** to the processing range.

To detect gaps, the time intervals between consecutive data points are determined.
If **auto_frequency_determination** is set to true, determine the expected data frequency using the
**auto_freq_percentile**-th quantile of the time intervals.
If **auto_frequency_determination` is set to false, the expected data frequency is defined by the
**expected_data_frequency**.
If a time interval is greater than the product of the **expected_data_freq_allowed_variance_factor**
and the expected data frequency, it is considered a gap.

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
Such issues can be tackled by choosing a smaller **auto_freq_percentile** or a smaller
**expected_data_freq_allowed_variance_factor**.
Thus the corresponding result is
```
{
    "__hd_wrapped_data_object__": "DATAFRAME",
    "__metadata__": {},
    "__data__": {
        "start_time": {
            "0": "2020-01-01T01:25:00.000Z",
            "1": "2020-01-01T08:31:00.000Z"
        },
        "end_time": {
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
        "gap_size_in_seconds": {
            "0": 25380,
            "1": 28980
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
            "ref_data_frequency": "1min"
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
    "interval_start_timestamp": "2020-01-01T00:16:00.000Z",
    "interval_end_timestamp": "2020-01-01T16:34:00.000Z",
    "auto_frequency_determination": false,
    "expected_data_frequency": "1min"
}
```
The result of either of these inputs is then
```
{
    "__hd_wrapped_data_object__": "DATAFRAME",
    "__metadata__": {},
    "__data__": {
        "start_time": {
            "0": "2020-01-01T00:16:00.000Z",
            "1": "2020-01-01T01:16:00.000Z",
            "2": "2020-01-01T01:20:00.000Z",
            "3": "2020-01-01T01:23:00.000Z",
            "4": "2020-01-01T01:25:00.000Z",
            "5": "2020-01-01T08:28:00.000Z",
            "6": "2020-01-01T08:31:00.000Z"
        },
        "end_time": {
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
        "gap_size_in_seconds": {
            "0": 3600,
            "1": 120,
            "2": 120,
            "3": 120,
            "4": 25380,
            "5": 120,
            "6": 28980
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
}
```
In some cases, data in the timeseries is expected at specific periodic points in time, e.g. every
full minute or every five minutes, at :04, :09, :14 etc.
If the frequency offset is specified in addition to the expected data frequency, the corresponding
timestamps are added as gaps of size 0s if there is no datapoint in the **timeseries** at this
point.

In the following example JSON input, the provided series would have no gaps if no
**expected_data_frequency_offset** was set, since all datapoints are separated exactly by the
expected data frequency of one minute.
However, if **expected_data_frequency_offset** is set to `0s`, there are a total of four gaps,
including those at the timestamps defined by **interval_start_timestamp** and
**interval_end_timestamp**.
```
{
    "timeseries": {
        "2020-01-01T01:16:30.000Z": 10.0,
        "2020-01-01T01:17:30.000Z": 10.0,
        "2020-01-01T01:18:30.000Z": 10.0
    },
    "interval_start_timestamp": "2020-01-01T01:16:00.000Z",
    "interval_end_timestamp": "2020-01-01T01:19:00.000Z",
    "auto_frequency_determination": false,
    "expected_data_frequency": "1min",
    "expected_data_frequency_offset": "0s",
}
```
The result is then the following output:
```
{
    "__hd_wrapped_data_object__": "DATAFRAME",
    "__metadata__": {},
    "__data__": {
        "start_time": {
            "0": "2020-01-01T01:16:00.000Z",
            "1": "2020-01-01T01:17:00.000Z",
            "2": "2020-01-01T01:18:00.000Z",
            "3": "2020-01-01T01:19:00.000Z"
        },
        "end_time": {
            "0": "2020-01-01T01:16:00.000Z",
            "1": "2020-01-01T01:17:00.000Z",
            "2": "2020-01-01T01:18:00.000Z",
            "3": "2020-01-01T01:19:00.000Z"
        },
        "start_inclusive": {
            "0": true,
            "1": true,
            "2": true,
            "3": true
        },
        "end_inclusive": {
            "0": true,
            "1": true,
            "2": true,
            "3": true
        },
        "gap_size_in_seconds": {
            "0": 0,
            "1": 0,
            "2": 0,
            "3": 0
        },
        "value_to_left": {
            "0": null,
            "1": 10,
            "2": 10,
            "3": 10
        },
        "value_to_right": {
            "0": 10,
            "1": 10,
            "2": 10,
            "3": null
        },
        "mean_left_right": {
            "0": null,
            "1": 10,
            "2": 10,
            "3": null
        }
    }
}
```
Furthermore, it is possible to include information on gaps from external sources, for example caused
by downtime or outages, where the data is likely to be atypical and should therefore not be included
in the analysis.
Gap points can be specified in a series, whereas gap intervals must be specified by a data frame
containing the expected columns.Further gap detection can be disabled by setting
**deactivate_internal_gap_detection** to true.
The example JSON input
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
        "2020-01-01T01:28:00.000Z": 20.0,
        "2020-01-01T01:30:00.000Z": 30.0,
        "2020-01-01T01:31:00.000Z": 30.0,
        "2020-01-01T01:34:00.000Z": 30.0
    },
    "externally_determined_gap_timestamps": {
        "2020-01-01T01:25:00.000Z": true,
        "2020-01-01T01:29:00.000Z": true
    },
    "externally_determined_gap_intervals": [
        {
            "start_time": "2020-01-01T01:01:00.000Z",
            "end_time": "2020-01-01T01:13:00.000Z",
            "start_inclusive": false,
            "end_inclusive": false
        },
        {
            "start_time": "2020-01-01T01:14:00.000Z",
            "end_time": "2020-01-01T01:25:00.000Z",
            "start_inclusive": false,
            "end_inclusive": false
        },
        {
            "start_time": "2020-01-01T01:31:00.000Z",
            "end_time": "2020-01-01T01:33:00.000Z",
            "start_inclusive": false,
            "end_inclusive": false
        },
        {
            "start_time": "2020-01-01T01:32:00.000Z",
            "end_time": "2020-01-01T01:38:00.000Z",
            "start_inclusive": false,
            "end_inclusive": false
        }
    ],
    "deactivate_internal_gap_detection": true,
}
```
then results in the following output with only those (parts of the) externally determined gaps,
which overlap with the time interval of interest:
```
{
    "__hd_wrapped_data_object__": "DATAFRAME",
    "__metadata__": {},
    "__data__": {
        "start_time": {
            "0": "2020-01-01T01:16:00.000Z",
            "1": "2020-01-01T01:29:00.000Z",
            "2": "2020-01-01T01:31:00.000Z"
        },
        "end_time": {
            "0": "2020-01-01T01:25:00.000Z",
            "1": "2020-01-01T01:29:00.000Z",
            "2": "2020-01-01T01:34:00.000Z"
        },
        "start_inclusive": {
            "0": true,
            "1": true,
            "2": false
        },
        "end_inclusive": {
            "0": true,
            "1": true,
            "2": true
        },
        "gap_size_in_seconds": {
            "0": 540,
            "1": 0,
            "2": 180
        },
        "value_to_left": {
            "0": null,
            "1": 20,
            "2": 30
        },
        "value_to_right": {
            "0": 20,
            "1": 30,
            "2": null
        },
        "mean_left_right": {
            "0": null,
            "1": 25,
            "2": null
        }
    }
}
```
"""

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from pydantic import BaseModel, validator

from hdutils import ComponentInputValidationException


def timestamp_str_to_pd_timestamp(timestamp_str: str, input_name: str) -> pd.Timestamp:
    """Transform timestamp string to Pandas Timestamp.

    >>> timestamp_str_to_pd_timestamp("2024-02-16 09:39", "test_input")
    Timestamp('2024-02-16 09:39:00+0000', tz='UTC')
    """
    try:
        timestamp = pd.to_datetime(timestamp_str, utc=True)
    except ValueError as error:
        raise ComponentInputValidationException(
            str(error), error_code=422, invalid_component_inputs=[input_name]
        ) from error
    return timestamp


def freqstr2dateoffset(freqstr: str) -> pd.DateOffset:
    """Transform frequency string to Pandas DateOffset.

    >>> freqstr2dateoffset("5min")
    <5 * Minutes>
    """
    return pd.tseries.frequencies.to_offset(freqstr)


def freqstr2timedelta(freqstr: str, input_name: str) -> pd.Timedelta:
    """Transform frequency string to Pandas Timedelta.

    >>> freqstr2timedelta("5min","test_input")
    Timedelta('0 days 00:05:00')
    """
    try:
        return pd.to_timedelta(freqstr)
    except ValueError:
        try:
            return pd.to_timedelta(freqstr2dateoffset(freqstr))
        except TypeError as err:
            raise ComponentInputValidationException(
                f"The {input_name} cannot be parsed as Pandas Timedelta: {str(err)}",
                error_code=422,
                invalid_component_inputs=[input_name],
            ) from err


class GapDetectionParameters(BaseModel, arbitrary_types_allowed=True):
    timeseries: pd.Series
    interval_start_timestamp_str: str | None
    interval_start_timestamp: pd.Timestamp | None = None
    interval_end_timestamp_str: str | None
    interval_end_timestamp: pd.Timestamp | None = None
    auto_frequency_determination: bool
    percentile: float
    min_amount_datapoints: int
    expected_data_frequency_str: str | None
    expected_data_frequency: pd.Timedelta | None = None
    expected_data_frequency_factor: float
    expected_data_frequency_offset_str: str | None = None
    expected_data_frequency_offset: pd.Timedelta | None = None
    externally_determined_gap_timestamps: pd.Series | None
    externally_determined_gap_intervals: pd.DataFrame | None

    @validator("timeseries")
    def timeseries_index_has_datetime_dtype(cls, timeseries: pd.Series) -> pd.Series:
        if len(timeseries) == 0:
            timeseries = pd.Series({})
            timeseries.index = pd.to_datetime(timeseries.index, utc=True)

        if pd.api.types.is_datetime64_any_dtype(timeseries.index.dtype) is False:
            raise ComponentInputValidationException(
                "The index of `timeseries` is not of any datetime64 dtype, "
                f"but {timeseries.index.dtype}.",
                error_code=422,
                invalid_component_inputs=["timeseries"],
            )
        return timeseries

    @validator("interval_start_timestamp", always=True)
    def get_interval_start_timestamp_from_interval_start_timestamp_str(
        cls,
        interval_start_timestamp: pd.Timestamp | None,  # noqa: ARG002
        values: dict,
    ) -> pd.Timestamp | None:
        if values["interval_start_timestamp_str"] is None:
            if "timeseries" in values and len(values["timeseries"]) > 0:
                return values["timeseries"].index[0]
            return None

        return timestamp_str_to_pd_timestamp(
            values["interval_start_timestamp_str"], "interval_start_timestamp_str"
        )

    @validator("interval_end_timestamp", always=True)
    def get_interval_end_timestamp_from_interval_end_timestamp_str(
        cls,
        interval_end_timestamp: pd.Timestamp | None,  # noqa: ARG002
        values: dict,
    ) -> pd.Timestamp | None:
        if values["interval_end_timestamp_str"] is None:
            if "timeseries" in values and len(values["timeseries"]) > 0:
                return values["timeseries"].index[-1]
            return None

        return timestamp_str_to_pd_timestamp(
            values["interval_end_timestamp_str"], "interval_end_timestamp_str"
        )

    @validator("interval_end_timestamp")
    def check_interval_end_timestamp_later_than_interval_start_timestamp(
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
                    "interval_start_timestamp",
                    "interval_end_timestamp",
                ],
            )
        return interval_end_timestamp

    @validator("percentile")
    def check_percentile_in_allowed_range(cls, percentile: float) -> float:
        if (percentile < 0) or (percentile > 1):
            raise ComponentInputValidationException(
                "The percentile value has to be a non-negative float less or equal to 1.",
                error_code=422,
                invalid_component_inputs=["auto_freq_percentile"],
            )
        return percentile

    @validator("min_amount_datapoints")
    def check_min_amount_datapoints_non_negative(cls, min_amount_datapoints: int) -> int:
        if min_amount_datapoints < 0:
            raise ComponentInputValidationException(
                "The minimum amount of datapoints has to be a non-negative integer.",
                error_code=422,
                invalid_component_inputs=["auto_freq_min_amount_datapoints"],
            )
        return min_amount_datapoints

    @validator("expected_data_frequency_str")
    def check_correct_input_param_combination_with_expected_data_frequency(
        cls, expected_data_frequency_str: str, values: dict
    ) -> str:
        auto_frequency_determination = values["auto_frequency_determination"]
        if auto_frequency_determination is False:
            if expected_data_frequency_str is None:
                raise ComponentInputValidationException(
                    "An expected_data_frequency_str is required for gap detection, "
                    "if it is not automatically determined.",
                    error_code=422,
                    invalid_component_inputs=[
                        "auto_frequency_determination",
                        "expected_data_frequency",
                    ],
                )
        elif expected_data_frequency_str is not None:
            raise ComponentInputValidationException(
                "The expected_data_frequency_str must not be set, "
                "if automatical frequency determination is enabled.",
                error_code=422,
                invalid_component_inputs=[
                    "auto_frequency_determination",
                    "expected_data_frequency",
                ],
            )
        return expected_data_frequency_str

    @validator("expected_data_frequency", always=True)
    def get_expected_data_frequency(
        cls,
        expected_data_frequency: pd.Timedelta | None,  # noqa: ARG002
        values: dict,
    ) -> pd.Timedelta | None:
        if values["expected_data_frequency_str"] is None:
            return None
        return freqstr2timedelta(
            values["expected_data_frequency_str"], "expected_data_frequency_str"
        )

    @validator("expected_data_frequency_offset_str")
    def check_correct_input_param_combination_with_expected_data_frequency_offset(
        cls, expected_data_frequency_offset_str: str, values: dict
    ) -> str:
        if expected_data_frequency_offset_str is None:
            return None
        auto_frequency_determination = values["auto_frequency_determination"]
        expected_data_frequency_str = values["expected_data_frequency_str"]
        if auto_frequency_determination is True:
            raise ComponentInputValidationException(
                "The expected_data_frequency_offset_str must not be set, "
                "if automatical frequency determination is enabled.",
                error_code=422,
                invalid_component_inputs=[
                    "auto_frequency_determination",
                    "expected_data_frequency_offset",
                ],
            )
        if expected_data_frequency_str is None:
            raise ComponentInputValidationException(
                "An expected_data_frequency_str is required for gap detection, "
                "if an expected_data_frequency_offset_str is provided.",
                error_code=422,
                invalid_component_inputs=[
                    "expected_data_frequency",
                    "expected_data_frequency_offset",
                ],
            )
        return expected_data_frequency_offset_str

    @validator("expected_data_frequency_offset", always=True)
    def get_expected_data_frequency_offset(
        cls,
        expected_data_frequency_offset: pd.Timedelta | None,  # noqa: ARG002
        values: dict,
    ) -> pd.Timedelta | None:
        if (
            "expected_data_frequency_offset_str" not in values
            or values["expected_data_frequency_offset_str"] is None
        ):
            return None
        return (
            freqstr2timedelta(
                values["expected_data_frequency_offset_str"],
                "expected_data_frequency_offset_str",
            )
            % values["expected_data_frequency"]
        )

    @validator("expected_data_frequency_factor")
    def check_expected_data_frequency_factor_non_negative(cls, factor: float) -> float:
        if factor < 0:
            raise ComponentInputValidationException(
                "The gap size factor has to be a non-negative float.",
                error_code=422,
                invalid_component_inputs=["expected_data_freq_allowed_variance_factor"],
            )
        return factor

    @validator("externally_determined_gap_timestamps")
    def externally_determined_gap_timestamps_index_has_datetime_dtype(
        cls, externally_determined_gap_timestamps: pd.Series | None
    ) -> pd.Series | None:
        if externally_determined_gap_timestamps is None:
            return externally_determined_gap_timestamps

        if (
            pd.api.types.is_datetime64_any_dtype(externally_determined_gap_timestamps.index.dtype)
            is False
        ):
            raise ComponentInputValidationException(
                "The index of `externally_determined_gap_timestamps` is not of "
                f"any datetime64 dtype, but {externally_determined_gap_timestamps.index.dtype}.",
                error_code=422,
                invalid_component_inputs=["externally_determined_gap_timestamps"],
            )

        return externally_determined_gap_timestamps

    @validator("externally_determined_gap_intervals")
    def check_required_externally_determined_gap_intervals_columns_are_present(
        cls, externally_determined_gap_intervals: pd.DataFrame | None
    ) -> pd.DataFrame | None:
        if externally_determined_gap_intervals is None:
            return None

        required_column_names = {
            "start_time",
            "end_time",
            "start_inclusive",
            "end_inclusive",
        }

        if not required_column_names.issubset(set(externally_determined_gap_intervals.columns)):
            column_names_string = ", ".join(externally_determined_gap_intervals.columns)
            required_column_names_string = ", ".join(required_column_names)
            raise ComponentInputValidationException(
                f"The column names {column_names_string} of `externally_determined_gap_intervals` "
                f"don't contain the required columns {required_column_names_string}.",
                error_code=422,
                invalid_component_inputs=["externally_determined_gap_intervals"],
            )

        return externally_determined_gap_intervals

    @validator("externally_determined_gap_intervals")
    def check_externally_determined_gap_intervals_columns_have_datetime_dtype(
        cls, externally_determined_gap_intervals: pd.DataFrame | None
    ) -> pd.DataFrame | None:
        if externally_determined_gap_intervals is None:
            return None

        required_datetime64_column_names = ["start_time", "end_time"]

        if not any(
            pd.api.types.is_datetime64_any_dtype(column_dtype)
            for column_dtype in externally_determined_gap_intervals[
                required_datetime64_column_names
            ].dtypes
        ):
            required_column_names_string = ", ".join(required_datetime64_column_names)
            raise ComponentInputValidationException(
                f"At least one of the required columns {required_column_names_string} "
                "is not of any datetime64 dtype.",
                error_code=422,
                invalid_component_inputs=["externally_determined_gap_intervals"],
            )
        return externally_determined_gap_intervals


def constrict_series_to_interval(
    timeseries: pd.Series,
    interval_start_timestamp: pd.Timestamp | None,
    interval_end_timestamp: pd.Timestamp | None,
) -> pd.Series:
    true_array = np.ones(shape=len(timeseries), dtype=bool)
    series_after_start = (
        timeseries.index >= interval_start_timestamp
        if interval_start_timestamp is not None
        else true_array
    )
    series_before_end = (
        timeseries.index <= interval_end_timestamp
        if interval_start_timestamp is not None
        else true_array
    )
    return timeseries[series_after_start & series_before_end]


def add_boundary_timestamps_and_sort(
    timeseries_with_bounds: pd.Series,
    interval_start_timestamp: pd.Timestamp | None,
    interval_end_timestamp: pd.Timestamp | None,
) -> pd.Series:
    timeseries_with_bounds = timeseries_with_bounds.copy()
    if (
        interval_start_timestamp is not None
        and interval_start_timestamp not in timeseries_with_bounds.index
    ):
        timeseries_with_bounds[interval_start_timestamp] = None

    if (
        interval_end_timestamp is not None
        and interval_end_timestamp not in timeseries_with_bounds.index
    ):
        timeseries_with_bounds[interval_end_timestamp] = None

    return timeseries_with_bounds.sort_index()


def check_amount_datapoints(series: pd.Series, min_amount_datapoints: int) -> None:
    if len(series) < min_amount_datapoints:
        raise ComponentInputValidationException(
            f"The timeseries does not contain at least {min_amount_datapoints} datapoints.",
            error_code=422,
            invalid_component_inputs=["timeseries"],
        )


def determine_expected_data_frequency(
    timeseries: pd.Series,
    percentile: float,
) -> pd.Timedelta:
    intervals = timeseries.index.to_series().diff().dropna()

    interval_size_percentile = intervals.quantile(percentile, interpolation="nearest")

    return interval_size_percentile


def determine_normalized_interval_sizes(
    timeseries: pd.Series, expected_data_frequency: pd.Timedelta
) -> pd.DataFrame:
    intervals = timeseries.index.to_series().diff().to_numpy()

    expected_data_frequency_in_seconds = expected_data_frequency.total_seconds()

    normalized_interval_sizes = [
        (
            pd.Timedelta(gap).total_seconds() / expected_data_frequency_in_seconds
            if pd.notna(gap)
            else None
        )
        for gap in intervals
    ]

    result_df = pd.DataFrame(
        {"value": timeseries.to_numpy(), "gap": normalized_interval_sizes},
        index=timeseries.index,
    )

    return result_df


no_gap_intervals = pd.DataFrame(
    {},
    columns=[
        "start_time",
        "end_time",
        "start_inclusive",
        "end_inclusive",
    ],
).astype(
    {
        "start_time": "datetime64[ns, UTC]",
        "end_time": "datetime64[ns, UTC]",
        "start_inclusive": bool,
        "end_inclusive": bool,
    }
)


empty_gap_info = pd.DataFrame(
    {},
    columns=[
        "start_time",
        "end_time",
        "start_inclusive",
        "end_inclusive",
        "gap_size_in_seconds",
        "value_to_left",
        "value_to_right",
        "mean_left_right",
    ],
).astype(
    {
        "start_time": "datetime64[ns, UTC]",
        "end_time": "datetime64[ns, UTC]",
        "start_inclusive": bool,
        "end_inclusive": bool,
        "gap_size_in_seconds": float,
    }
)


def identify_gaps(
    df_normalized_interval_sizes: pd.DataFrame,
    expected_data_frequency_factor: float = 1.0,
) -> pd.DataFrame:
    # Identify rows where gap is greater than 1
    gap_ends = df_normalized_interval_sizes[
        df_normalized_interval_sizes["gap"] > expected_data_frequency_factor
    ].index.to_numpy()

    if len(gap_ends) == 0:
        return no_gap_intervals

    # Extract the start of the gaps
    gap_starts = [
        df_normalized_interval_sizes.index[index - 1]
        for index, large_gap_index in enumerate(df_normalized_interval_sizes.index)
        if large_gap_index in gap_ends
    ]

    gap_intervals = pd.DataFrame(
        {
            "start_time": gap_starts,
            "end_time": gap_ends,
            "start_inclusive": False,
            "end_inclusive": False,
        }
    )

    return gap_intervals


def shift_timestamp_to_the_left_onto_rhythm(
    timestamp: pd.Timestamp,
    data_frequency: pd.DateOffset,
    data_frequency_offset: pd.Timedelta,
) -> pd.Timestamp:
    """Shift a timestamp to the left in the rhythm.

    The parameters data_frequency and data_frequency_offset define a kind of "rhythm".
    For example a data_frequency of "5min" and a data_frequency_offset of "1min" define the
    rhythm which contains all timestamps, where the minutes are 01, 06, 11, 16, and so on.
    The provided timestamp is shifted to the left onto the closest timestamp of this rhythm.

    Conveniently, the Pandas class Timestamp comes with a method `floor`, which is similar to
    the mathematical method `floor`, but instead of a decimal place takes into account the
    specified frequency.
    """
    return (timestamp - data_frequency_offset).floor(freq=data_frequency) + data_frequency_offset


def shift_timestamp_to_the_right_onto_rhythm(
    timestamp: pd.Timestamp,
    data_frequency: pd.DateOffset,
    data_frequency_offset: pd.Timedelta,
) -> pd.Timestamp:
    """Shift a timestamp to the right in the rhythm.

    The parameters data_frequency and data_frequency_offset define a kind of "rhythm".
    The specified timestamp is shifted to the right onto the closest timestamp of this rhythm.

    Conveniently, the Pandas class Timestamp has a method `ceil` that is similar to the
    mathematical method `ceil`, but instead of a decimal place, it takes into account the
    specified frequency.
    """
    return (timestamp - data_frequency_offset).ceil(freq=data_frequency) + data_frequency_offset


def get_boundary_values(
    timeseries: pd.Series,
    gap_boundaries: NDArray[np.datetime64],
    gap_boundaries_inclusive: NDArray[np.bool_],
    method: str,
) -> NDArray:
    exclusive_index = timeseries.index.join(
        pd.Index(gap_boundaries[np.logical_not(gap_boundaries_inclusive)]),
        how="outer",
        sort=True,
    ).sort_values()
    boundary_values_exclusive = timeseries.reindex(
        index=exclusive_index,
        method=method,
    )
    boundary_values_exclusive = boundary_values_exclusive[
        gap_boundaries[np.logical_not(gap_boundaries_inclusive)]
    ]

    timeseries_without_inclusive_gap_boundaries = timeseries.copy()
    timeseries_without_inclusive_gap_boundaries = timeseries_without_inclusive_gap_boundaries.drop(
        timeseries_without_inclusive_gap_boundaries.index.intersection(
            gap_boundaries[gap_boundaries_inclusive]
        )
    )
    boundary_values_inclusive = timeseries_without_inclusive_gap_boundaries.reindex(
        timeseries.index.join(
            pd.Index(gap_boundaries[gap_boundaries_inclusive]),
            how="outer",
            sort=True,
        ),
        method=method,
    )
    boundary_values_inclusive = boundary_values_inclusive[gap_boundaries[gap_boundaries_inclusive]]

    boundary_values = pd.concat(
        [
            series
            for series in (boundary_values_exclusive, boundary_values_inclusive)
            if len(series) != 0
        ]
    )

    return boundary_values.sort_index().to_numpy()


def constricted_gap_timestamps_to_intervals(
    constricted_gap_points: pd.Series,
) -> pd.DataFrame:
    if len(constricted_gap_points) == 0:
        return no_gap_intervals

    gap_intervals = pd.DataFrame(
        {
            "start_time": constricted_gap_points.index,
            "end_time": constricted_gap_points.index,
            "start_inclusive": True,
            "end_inclusive": True,
        }
    )

    return gap_intervals


def identify_gaps_from_missing_expected_datapoints(
    constricted_timeseries_without_bounds: pd.Series,
    interval_start_timestamp: pd.Timestamp,
    interval_end_timestamp: pd.Timestamp,
    expected_data_frequency: pd.Timedelta,
    expected_data_frequency_offset: pd.Timedelta | None,
) -> pd.DataFrame:
    if expected_data_frequency_offset is None:
        return None

    expected_datapoints = pd.date_range(
        start=shift_timestamp_to_the_right_onto_rhythm(
            interval_start_timestamp,
            expected_data_frequency,
            expected_data_frequency_offset,
        ),
        end=shift_timestamp_to_the_left_onto_rhythm(
            interval_end_timestamp,
            expected_data_frequency,
            expected_data_frequency_offset,
        ),
        freq=expected_data_frequency,
        inclusive="both",
    )

    missing_expected_datapoints = expected_datapoints.difference(
        constricted_timeseries_without_bounds.index
    )

    return constricted_gap_timestamps_to_intervals(
        pd.Series(index=missing_expected_datapoints),
    )


def constrict_intervals_df_to_interval(
    gap_intervals: pd.DataFrame,
    interval_start_timestamp: pd.Timestamp | None,
    interval_end_timestamp: pd.Timestamp | None,
) -> pd.DataFrame:
    if interval_start_timestamp is not None:
        gap_start_before_interval_start_index = gap_intervals[
            gap_intervals["start_time"] < interval_start_timestamp
        ].index
        gap_intervals.loc[gap_start_before_interval_start_index, "start_time"] = (
            interval_start_timestamp
        )
        gap_intervals.loc[gap_start_before_interval_start_index, "start_inclusive"] = True

    if interval_end_timestamp is not None:
        gap_end_after_interval_end_index = gap_intervals[
            gap_intervals["end_time"] > interval_end_timestamp
        ].index
        gap_intervals.loc[gap_end_after_interval_end_index, "end_time"] = interval_end_timestamp
        gap_intervals.loc[gap_end_after_interval_end_index, "end_inclusive"] = True

    gap_intervals = gap_intervals.drop(
        gap_intervals[gap_intervals["start_time"] > gap_intervals["end_time"]].index
    )
    gap_intervals = gap_intervals.drop(
        gap_intervals[
            (gap_intervals["start_time"] == gap_intervals["end_time"])
            & (~gap_intervals["start_inclusive"] | ~gap_intervals["end_inclusive"])
        ].index
    )

    return gap_intervals


def merge_intervals(intervals: pd.DataFrame) -> pd.DataFrame:
    """Merge intervals.

    Apply cumsum to logical conditions that specify where in the dataframe a group change occurs in
    order to generate group indices for grouping the data.
    Therefore, the correct sorting of the data in the data frame is crucial.
    Multiple steps are required to properly track whether the resulting interval boundary is
    inclusive or not.

    >>> merge_intervals(
    ...     pd.DataFrame(
    ...         [
    ...             {
    ...                 "start_time": "2020-01-01T01:16:00.000Z",
    ...                 "end_time": "2020-01-01T01:25:00.000Z",
    ...                 "start_inclusive": True,
    ...                 "end_inclusive": False
    ...             },
    ...             {
    ...                 "start_time": "2020-01-01T01:25:00.000Z",
    ...                 "end_time": "2020-01-01T01:25:00.000Z",
    ...                 "start_inclusive": True,
    ...                 "end_inclusive": True
    ...             },
    ...             {
    ...                 "start_time": "2020-01-01T01:29:00.000Z",
    ...                 "end_time": "2020-01-01T01:29:00.000Z",
    ...                 "start_inclusive": True,
    ...                 "end_inclusive": True
    ...             },
    ...             {
    ...                 "start_time": "2020-01-01T01:31:00.000Z",
    ...                 "end_time": "2020-01-01T01:33:00.000Z",
    ...                 "start_inclusive": False,
    ...                 "end_inclusive": False
    ...             },
    ...             {
    ...                 "start_time": "2020-01-01T01:32:00.000Z",
    ...                 "end_time": "2020-01-01T01:34:00.000Z",
    ...                 "start_inclusive": False,
    ...                 "end_inclusive": True
    ...             }
    ...         ]
    ...     )
    ... )
                         start_time  ... end_inclusive
    touch                            ...
    0      2020-01-01T01:16:00.000Z  ...          True
    1      2020-01-01T01:29:00.000Z  ...          True
    2      2020-01-01T01:31:00.000Z  ...          True
    <BLANKLINE>
    [3 rows x 4 columns]
    """
    intervals = intervals.sort_values(["start_time", "end_time"])

    intervals["same_start_time"] = (
        intervals["start_time"] != intervals["start_time"].shift()
    ).cumsum()
    intervals = intervals.groupby(intervals["same_start_time"]).agg(
        {
            "start_time": "first",
            "end_time": "last",
            "start_inclusive": any,
            "end_inclusive": "last",
        }
    )

    intervals["same_end_time"] = (intervals["end_time"] != intervals["end_time"].shift()).cumsum()
    intervals = intervals.groupby(intervals["same_end_time"]).agg(
        {
            "start_time": "first",
            "end_time": "last",
            "start_inclusive": "first",
            "end_inclusive": any,
        }
    )

    intervals["overlap"] = (intervals["start_time"] >= intervals["end_time"].shift()).cumsum()
    intervals = intervals.groupby(intervals["overlap"]).agg(
        {
            "start_time": "first",
            "end_time": "last",
            "start_inclusive": "first",
            "end_inclusive": "last",
        }
    )

    intervals["touch"] = (
        (intervals["start_time"] > intervals["end_time"].shift())
        | (~(intervals["start_inclusive"] & intervals["end_inclusive"]))
    ).cumsum()
    intervals = intervals.groupby(intervals["touch"]).agg(
        {
            "start_time": "first",
            "end_time": "last",
            "start_inclusive": "first",
            "end_inclusive": "last",
        }
    )

    return intervals


def get_gap_intervals_info(
    constricted_timeseries_with_bounds: pd.Series,
    constricted_gap_interval_dfs: list[pd.DataFrame],
) -> pd.DataFrame:
    constricted_gap_interval_dfs = [
        df for df in constricted_gap_interval_dfs if df is not None and len(df) != 0
    ]

    if len(constricted_gap_interval_dfs) == 0:
        return empty_gap_info

    merged_gap_intervals = merge_intervals(
        pd.concat(constricted_gap_interval_dfs, ignore_index=True)
    )

    gap_starts = merged_gap_intervals["start_time"].to_numpy()
    gap_starts_inclusive = merged_gap_intervals["start_inclusive"].to_numpy()
    left_values = get_boundary_values(
        timeseries=constricted_timeseries_with_bounds,
        gap_boundaries=gap_starts,
        gap_boundaries_inclusive=gap_starts_inclusive,
        method="ffill",
    )

    gap_ends = merged_gap_intervals["end_time"].to_numpy()
    gap_ends_inclusive = merged_gap_intervals["end_inclusive"].to_numpy()
    right_values = get_boundary_values(
        timeseries=constricted_timeseries_with_bounds,
        gap_boundaries=gap_ends,
        gap_boundaries_inclusive=gap_ends_inclusive,
        method="bfill",
    )

    gap_info = pd.DataFrame(
        {
            "start_time": gap_starts,
            "end_time": gap_ends,
            "start_inclusive": gap_starts_inclusive,
            "end_inclusive": gap_ends_inclusive,
            "gap_size_in_seconds": gap_ends - gap_starts,
            "value_to_left": left_values,
            "value_to_right": right_values,
            "mean_left_right": (
                np.mean((left_values, right_values), axis=0)
                if pd.api.types.is_numeric_dtype(constricted_timeseries_with_bounds) is True
                else None
            ),
        }
    )

    gap_info["gap_size_in_seconds"] = gap_info["gap_size_in_seconds"].dt.total_seconds()

    return gap_info


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "timeseries": {"data_type": "SERIES"},
        "interval_start_timestamp": {"data_type": "STRING", "default_value": None},
        "interval_end_timestamp": {"data_type": "STRING", "default_value": None},
        "auto_frequency_determination": {"data_type": "BOOLEAN", "default_value": True},
        "auto_freq_percentile": {"data_type": "FLOAT", "default_value": 0.5},
        "auto_freq_min_amount_datapoints": {"data_type": "INT", "default_value": 11},
        "expected_data_frequency": {"data_type": "STRING", "default_value": None},
        "expected_data_freq_allowed_variance_factor": {
            "data_type": "FLOAT",
            "default_value": 1.0,
        },
        "expected_data_frequency_offset": {
            "data_type": "STRING",
            "default_value": None,
        },
        "externally_determined_gap_timestamps": {
            "data_type": "SERIES",
            "default_value": None,
        },
        "externally_determined_gap_intervals": {
            "data_type": "DATAFRAME",
            "default_value": None,
        },
        "deactivate_freq_based_gap_detection": {
            "data_type": "BOOLEAN",
            "default_value": False,
        },
    },
    "outputs": {
        "gap_info": {"data_type": "DATAFRAME"},
        "data_frequency": {"data_type": "STRING"},
    },
    "name": "Gap Detection Intervals",
    "category": "Data Quality",
    "description": "Detects gaps in the given timeseries that are larger than the expected data frequency and returns a DataFrame with information about the gaps.",  # noqa: E501
    "version_tag": "1.0.0",
    "id": "cd2a8b7f-a1af-4630-89a5-738af595472a",
    "revision_group_id": "415662ab-e4fb-4084-b752-80433d0df291",
    "state": "RELEASED",
    "released_timestamp": "2024-02-15T14:00:16.393911+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(
    *,
    timeseries,
    interval_start_timestamp=None,
    interval_end_timestamp=None,
    auto_frequency_determination=True,
    auto_freq_percentile=0.5,
    auto_freq_min_amount_datapoints=11,
    expected_data_frequency=None,
    expected_data_freq_allowed_variance_factor=1.0,
    expected_data_frequency_offset=None,
    externally_determined_gap_timestamps=parse_default_value(
        COMPONENT_INFO, "externally_determined_gap_timestamps"
    ),
    externally_determined_gap_intervals=parse_default_value(
        COMPONENT_INFO, "externally_determined_gap_intervals"
    ),
    deactivate_freq_based_gap_detection=False,
):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    if interval_start_timestamp is None:
        if "ref_interval_start_timestamp" in timeseries.attrs:
            interval_start_timestamp = timeseries.attrs["ref_interval_start_timestamp"]
        elif "from" in timeseries.attrs:
            interval_start_timestamp = timeseries.attrs["from"]

    if interval_end_timestamp is None:
        if "ref_interval_end_timestamp" in timeseries.attrs:
            interval_end_timestamp = timeseries.attrs["ref_interval_end_timestamp"]
        elif "to" in timeseries.attrs:
            interval_end_timestamp = timeseries.attrs["to"]

    if expected_data_frequency is None and "ref_data_frequency" in timeseries.attrs:
        expected_data_frequency = timeseries.attrs["ref_data_frequency"]
        freqstr2timedelta(expected_data_frequency, 'timeseries.attrs["ref_data_frequency"]')
        auto_frequency_determination = False

    if expected_data_frequency_offset is None and "ref_data_frequency_offset" in timeseries.attrs:
        expected_data_frequency_offset = timeseries.attrs["ref_data_frequency_offset"]
        freqstr2timedelta(
            expected_data_frequency_offset,
            'timeseries.attrs["ref_data_frequency_offset"]',
        )
        auto_frequency_determination = False

    input_params = GapDetectionParameters(
        timeseries=timeseries,
        interval_start_timestamp_str=interval_start_timestamp,
        interval_end_timestamp_str=interval_end_timestamp,
        auto_frequency_determination=auto_frequency_determination,
        percentile=auto_freq_percentile,
        min_amount_datapoints=auto_freq_min_amount_datapoints,
        expected_data_frequency_str=expected_data_frequency,
        expected_data_frequency_factor=expected_data_freq_allowed_variance_factor,
        expected_data_frequency_offset_str=expected_data_frequency_offset,
        externally_determined_gap_timestamps=externally_determined_gap_timestamps,
        externally_determined_gap_intervals=externally_determined_gap_intervals,
    )

    constricted_timeseries_without_bounds = constrict_series_to_interval(
        input_params.timeseries,
        input_params.interval_start_timestamp,
        input_params.interval_end_timestamp,
    )

    constricted_timeseries_with_bounds = add_boundary_timestamps_and_sort(
        constricted_timeseries_without_bounds,
        input_params.interval_start_timestamp,
        input_params.interval_end_timestamp,
    )

    constricted_externally_determined_gap_timestamp_intervals = (
        constricted_gap_timestamps_to_intervals(
            constrict_series_to_interval(
                input_params.externally_determined_gap_timestamps,
                input_params.interval_start_timestamp,
                input_params.interval_end_timestamp,
            ),
        )
        if input_params.externally_determined_gap_timestamps is not None
        else no_gap_intervals
    )

    constricted_externally_determined_gap_intervals = (
        constrict_intervals_df_to_interval(
            input_params.externally_determined_gap_intervals,
            input_params.interval_start_timestamp,
            input_params.interval_end_timestamp,
        )
        if input_params.externally_determined_gap_intervals is not None
        else no_gap_intervals
    )

    if deactivate_freq_based_gap_detection is True:
        return {
            "gap_info": get_gap_intervals_info(
                constricted_timeseries_with_bounds,
                [
                    constricted_externally_determined_gap_intervals,
                    constricted_externally_determined_gap_timestamp_intervals,
                ],
            )
        }

    if auto_frequency_determination:
        check_amount_datapoints(
            series=constricted_timeseries_with_bounds,
            min_amount_datapoints=input_params.min_amount_datapoints,
        )
        input_params.expected_data_frequency = determine_expected_data_frequency(
            constricted_timeseries_with_bounds, auto_freq_percentile
        )

    normalized_intervals_df = determine_normalized_interval_sizes(
        constricted_timeseries_with_bounds, input_params.expected_data_frequency
    )

    identified_gaps_df = identify_gaps(
        normalized_intervals_df,
        expected_data_freq_allowed_variance_factor,
    )

    gaps_from_missing_expected_datapoints = identify_gaps_from_missing_expected_datapoints(
        constricted_timeseries_without_bounds=constricted_timeseries_without_bounds,
        interval_start_timestamp=input_params.interval_start_timestamp,
        interval_end_timestamp=input_params.interval_end_timestamp,
        expected_data_frequency=input_params.expected_data_frequency,
        expected_data_frequency_offset=input_params.expected_data_frequency_offset,
    )

    return {
        "gap_info": get_gap_intervals_info(
            constricted_timeseries_with_bounds,
            [
                identified_gaps_df,
                constricted_externally_determined_gap_intervals,
                constricted_externally_determined_gap_timestamp_intervals,
                gaps_from_missing_expected_datapoints,
            ],
        ),
        "data_frequency": pd.tseries.frequencies.to_offset(
            input_params.expected_data_frequency
        ).freqstr,
    }


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "timeseries",
            "filters": {
                "value": '{\n    "2020-01-01T01:16:00.000Z": 10.0,\n    "2020-01-01T01:18:00.000Z": 10.0,\n    "2020-01-01T01:19:00.000Z": 10.0,\n    "2020-01-01T01:20:00.000Z": 10.0,\n    "2020-01-01T01:22:00.000Z": 20.0,\n    "2020-01-01T01:23:00.000Z": 20.0,\n    "2020-01-01T01:25:00.000Z": 20.0,\n    "2020-01-01T08:28:00.000Z": 20.0,\n    "2020-01-01T08:30:00.000Z": 30.0,\n    "2020-01-01T08:31:00.000Z": 30.0,\n    "2020-01-01T16:34:00.000Z": 30.0\n}'
            },
        }
    ]
}
RELEASE_WIRING = {
    "input_wirings": [
        {
            "workflow_input_name": "timeseries",
            "filters": {
                "value": '{\n    "2020-01-01T01:16:00.000Z": 10.0,\n    "2020-01-01T01:18:00.000Z": 10.0,\n    "2020-01-01T01:19:00.000Z": 10.0,\n    "2020-01-01T01:20:00.000Z": 10.0,\n    "2020-01-01T01:22:00.000Z": 20.0,\n    "2020-01-01T01:23:00.000Z": 20.0,\n    "2020-01-01T01:25:00.000Z": 20.0,\n    "2020-01-01T08:28:00.000Z": 20.0,\n    "2020-01-01T08:30:00.000Z": 30.0,\n    "2020-01-01T08:31:00.000Z": 30.0,\n    "2020-01-01T16:34:00.000Z": 30.0\n}'
            },
        }
    ]
}

"""Documentation for component "Replacement Locations for Gaps"

# Replacement Locations for Gaps

## Description
Determine timestamps at which replacement values need to be determined.

## Inputs

- **gap_intervals** (DataFrame):
  Expects Pandas DataFrame with columns "start_time", "end_time", "start_inclusive", "end_inclusive,
  which all have a datatime64 dtype.

- **timeseries** (Series, default value: null):
  Expects Pandas Series with index of datatype DateTimeIndex.

- **interval_start_timestamp** (String, default value: null):
  Desired start timestamp of the processing range. Expexcts ISO 8601 format.
  Alternatively, the **timeseries** can have metadata in the Pandas object's `.attrs` entry with key
  "ref_interval_start_timestamp" (or "from") that will be used if no **interval_start_timestamp** is
  provided.
  If neither is defined, the processing range begins with the first data point in **timeseries**.
  The start timestamp must not be later than the end timestamp.

- **interval_end_timestamp** (String, default value: null):
  Desired end timestamp of the processing range. Expexcts ISO 8601 format.
  Alternatively, the **timeseries** can have metadata in the Pandas object's `.attrs` entry with key
  "ref_interval_end_timestamp" (or "to") that will be used if no **interval_end_timestamp** is
  provided.
  If neither is defined, the processing range ends with the last data point in **timeseries**.
  The start timestamp must not be later than the end timestamp.

- **auto_frequency_determination** (Boolean, default value: false):
  If true, the function will automatically determine the expected data frequency based on the
  **timeseries** index, thus **timeseries** must be provided but **expected_data_frequency** must
  not be set.
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
  **auto_frequency_determination** is false or **timeseries** is null.
  The expected time difference between consecutive timestamps in the input **timeseries**. Must be a
  [date offset aliases](
    https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#timeseries-offset-aliases
  ) or a timedelta string, e.g. "D" or "60s".
  Alternatively, the **timeseries** can have metadata in the Pandas object's `.attrs` entry with key
  "ref_data_frequency" that will be used if no **expected_data_frequency** is provided.
  In that case **auto_frequency_determination** will be set to false.

- **expected_data_frequency_offset** (String, default value: null):
  Must not be set if **auto_frequency_determination** is true or the **expected_data_frequency**
  is not set.
  The time difference between the reference time  1970-01-01 00:00:00 and the timestamps of the
  input **timeseries** with the provided expected data frequency. Must be a
  [date offset aliases](
    https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#timeseries-offset-aliases
  ) or a timedelta string, e.g. "D" or "60s".

- **all_gap_points** (Boolean, default value: true):
  If set to true, all gap intervals of size 0 are added to the replacement locations without
  checking whether they correspond to the pattern defined by frequency and frequency offset.

## Outputs
- **replacement_locations** (Series):
  A Pandas Series with the replacement location timestamps as index and NaN values.

## Details

Defining the time points of a periodic timeseries requires specifying both the data
frequency and the offset by which the timestamps are shifted.

If **auto_frequency_determination** is set to true, the expected data frequency is determined using
the **auto_freq_percentile**-th quantile of the time intervals between consecutive datapoints in
**timeseries**.
If **auto_frequency_determination** is set to false, the expected data frequency must be provided by
the input **expected_data_frequency**.

If no **expected_data_frequency_offset** is specified, the data frequency offset is determine by
using either the timestamp of the first datapoint of the timeseries within the specified time
interval or, if the time series is empty, the **interval_start_timestamp**.
If neither value is specified, the start timestamp of each gap is used.
Depending on the gaps, the replacement locations might then be shifted against each other.

## Examples
The minimal valid JSON input contains just **gap_intervals** and **expected_data_frequency**, e.g.:
```json
{
    "gap_intervals": [
        {
            "start_time": "2020-01-01T01:16:30.000Z",
            "end_time": "2020-01-01T01:25:30.000Z",
            "start_inclusive": true,
            "end_inclusive": true
        },
        {
            "start_time": "2020-01-01T01:29:30.000Z",
            "end_time": "2020-01-01T01:29:30.000Z",
            "start_inclusive": true,
            "end_inclusive": true
        },
        {
            "start_time": "2020-01-01T01:31:30.000Z",
            "end_time": "2020-01-01T01:34:30.000Z",
            "start_inclusive": false,
            "end_inclusive": true
        }
    ],
    "expected_data_frequency": "2min",
}
```
This results in the output:
```json
{
    "__hd_wrapped_data_object__": "SERIES",
    "__metadata__": {},
    "__data__": {
        "2020-01-01T01:16:30.000Z": null,
        "2020-01-01T01:18:30.000Z": null,
        "2020-01-01T01:20:30.000Z": null,
        "2020-01-01T01:22:30.000Z": null,
        "2020-01-01T01:24:30.000Z": null,
        "2020-01-01T01:29:30.000Z": null,
        "2020-01-01T01:32:30.000Z": null,
        "2020-01-01T01:34:30.000Z": null
    }
}
```
Providing additionally **expected_data_frequency_offset** shifts the output timestamps to the
specified pattern. For example the value "0s" yields the output:
```json
{
    "__hd_wrapped_data_object__": "SERIES",
    "__metadata__": {},
    "__data__": {
        "2020-01-01T01:18:00.000Z": null,
        "2020-01-01T01:20:00.000Z": null,
        "2020-01-01T01:22:00.000Z": null,
        "2020-01-01T01:24:00.000Z": null,
        "2020-01-01T01:29:30.000Z": null,
        "2020-01-01T01:32:00.000Z": null,
        "2020-01-01T01:34:00.000Z": null
    }
}
```
The same input, but with **all_gap_points** set to false, would result in almost the same output in
both cases, but without the timestamp "2020-01-01T01:29:30.000Z", since it does not match the
pattern.

Examples illustrating the input parameters used to automatically determine the frequency from the
timeseries can be found in the documentation of the "Gap Detection Intervals" component.
"""

import numpy as np
import pandas as pd
from pydantic import BaseModel, validator

from hdutils import ComponentInputValidationException


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
                f"The {input_name} cannot be parsed as Pandas Timedelta: {str(err)}",
                error_code=422,
                invalid_component_inputs=[input_name],
            ) from err


class GapDetectionParameters(BaseModel, arbitrary_types_allowed=True):
    gap_intervals: pd.DataFrame
    timeseries: pd.Series | None
    interval_start_timestamp_str: str | None
    interval_start_timestamp: pd.Timestamp | None = None
    interval_end_timestamp_str: str | None
    interval_end_timestamp: pd.Timestamp | None = None
    auto_frequency_determination: bool
    percentile: float
    min_amount_datapoints: int
    expected_data_frequency_str: str | None
    expected_data_frequency: pd.Timedelta | None = None
    expected_data_frequency_offset_str: str | None = None
    expected_data_frequency_offset: pd.Timedelta | None = None
    externally_determined_gap_timestamps: pd.Series | None

    @validator("timeseries")
    def timeseries_index_has_datetime_dtype(cls, timeseries: pd.Series | None) -> pd.Series | None:
        if timeseries is None:
            return timeseries
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
            if (
                "timeseries" in values
                and values["timeseries"] is not None
                and len(values["timeseries"]) > 0
            ):
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
            if (
                "timeseries" in values
                and values["timeseries"] is not None
                and len(values["timeseries"]) > 0
            ):
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

    @validator("expected_data_frequency_str", always=True)
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
    def get_expected_data_frequency_from_expected_data_frequency_str(
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
    def get_expected_data_frequency_offset_from_expected_data_frequency_offset_str(
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

    @validator("gap_intervals")
    def check_required_gap_intervals_columns_are_present(
        cls, gap_intervals: pd.DataFrame | None
    ) -> pd.DataFrame | None:
        if gap_intervals is None:
            return None

        required_column_names = {
            "start_time",
            "end_time",
            "start_inclusive",
            "end_inclusive",
        }

        if not required_column_names.issubset(set(gap_intervals.columns)):
            column_names_string = ", ".join(gap_intervals.columns)
            required_column_names_string = ", ".join(required_column_names)
            raise ComponentInputValidationException(
                f"The column names {column_names_string} of `gap_intervals` "
                f"don't contain the required columns {required_column_names_string}.",
                error_code=422,
                invalid_component_inputs=["gap_intervals"],
            )

        return gap_intervals

    @validator("gap_intervals")
    def check_gap_intervals_columns_have_datetime_dtype(
        cls, gap_intervals: pd.DataFrame | None
    ) -> pd.DataFrame | None:
        if gap_intervals is None:
            return None

        required_datetime64_column_names = ["start_time", "end_time"]

        if not any(
            pd.api.types.is_datetime64_any_dtype(column_dtype)
            for column_dtype in gap_intervals[required_datetime64_column_names].dtypes
        ):
            required_column_names_string = ", ".join(required_datetime64_column_names)
            raise ComponentInputValidationException(
                f"At least one of the required columns {required_column_names_string} "
                "is not of any datetime64 dtype.",
                error_code=422,
                invalid_component_inputs=["gap_intervals"],
            )
        return gap_intervals

    @validator("gap_intervals")
    def check_gap_intervals_start_before_end(
        cls, gap_intervals: pd.DataFrame | None
    ) -> pd.DataFrame | None:
        if gap_intervals is None:
            return None

        invalid_gap_intervals = gap_intervals[
            gap_intervals["start_time"] > gap_intervals["end_time"]
        ]

        if len(invalid_gap_intervals) > 0:
            raise ComponentInputValidationException(
                "There is at least one gap interval for which the start is after the end:\n"
                + invalid_gap_intervals.to_json(date_format="iso", indent=2),
                error_code=422,
                invalid_component_inputs=["gap_intervals"],
            )
        return gap_intervals


def constrict_series_to_interval(
    timeseries: pd.Series | None,
    interval_start_timestamp: pd.Timestamp | None,
    interval_end_timestamp: pd.Timestamp | None,
) -> pd.Series | None:
    if timeseries is None:
        return None

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
    timeseries_with_bounds: pd.Series | None,
    interval_start_timestamp: pd.Timestamp | None,
    interval_end_timestamp: pd.Timestamp | None,
) -> pd.Series | None:
    if timeseries_with_bounds is None:
        return None

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


interval_inclusive_from_boundaries_inclusive = {
    (True, True): "both",
    (False, False): "neither",
    (True, False): "left",
    (False, True): "right",
}


def generate_replacement_locations(
    gap_intervals: pd.DataFrame,
    data_frequency: pd.Timedelta,
    data_frequency_offset: pd.Timedelta | None,
    all_gap_points: bool,
) -> pd.Series:
    replacement_locations = pd.DatetimeIndex([])
    for gap_start_time, gap_end_time, gap_start_inclusive, gap_end_inclusive in zip(
        gap_intervals["start_time"],
        gap_intervals["end_time"],
        gap_intervals["start_inclusive"],
        gap_intervals["end_inclusive"],
        strict=True,
    ):
        if all_gap_points and gap_start_time == gap_end_time:
            replacement_locations = replacement_locations.append(pd.DatetimeIndex([gap_start_time]))
        else:
            if data_frequency_offset is None:
                data_frequency_offset = gap_start_time
            replacement_start = shift_timestamp_to_the_right_onto_rhythm(
                gap_start_time, data_frequency, data_frequency_offset
            )
            replacement_end = shift_timestamp_to_the_left_onto_rhythm(
                gap_end_time, data_frequency, data_frequency_offset
            )
            replacement_locations = replacement_locations.append(
                pd.date_range(
                    start=replacement_start,
                    end=replacement_end,
                    freq=data_frequency,
                    inclusive=interval_inclusive_from_boundaries_inclusive[
                        gap_start_inclusive | (replacement_start != gap_start_time),
                        gap_end_inclusive | (replacement_end != gap_end_time),
                    ],
                )
            )

    return pd.Series(index=replacement_locations)


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


def determine_expected_data_frequency_offset(
    constricted_timeseries_without_bounds: pd.Series | None,
    interval_start_timestamp: pd.Timestamp,
) -> pd.Timedelta | None:
    reference_timestamp = pd.Timestamp("1970-01-01", tz="utc")

    if (
        constricted_timeseries_without_bounds is not None
        and len(constricted_timeseries_without_bounds) > 0
    ):
        return reference_timestamp - constricted_timeseries_without_bounds.index[0]

    if interval_start_timestamp is not None:
        return reference_timestamp - interval_start_timestamp

    return None


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "gap_intervals": {"data_type": "DATAFRAME"},
        "timeseries": {"data_type": "SERIES", "default_value": None},
        "interval_start_timestamp": {"data_type": "STRING", "default_value": None},
        "interval_end_timestamp": {"data_type": "STRING", "default_value": None},
        "auto_frequency_determination": {
            "data_type": "BOOLEAN",
            "default_value": False,
        },
        "auto_freq_percentile": {"data_type": "FLOAT", "default_value": 0.5},
        "auto_freq_min_amount_datapoints": {"data_type": "INT", "default_value": 11},
        "expected_data_frequency": {"data_type": "STRING", "default_value": None},
        "expected_data_frequency_offset": {
            "data_type": "STRING",
            "default_value": None,
        },
        "all_gap_points": {"data_type": "BOOLEAN", "default_value": True},
    },
    "outputs": {
        "replacement_locations": {"data_type": "SERIES"},
    },
    "name": "Replacement Locations for Gaps",
    "category": "Data Quality",
    "description": "Determine timestamps at which replacement values need to be determined.",
    "version_tag": "1.0.0",
    "id": "ccf45f3a-8cbe-4269-8f3c-5d56d80db29a",
    "revision_group_id": "fd0f4cce-9a6e-48d2-8d10-5a2a1310f6c6",
    "state": "RELEASED",
    "released_timestamp": "2024-02-15T14:27:23.783017+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(
    *,
    gap_intervals,
    timeseries=parse_default_value(COMPONENT_INFO, "timeseries"),
    interval_start_timestamp=None,
    interval_end_timestamp=None,
    auto_frequency_determination=False,
    auto_freq_percentile=0.5,
    auto_freq_min_amount_datapoints=11,
    expected_data_frequency=None,
    expected_data_frequency_offset=None,
    all_gap_points=True,
):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    if timeseries is not None:
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

        if (
            expected_data_frequency_offset is None
            and "ref_data_frequency_offset" in timeseries.attrs
        ):
            expected_data_frequency_offset = timeseries.attrs["ref_data_frequency_offset"]
            freqstr2timedelta(
                expected_data_frequency_offset,
                'timeseries.attrs["ref_data_frequency_offset"]',
            )
            auto_frequency_determination = False

    input_params = GapDetectionParameters(
        gap_intervals=gap_intervals,
        timeseries=timeseries,
        interval_start_timestamp_str=interval_start_timestamp,
        interval_end_timestamp_str=interval_end_timestamp,
        auto_frequency_determination=auto_frequency_determination,
        percentile=auto_freq_percentile,
        min_amount_datapoints=auto_freq_min_amount_datapoints,
        expected_data_frequency_str=expected_data_frequency,
        expected_data_frequency_offset_str=expected_data_frequency_offset,
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

    if auto_frequency_determination:
        check_amount_datapoints(
            series=constricted_timeseries_with_bounds,
            min_amount_datapoints=input_params.min_amount_datapoints,
        )
        input_params.expected_data_frequency = determine_expected_data_frequency(
            constricted_timeseries_with_bounds, auto_freq_percentile
        )

    if input_params.expected_data_frequency_offset is None:
        input_params.expected_data_frequency_offset = determine_expected_data_frequency_offset(
            constricted_timeseries_without_bounds,
            input_params.interval_start_timestamp,
        )

    # The offset might still be None
    if input_params.expected_data_frequency_offset is not None:
        input_params.expected_data_frequency_offset = (
            input_params.expected_data_frequency_offset % input_params.expected_data_frequency
        )

    constricted_gap_intervals = (
        constrict_intervals_df_to_interval(
            input_params.gap_intervals,
            input_params.interval_start_timestamp,
            input_params.interval_end_timestamp,
        )
        if input_params.gap_intervals is not None
        else no_gap_intervals
    )

    merged_gap_intervals = merge_intervals(constricted_gap_intervals)

    replacement_locations = generate_replacement_locations(
        merged_gap_intervals,
        input_params.expected_data_frequency,
        input_params.expected_data_frequency_offset,
        all_gap_points,
    )

    return {"replacement_locations": replacement_locations}


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "gap_intervals",
            "filters": {
                "value": '[\n    {\n        "start_time": "2020-01-01T01:16:00.000Z",\n        "end_time": "2020-01-01T01:25:00.000Z",\n        "start_inclusive": true,\n        "end_inclusive": true\n    },\n    {\n        "start_time": "2020-01-01T01:29:00.000Z",\n        "end_time": "2020-01-01T01:29:00.000Z",\n        "start_inclusive": true,\n        "end_inclusive": true\n    },\n    {\n        "start_time": "2020-01-01T01:31:00.000Z",\n        "end_time": "2020-01-01T01:34:00.000Z",\n        "start_inclusive": false,\n        "end_inclusive": true\n    }\n]\n'
            },
        },
        {
            "workflow_input_name": "expected_data_frequency",
            "filters": {"value": "2min"},
        },
    ]
}
RELEASE_WIRING = {
    "input_wirings": [
        {
            "workflow_input_name": "gap_intervals",
            "filters": {
                "value": '[\n    {\n        "start_time": "2020-01-01T01:16:00.000Z",\n        "end_time": "2020-01-01T01:25:00.000Z",\n        "start_inclusive": true,\n        "end_inclusive": true\n    },\n    {\n        "start_time": "2020-01-01T01:29:00.000Z",\n        "end_time": "2020-01-01T01:29:00.000Z",\n        "start_inclusive": true,\n        "end_inclusive": true\n    },\n    {\n        "start_time": "2020-01-01T01:31:00.000Z",\n        "end_time": "2020-01-01T01:34:00.000Z",\n        "start_inclusive": false,\n        "end_inclusive": true\n    }\n]\n'
            },
        },
        {
            "workflow_input_name": "expected_data_frequency",
            "filters": {"value": "2min"},
        },
    ]
}

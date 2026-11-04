"""Documentation for Aggregate Time Series in Moving Window

# Aggregate Time Series in Moving Window

## Description
This component calculates aggregation values on fixed time windows that move
over the data in a regular rhythm.

## Inputs
* **timeseries** (Pandas Series): Series to perform the moving window aggregation on.
* **aggregator** (String, default value: "mean"): Aggregation function to
  apply in each window. Must be one of "mean", "median", "min", "max", or
  "std".
* **min_periods** (Integer, default value: 1): Minimum number of valid values
  in a window required to return an aggregation result. If fewer values are
  present, the result is `NaN`.
* **window_size** (String, default value: "15min"): Time span covered by each
  window. Can be either a Pandas frequency string based on [date offset
  aliases](https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#timeseries-offset-aliases)
  or a timedelta string.
* **window_frequency** (String, default value: "5min"): Time span between two
  consecutive window starts. For directly consecutive, non-overlapping windows
  set **window_frequency** to the same value as **window_size**.
* **frequency_offset** (String, default value: "0min"): Optional shift of the
  complete window rhythm. In most cases no shift is needed, so the default is
  `"0min"`.
* **interval_type** (String, default value: "left_closed"): Controls whether
  values exactly on a window edge belong to the window or not.
  Supported values are "left_closed", "right_open", "right_closed",
  "left_open", "closed", and "open".
  In practice:
  - `left_closed` / `right_open`: left edge included, right edge excluded
  - `right_closed` / `left_open`: right edge included, left edge excluded
  - `closed`: both edges included
  - `open`: both edges excluded
* **label_position** (String, default value: "left"): Determines which
  timestamp represents each window in the result. Must be one of "left",
  "center", or "right". For non-fixed calendar windows such as monthly or
  quarterly windows, `center` is not supported.

## Outputs
* **window_values** (Pandas Series): Series with the calculated aggregation values of each window.

## Details
1. The component checks the configuration and maps `interval_type` to the internal window boundary mode.
2. It converts the time settings (`window_size`, `window_frequency`, `frequency_offset`) to pandas time objects.
3. The input series is sorted by timestamp to ensure a stable and deterministic calculation order.
4. A regular window rhythm is built from `window_frequency` and
   `frequency_offset`.
5. If the settings allow it, a fast `resample` path is used. Otherwise, a
   general `rolling` path is used.
6. For each window, the selected `aggregator` is calculated.
7. If a window has fewer than `min_periods` valid values, its aggregation
   result is set to `NaN`.
8. The output labels are placed at the `left`, `center`, or `right` of the
   window according to `label_position`.
9. The component returns the aggregated series (`window_values`).

## Examples
The json input of a typical call of this component is
```
{
    "timeseries": {
        "2025-12-06 23:17:14+00:00": 14.360453,
        "2025-12-06 23:18:14+00:00": 14.872439,
        "2025-12-06 23:19:14+00:00": 15.803046,
        "2025-12-06 23:20:14+00:00": 13.661063,
        "2025-12-06 23:21:14+00:00": 14.969653,
        "2025-12-06 23:22:14+00:00": 13.530460,
        "2025-12-06 23:23:14+00:00": 14.009814,
        "2025-12-06 23:24:14+00:00": 13.708907,
        "2025-12-06 23:25:14+00:00": 15.119281,
        "2025-12-06 23:26:14+00:00": 15.666053,
        "2025-12-06 23:27:14+00:00": 15.488811,
        "2025-12-06 23:28:14+00:00": 15.515572,
        "2025-12-06 23:29:14+00:00": 14.767891,
        "2025-12-06 23:30:14+00:00": 13.726783,
        "2025-12-06 23:31:14+00:00": 14.997352,
        "2025-12-06 23:32:14+00:00": 13.015161,
        "2025-12-06 23:33:14+00:00": 15.079884,
        "2025-12-06 23:34:14+00:00": 15.001638,
        "2025-12-06 23:35:14+00:00": 16.035476,
        "2025-12-06 23:36:14+00:00": 14.545874,
        "2025-12-06 23:37:14+00:00": 13.970260,
        "2025-12-06 23:38:14+00:00": 15.045999,
        "2025-12-06 23:39:14+00:00": 13.824304,
        "2025-12-06 23:40:14+00:00": 13.620449,
        "2025-12-06 23:41:14+00:00": 15.146005,
        "2025-12-06 23:42:14+00:00": 14.796941,
        "2025-12-06 23:43:14+00:00": 17.036046,
        "2025-12-06 23:44:14+00:00": 14.976151,
        "2025-12-06 23:45:14+00:00": 14.637615,
        "2025-12-06 23:46:14+00:00": 15.195011,
        "2025-12-06 23:47:14+00:00": 14.082022,
        "2025-12-06 23:48:14+00:00": 15.311653,
        "2025-12-06 23:49:14+00:00": 15.534084,
        "2025-12-06 23:50:14+00:00": 15.020099,
        "2025-12-06 23:51:14+00:00": 14.020416,
        "2025-12-06 23:52:14+00:00": 13.779699,
        "2025-12-06 23:53:14+00:00": 14.407253,
        "2025-12-06 23:54:14+00:00": 15.180839,
        "2025-12-06 23:55:14+00:00": 14.618573,
        "2025-12-06 23:56:14+00:00": 14.194774,
        "2025-12-06 23:57:14+00:00": 14.653221,
        "2025-12-06 23:58:14+00:00": 14.911146,
        "2025-12-06 23:59:14+00:00": 14.951289,
        "2025-12-07 00:00:14+00:00": 15.005731,
        "2025-12-07 00:01:14+00:00": 15.708401,
        "2025-12-07 00:02:14+00:00": 13.605439,
        "2025-12-07 00:03:14+00:00": 14.620927,
        "2025-12-07 00:04:14+00:00": 15.181250,
        "2025-12-07 00:05:14+00:00": 13.912724,
        "2025-12-07 00:06:14+00:00": 14.060204
    },
    "window_size": "15min",
    "window_frequency": "5min",
    "frequency_offset": "0min",
    "interval_type": "left_closed",
    "aggregator": "mean",
    "min_periods": 1,
    "label_position": "left"
}
```
The expected output is
```
"window_values": {
    "2025-12-06T23:05:00.000Z": 15.0119793333,
    "2025-12-06T23:10:00.000Z": 14.364479375,
    "2025-12-06T23:15:00.000Z": 14.7287263846,
    "2025-12-06T23:20:00.000Z": 14.5505548667,
    "2025-12-06T23:25:00.000Z": 14.7866892667,
    "2025-12-06T23:30:00.000Z": 14.7212215333,
    "2025-12-06T23:35:00.000Z": 14.9171926667,
    "2025-12-06T23:40:00.000Z": 14.8496188667,
    "2025-12-06T23:45:00.000Z": 14.6998462667,
    "2025-12-06T23:50:00.000Z": 14.6572704667,
    "2025-12-06T23:55:00.000Z": 14.6186399167,
    "2025-12-07T00:00:00.000Z": 14.5849537143,
    "2025-12-07T00:05:00.000Z": 13.986464
},
```
"""

from typing import Literal

import numpy as np
import pandas as pd

from hdutils import ComponentInputValidationException


def freqstr2dateoffset(freqstr: str) -> pd.DateOffset:
    """Transform frequency string to Pandas DateOffset."""
    return pd.tseries.frequencies.to_offset(freqstr)


def freqstr2timedelta(freqstr: str) -> pd.Timedelta:
    """Transform frequency string to Pandas Timedelta."""
    try:
        return pd.to_timedelta(freqstr)
    except ValueError:
        return pd.to_timedelta(freqstr2dateoffset(freqstr))


def is_fixed_frequency(offset: pd.DateOffset) -> bool:
    """Return True if a pandas offset represents a fixed duration."""
    try:
        _ = offset.nanos
        return True
    except ValueError:
        return False


def shift_timestamp_to_the_left_onto_rhythm(
    timestamp: pd.Timestamp,
    window_frequency: pd.DateOffset,
    frequency_offset: pd.Timedelta,
) -> pd.Timestamp:
    """Shift a timestamp to the left in the rhythm.

    The parameters window_frequency and frequency_offset define a kind of "rhythm".
    For example a window_frequency of "5min" and a frequency_offset of "1min" define the
    rhythm which contains all timestamps, where the minutes are 01, 06, 11, 16, and so on.
    The provided timestamp is shifted to the left onto the closest timestamp of this rhythm.

    Conveniently, the Pandas class Timestamp comes with a method `floor`, which is similar to
    the mathematical method `floor`, but instead of a decimal place takes into account the
    specified frequency.

    It is not completely obvious how the frequency_offset needs to be taken into account so that the
    shifted timestamp actually lies in the desired interval:
        timestamp - window_frequency < shifted <= timestamp
    so in the following a little proof is provided:

    On the one hand we have:
        frequency_offset < window_frequency
        shifted = (timestamp - frequency_offset).floor(freq=window_frequency) + frequency_offset
    <-> shifted - frequency_offset = (timestamp - frequency_offset).floor(freq=window_frequency)
                                  <=  timestamp - frequency_offset
     -> shifted <= timestamp

    On the other hand:
        shifted - frequency_offset = (timestamp - frequency_offset).floor(freq=window_frequency)
                                   >  timestamp - frequency_offset - window_frequency
     -> shifted > timestamp - window_frequency
    """
    return (timestamp - frequency_offset).floor(freq=window_frequency) + frequency_offset


def shift_timestamp_to_the_right_onto_rhythm(
    timestamp: pd.Timestamp,
    window_frequency: pd.DateOffset,
    frequency_offset: pd.Timedelta,
) -> pd.Timestamp:
    """Shift a timestamp to the right in the rhythm.

    The parameters window_frequency and frequency_offset define a kind of "rhythm".
    The specified timestamp is shifted to the right onto the closest timestamp of this rhythm.

    Conveniently, the Pandas class Timestamp has a method `ceil` that is similar to the
    mathematical method `ceil`, but instead of a decimal place, it takes into account the
    specified frequency.

    It is not completely obvious how the frequency_offset must be taken into account so that
    the shifted timestamp actually lies in the desired interval:
        timestamp <= shifted < timestamp + window_frequency
    The proof that the implemented code fulfills this requirement is analogous to the one for
    `shift_timestamp_to_the_left_in_rhythm`.
    """
    return (timestamp - frequency_offset).ceil(freq=window_frequency) + frequency_offset


def right_window_edge_from_left_window_edge(
    left_window_edge: pd.Timestamp, window_size: pd.DateOffset
) -> pd.Timestamp:
    return left_window_edge + window_size


def determine_right_window_edges(
    first_index: pd.Timestamp,
    last_index: pd.Timestamp,
    window_size: pd.DateOffset,
    window_frequency: pd.DateOffset,
    frequency_offset: pd.Timedelta,
) -> pd.DatetimeIndex:
    """Determine right window edges of all windows containing first_index and last_index.

    This function determines the right edges of the windows for which the mean shall be calculated.

    The parameters window_frequency and frequency_offset define an endless "rhythm" where left
    edges of windows should be located. From first_index and last_index the left edges of earliest
    and latest window containing these timestamps are determined. Using the window_size left window
    edges are transformed to right window edges. Finally the list of all right window edges is
    determined and returned.

    The right edges are determined because the Pandas rolling method only offers the possibility to
    operate on windows that center around the current point or on windows for which the current
    point is the right edge.
    """
    earliest_possible_left_edge_of_window_containing_first_index = first_index - window_size
    first_window_left_edge = shift_timestamp_to_the_right_onto_rhythm(
        timestamp=earliest_possible_left_edge_of_window_containing_first_index,
        window_frequency=window_frequency,
        frequency_offset=frequency_offset,
    )
    first_window_right_boundary = right_window_edge_from_left_window_edge(
        left_window_edge=first_window_left_edge, window_size=window_size
    )

    latest_possible_left_edge_of_window_containing_last_index = last_index
    last_window_left_boundary = shift_timestamp_to_the_left_onto_rhythm(
        timestamp=latest_possible_left_edge_of_window_containing_last_index,
        window_frequency=window_frequency,
        frequency_offset=frequency_offset,
    )
    last_window_right_boundary = right_window_edge_from_left_window_edge(
        left_window_edge=last_window_left_boundary, window_size=window_size
    )

    return pd.date_range(
        start=first_window_right_boundary,
        end=last_window_right_boundary,
        freq=window_frequency,
        inclusive="both",
    )


def calculate_moving_time_window(
    timeseries: pd.Series,
    window_size: pd.DateOffset,
    window_frequency: pd.DateOffset,
    frequency_offset: pd.Timedelta,
    inclusive: Literal["left", "right", "both", "neither"],
    label_position: Literal["left", "center", "right"],
    aggregator: Literal["mean", "median", "min", "max", "std"],
) -> tuple[pd.Series, pd.Series]:
    """Calculate periodically shifting window aggregates for a constant time window.

    timeseries (Pandas Series): Series to perform the periodically shifting time window
        calculation on.
    window_size (Pandas DateOffset): Time span of each window.
    window_frequency (Pandas DateOffset): Frequency of windows for which the aggregation is calculated,
        i.e. time delta between the start (or end) of each two consecutive windows.
        For directly consecutive, non-overlapping windows set window_frequency to the same value as
        window_size. If the window_frequency is smaller than the window_size the windows will
        overlap. If the window_frequency is larger than the window_size, there will be gaps between
        each two successive windows.
    frequency_offset (Pandas Timedelta): Offset of the window starts compared to
        1970-01-01 00:00:00. In most cases no offset is necessary, so this can be set to zero,
        i.e. "0".
    inclusive (string): One of "left", "right", "both", or "neither".
        In case a datapoint is on the left or right border of a window this option
        determines if it belongs to that window or not, but potentially a neighbouring window.
    label_position (string): The string must be either "left", "center", or "right".
        This option determines which timestamp is provided to represent the window for the
        corresponding aggregation in the output time series.

    To reduce the runtime, the Pandas function resample is used when possible
    (window_frequency and window_size are identical and inclusive is "left" or "right").
    Otherwise, the Pandas function rolling is used.
    """
    timeseries = timeseries.sort_index()

    frequency_offset = frequency_offset % window_frequency

    if window_size == window_frequency and inclusive in ["left", "right"]:
        # resample is the fastest method, if it can be used
        resampled = timeseries.resample(
            rule=window_size,
            closed=inclusive,
            label="right",
            origin="epoch",
            offset=frequency_offset,
        )
        result = getattr(resampled, aggregator)()
        counts = resampled.count()
    else:
        # default label position in rolling is right
        # left is  not possible, only alternative is center
        right_window_boundaries = determine_right_window_edges(
            first_index=timeseries.index[0],
            last_index=timeseries.index[-1],
            window_size=window_size,
            window_frequency=window_frequency,
            frequency_offset=frequency_offset,
        )

        reindexed_timeseries = timeseries.reindex(
            index=right_window_boundaries.union(timeseries.index)
        )

        rolling_obj = reindexed_timeseries.rolling(window_size.freqstr, closed=inclusive)
        result = getattr(rolling_obj, aggregator)()
        counts = rolling_obj.count()

        result = result.reindex(index=right_window_boundaries)
        counts = counts.reindex(index=right_window_boundaries)

    if label_position == "center":
        result = result.shift(freq=-pd.to_timedelta(window_size) / 2)
        counts = counts.shift(freq=-pd.to_timedelta(window_size) / 2)
    elif label_position == "left":
        result = result.shift(freq=-pd.to_timedelta(window_size))
        counts = counts.shift(freq=-pd.to_timedelta(window_size))

    return result, counts


def validate_inputs(
    timeseries: pd.Series,
    aggregator: str,
    min_periods,
    window_size: str,
    window_frequency: str,
    frequency_offset: str,
    interval_type: str,
    label_position: str,
) -> tuple[int, pd.DateOffset, pd.DateOffset, pd.Timedelta]:
    if not isinstance(timeseries, pd.Series):
        raise ComponentInputValidationException(
            "timeseries must be a pandas Series.",
            error_code="422",
            invalid_component_inputs=["timeseries"],
        )
    if not isinstance(timeseries.index, pd.DatetimeIndex):
        raise ComponentInputValidationException(
            "timeseries index must be a pandas DatetimeIndex.",
            error_code="422",
            invalid_component_inputs=["timeseries"],
        )
    if timeseries.empty:
        raise ComponentInputValidationException(
            "timeseries must not be empty.",
            error_code="422",
            invalid_component_inputs=["timeseries"],
        )
    if not pd.api.types.is_numeric_dtype(timeseries):
        raise ComponentInputValidationException(
            "timeseries values must be numeric.",
            error_code="422",
            invalid_component_inputs=["timeseries"],
        )
    finite_mask = np.isfinite(timeseries.dropna().to_numpy(dtype=float))
    if not finite_mask.all():
        raise ComponentInputValidationException(
            "timeseries values must be finite numbers.",
            error_code="422",
            invalid_component_inputs=["timeseries"],
        )

    allowed_aggregators = {"mean", "median", "min", "max", "std"}
    if aggregator not in allowed_aggregators:
        raise ComponentInputValidationException(
            "aggregator must be one of: mean, median, min, max, std",
            error_code="422",
            invalid_component_inputs=["aggregator"],
        )

    allowed_interval_types = {
        "closed",
        "open",
        "left_closed",
        "right_open",
        "right_closed",
        "left_open",
    }
    if interval_type not in allowed_interval_types:
        raise ComponentInputValidationException(
            "interval_type must be one of: closed, open, left_closed, right_open, right_closed, left_open",
            error_code="422",
            invalid_component_inputs=["interval_type"],
        )

    if label_position not in {"left", "center", "right"}:
        raise ComponentInputValidationException(
            "label_position must be one of: left, center, right",
            error_code="422",
            invalid_component_inputs=["label_position"],
        )

    if isinstance(min_periods, str):
        min_periods = min_periods.strip()
        if not min_periods.isdigit():
            raise ComponentInputValidationException(
                "min_periods must be an integer >= 1.",
                error_code="422",
                invalid_component_inputs=["min_periods"],
            )
        min_periods = int(min_periods)
    if not isinstance(min_periods, int) or min_periods < 1:
        raise ComponentInputValidationException(
            "min_periods must be an integer >= 1.",
            error_code="422",
            invalid_component_inputs=["min_periods"],
        )

    try:
        window_size_offset = freqstr2dateoffset(window_size)
    except Exception as exc:
        raise ComponentInputValidationException(
            "window_size must be a valid positive frequency string.",
            error_code="422",
            invalid_component_inputs=["window_size"],
        ) from exc

    try:
        window_frequency_offset = freqstr2dateoffset(window_frequency)
    except Exception as exc:
        raise ComponentInputValidationException(
            "window_frequency must be a valid positive frequency string.",
            error_code="422",
            invalid_component_inputs=["window_frequency"],
        ) from exc

    try:
        frequency_offset_delta = freqstr2timedelta(frequency_offset)
    except Exception as exc:
        raise ComponentInputValidationException(
            "frequency_offset must be a valid timedelta/frequency string.",
            error_code="422",
            invalid_component_inputs=["frequency_offset"],
        ) from exc

    reference_ts = pd.Timestamp("1970-01-01T00:00:00Z")
    if not (reference_ts + window_size_offset > reference_ts):
        raise ComponentInputValidationException(
            "window_size must represent a positive duration.",
            error_code="422",
            invalid_component_inputs=["window_size"],
        )
    if not (reference_ts + window_frequency_offset > reference_ts):
        raise ComponentInputValidationException(
            "window_frequency must represent a positive duration.",
            error_code="422",
            invalid_component_inputs=["window_frequency"],
        )

    if label_position == "center" and not is_fixed_frequency(window_size_offset):
        raise ComponentInputValidationException(
            "label_position='center' is only supported for fixed-duration windows such as '15min', '1h', or '7D'.",
            error_code="422",
            invalid_component_inputs=["label_position", "window_size"],
        )

    return (
        min_periods,
        window_size_offset,
        window_frequency_offset,
        frequency_offset_delta,
    )


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "timeseries": {"data_type": "SERIES"},
        "aggregator": {"data_type": "STRING", "default_value": "mean"},
        "min_periods": {"data_type": "INT", "default_value": 1},
        "window_size": {"data_type": "STRING", "default_value": "15min"},
        "window_frequency": {"data_type": "STRING", "default_value": "5min"},
        "frequency_offset": {"data_type": "STRING", "default_value": "0min"},
        "interval_type": {"data_type": "STRING", "default_value": "left_closed"},
        "label_position": {"data_type": "STRING", "default_value": "left"},
    },
    "outputs": {
        "window_values": {"data_type": "SERIES"},
    },
    "name": "Aggregate Time Series in Moving Window",
    "category": "Time Series Base Components",
    "description": "Calculate moving time window aggregation values.",
    "version_tag": "1.0.0",
    "id": "12bb2c56-2adc-4c5d-bdaf-9c39ea247cd7",
    "revision_group_id": "f1642f90-cc86-48f9-8feb-50e750204d40",
    "state": "RELEASED",
    "released_timestamp": "2026-05-11T06:00:00+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(
    *,
    timeseries,
    aggregator="mean",
    min_periods=1,
    window_size="15min",
    window_frequency="5min",
    frequency_offset="0min",
    interval_type="left_closed",
    label_position="left",
):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # Step 1: Map the user-facing interval type to the internal pandas mode.
    inclusive_string_from_interval_type = {
        "closed": "both",
        "open": "neither",
        "left_closed": "left",
        "right_open": "left",
        "right_closed": "right",
        "left_open": "right",
    }

    # Step 2: Validate inputs and convert time settings to pandas objects.
    (
        min_periods,
        window_size_offset,
        window_frequency_offset,
        frequency_offset_delta,
    ) = validate_inputs(
        timeseries=timeseries,
        aggregator=aggregator,
        min_periods=min_periods,
        window_size=window_size,
        window_frequency=window_frequency,
        frequency_offset=frequency_offset,
        interval_type=interval_type,
        label_position=label_position,
    )

    # Step 3: Calculate window aggregates and valid-value counts.
    window_values, valid_value_counts = calculate_moving_time_window(
        timeseries=timeseries,
        window_size=window_size_offset,
        window_frequency=window_frequency_offset,
        frequency_offset=frequency_offset_delta,
        inclusive=inclusive_string_from_interval_type[interval_type],
        label_position=label_position,
        aggregator=aggregator,
    )

    # Step 4: Apply the minimum valid-value requirement per window.
    window_values = window_values.where(valid_value_counts >= min_periods)

    # Step 5: Return the aggregated output series.
    return {
        "window_values": window_values,
    }


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "timeseries",
            "filters": {
                "value": '{\n    "2025-12-06 23:17:14+00:00": 14.360453,\n    "2025-12-06 23:18:14+00:00": 14.872439,\n    "2025-12-06 23:19:14+00:00": 15.803046,\n    "2025-12-06 23:20:14+00:00": 13.661063,\n    "2025-12-06 23:21:14+00:00": 14.969653,\n    "2025-12-06 23:22:14+00:00": 13.530460,\n    "2025-12-06 23:23:14+00:00": 14.009814,\n    "2025-12-06 23:24:14+00:00": 13.708907,\n    "2025-12-06 23:25:14+00:00": 15.119281,\n    "2025-12-06 23:26:14+00:00": 15.666053,\n    "2025-12-06 23:27:14+00:00": 15.488811,\n    "2025-12-06 23:28:14+00:00": 15.515572,\n    "2025-12-06 23:29:14+00:00": 14.767891,\n    "2025-12-06 23:30:14+00:00": 13.726783,\n    "2025-12-06 23:31:14+00:00": 14.997352,\n    "2025-12-06 23:32:14+00:00": 13.015161,\n    "2025-12-06 23:33:14+00:00": 15.079884,\n    "2025-12-06 23:34:14+00:00": 15.001638,\n    "2025-12-06 23:35:14+00:00": 16.035476,\n    "2025-12-06 23:36:14+00:00": 14.545874,\n    "2025-12-06 23:37:14+00:00": 13.970260,\n    "2025-12-06 23:38:14+00:00": 15.045999,\n    "2025-12-06 23:39:14+00:00": 13.824304,\n    "2025-12-06 23:40:14+00:00": 13.620449,\n    "2025-12-06 23:41:14+00:00": 15.146005,\n    "2025-12-06 23:42:14+00:00": 14.796941,\n    "2025-12-06 23:43:14+00:00": 17.036046,\n    "2025-12-06 23:44:14+00:00": 14.976151,\n    "2025-12-06 23:45:14+00:00": 14.637615,\n    "2025-12-06 23:46:14+00:00": 15.195011,\n    "2025-12-06 23:47:14+00:00": 14.082022,\n    "2025-12-06 23:48:14+00:00": 15.311653,\n    "2025-12-06 23:49:14+00:00": 15.534084,\n    "2025-12-06 23:50:14+00:00": 15.020099,\n    "2025-12-06 23:51:14+00:00": 14.020416,\n    "2025-12-06 23:52:14+00:00": 13.779699,\n    "2025-12-06 23:53:14+00:00": 14.407253,\n    "2025-12-06 23:54:14+00:00": 15.180839,\n    "2025-12-06 23:55:14+00:00": 14.618573,\n    "2025-12-06 23:56:14+00:00": 14.194774,\n    "2025-12-06 23:57:14+00:00": 14.653221,\n    "2025-12-06 23:58:14+00:00": 14.911146,\n    "2025-12-06 23:59:14+00:00": 14.951289,\n    "2025-12-07 00:00:14+00:00": 15.005731,\n    "2025-12-07 00:01:14+00:00": 15.708401,\n    "2025-12-07 00:02:14+00:00": 13.605439,\n    "2025-12-07 00:03:14+00:00": 14.620927,\n    "2025-12-07 00:04:14+00:00": 15.181250,\n    "2025-12-07 00:05:14+00:00": 13.912724,\n    "2025-12-07 00:06:14+00:00": 14.060204\n}'
            },
        }
    ]
}
RELEASE_WIRING = {
    "input_wirings": [
        {
            "workflow_input_name": "timeseries",
            "filters": {
                "value": '{\n    "2025-12-06 23:17:14+00:00": 14.360453,\n    "2025-12-06 23:18:14+00:00": 14.872439,\n    "2025-12-06 23:19:14+00:00": 15.803046,\n    "2025-12-06 23:20:14+00:00": 13.661063,\n    "2025-12-06 23:21:14+00:00": 14.969653,\n    "2025-12-06 23:22:14+00:00": 13.530460,\n    "2025-12-06 23:23:14+00:00": 14.009814,\n    "2025-12-06 23:24:14+00:00": 13.708907,\n    "2025-12-06 23:25:14+00:00": 15.119281,\n    "2025-12-06 23:26:14+00:00": 15.666053,\n    "2025-12-06 23:27:14+00:00": 15.488811,\n    "2025-12-06 23:28:14+00:00": 15.515572,\n    "2025-12-06 23:29:14+00:00": 14.767891,\n    "2025-12-06 23:30:14+00:00": 13.726783,\n    "2025-12-06 23:31:14+00:00": 14.997352,\n    "2025-12-06 23:32:14+00:00": 13.015161,\n    "2025-12-06 23:33:14+00:00": 15.079884,\n    "2025-12-06 23:34:14+00:00": 15.001638,\n    "2025-12-06 23:35:14+00:00": 16.035476,\n    "2025-12-06 23:36:14+00:00": 14.545874,\n    "2025-12-06 23:37:14+00:00": 13.970260,\n    "2025-12-06 23:38:14+00:00": 15.045999,\n    "2025-12-06 23:39:14+00:00": 13.824304,\n    "2025-12-06 23:40:14+00:00": 13.620449,\n    "2025-12-06 23:41:14+00:00": 15.146005,\n    "2025-12-06 23:42:14+00:00": 14.796941,\n    "2025-12-06 23:43:14+00:00": 17.036046,\n    "2025-12-06 23:44:14+00:00": 14.976151,\n    "2025-12-06 23:45:14+00:00": 14.637615,\n    "2025-12-06 23:46:14+00:00": 15.195011,\n    "2025-12-06 23:47:14+00:00": 14.082022,\n    "2025-12-06 23:48:14+00:00": 15.311653,\n    "2025-12-06 23:49:14+00:00": 15.534084,\n    "2025-12-06 23:50:14+00:00": 15.020099,\n    "2025-12-06 23:51:14+00:00": 14.020416,\n    "2025-12-06 23:52:14+00:00": 13.779699,\n    "2025-12-06 23:53:14+00:00": 14.407253,\n    "2025-12-06 23:54:14+00:00": 15.180839,\n    "2025-12-06 23:55:14+00:00": 14.618573,\n    "2025-12-06 23:56:14+00:00": 14.194774,\n    "2025-12-06 23:57:14+00:00": 14.653221,\n    "2025-12-06 23:58:14+00:00": 14.911146,\n    "2025-12-06 23:59:14+00:00": 14.951289,\n    "2025-12-07 00:00:14+00:00": 15.005731,\n    "2025-12-07 00:01:14+00:00": 15.708401,\n    "2025-12-07 00:02:14+00:00": 13.605439,\n    "2025-12-07 00:03:14+00:00": 14.620927,\n    "2025-12-07 00:04:14+00:00": 15.181250,\n    "2025-12-07 00:05:14+00:00": 13.912724,\n    "2025-12-07 00:06:14+00:00": 14.060204\n}'
            },
        }
    ]
}

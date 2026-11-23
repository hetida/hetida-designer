"""Documentation for Integrate Time Series

# Integrate Time Series

## Description
Component to integrate a time series on a datetime axis. It supports irregular
sampling, optional periodic resets, and can return either the cumulative
integrated series or one sum per period.

## Inputs
- **timeseries** (Pandas Series):
    The input time series. The index must contain timestamps, and the values
    must be numeric.
- **output_mode** (String, default value: "series_integrated"):
    Selects which result series the component returns.
    - `series_integrated`: returns the cumulative integrated series.
    - `period_sums`: returns one sum per reset period. If `reset` is `null`,
      one total sum for the whole series is returned and indexed by the first
      timestamp of the input series.
- **method** (String, default value: "trapezoidal"):
    Integration method. Must be one of `"trapezoidal"`, `"rectangle_left"`, or
    `"rectangle_right"`.
    - `trapezoidal`: assumes the value changes linearly between two timestamps.
      This is a good default for smooth signals.
    - `rectangle_left`: uses the left value for the whole interval until the
      next timestamp.
    - `rectangle_right`: uses the right value for the whole interval and applies
      it backward to the interval.
- **gap_handling** (String, default value: "break"):
    Controls how missing values are handled during integration.
    - `break`: does not integrate across intervals that contain missing values.
      This is the safer default.
    - `ignore`: skips missing observations and integrates between the remaining
      valid points. This is a more aggressive option because it connects valid
      datapoints across gaps.
- **max_gap** (String, default value: null):
    Optional maximum time gap allowed for integration across two neighboring
    valid timestamps. If the time difference is larger than this value, the
    interval is skipped. Use a fixed timedelta string such as `2h`, `30min`,
    or `1D`, or `null` to disable this check.
- **reset** (String, default value: null):
    Optional reset period for the cumulative output. Must be one of `hourly`,
    `daily`, `weekly`, `monthly`, `yearly`, or `null`.
- **time_unit** (String, default value: "h"):
    Time unit used to scale the time differences during integration. Must be one
    of `s`, `min`, `h`, or `d`.
    For example, if the values are in `kW` and `time_unit="h"`, the integrated
    output is in `kWh`.

## Outputs
- **result_series** (Pandas Series):
    The selected result series. Depending on `output_mode`, this is either the
    cumulative integrated series or the period sums. For
    `output_mode="series_integrated"`, additional timestamps can appear at reset
    boundaries if an integration interval crosses such a boundary.

## Details
1. The input series is sorted by time and duplicate timestamps are merged by mean.
2. Depending on `gap_handling`, missing values are either treated as hard
   breaks or skipped during integration.
3. If `max_gap` is set, intervals larger than this threshold are skipped even
   if both endpoint values are valid.
4. The integral is calculated interval by interval on the datetime axis using
   the selected `method`.
5. The `time_unit` input scales the time differences, for example to hours when
   converting power to energy.
6. If `reset` is set, intervals that cross a period boundary are split so that
   the cumulative result can be represented correctly across the boundary. This
   can add extra timestamps at reset boundaries in
   `output_mode="series_integrated"` if no original datapoint exists exactly at
   that boundary.
7. If `output_mode="period_sums"`, one sum per reset period is returned.
   Without a reset, one total sum for the whole series is returned and indexed
   by the first timestamp of the input series.
8. If the series should first be put on a regular time grid or missing
   timestamps should be handled explicitly, use `handle_gaps_and_missing_data`
   upstream and keep `gap_handling="break"` here.

## Example
```json
{
  "timeseries": {
    "2026-03-01T20:00:00Z": 5.0,
    "2026-03-01T21:00:00Z": 5.5,
    "2026-03-01T22:00:00Z": 5.2,
    "2026-03-01T23:00:00Z": null,
    "2026-03-02T00:00:00Z": 6.0,
    "2026-03-02T01:00:00Z": 5.8,
    "2026-03-02T02:00:00Z": 6.1,
    "2026-03-02T03:00:00Z": 5.9,
    "2026-03-02T04:00:00Z": 6.1,
    "2026-03-02T05:00:00Z": 5.8,
    "2026-03-02T06:00:00Z": 5.6,
    "2026-03-02T07:00:00Z": 5.5,
    "2026-03-02T08:00:00Z": 5.7
  },
  "output_mode": "series_integrated",
  "method": "trapezoidal",
  "gap_handling": "break",
  "max_gap": "2h",
  "reset": "daily",
  "time_unit": "h"
}
```

Expected output:
```json
{
  "result_series": {
    "2026-03-01T20:00:00Z": 0.0,
    "2026-03-01T21:00:00Z": 5.25,
    "2026-03-01T22:00:00Z": 10.6,
    "2026-03-01T23:00:00Z": 10.6,
    "2026-03-02T00:00:00Z": 0.0,
    "2026-03-02T01:00:00Z": 5.9,
    "2026-03-02T02:00:00Z": 11.85,
    "2026-03-02T03:00:00Z": 17.85,
    "2026-03-02T04:00:00Z": 23.85,
    "2026-03-02T05:00:00Z": 29.8,
    "2026-03-02T06:00:00Z": 35.5,
    "2026-03-02T07:00:00Z": 41.05,
    "2026-03-02T08:00:00Z": 46.65
  }
}
```

Second example with period sums:
```json
{
  "timeseries": {
    "2026-03-01T20:00:00Z": 5.0,
    "2026-03-01T21:00:00Z": 5.5,
    "2026-03-01T22:00:00Z": 5.2,
    "2026-03-01T23:00:00Z": null,
    "2026-03-02T00:00:00Z": 6.0,
    "2026-03-02T01:00:00Z": 5.8,
    "2026-03-02T02:00:00Z": 6.1,
    "2026-03-02T03:00:00Z": 5.9,
    "2026-03-02T04:00:00Z": 6.1,
    "2026-03-02T05:00:00Z": 5.8,
    "2026-03-02T06:00:00Z": 5.6,
    "2026-03-02T07:00:00Z": 5.5,
    "2026-03-02T08:00:00Z": 5.7
  },
  "output_mode": "period_sums",
  "method": "trapezoidal",
  "gap_handling": "break",
  "max_gap": "2h",
  "reset": "daily",
  "time_unit": "h"
}
```

Expected output:
```json
{
  "result_series": {
    "2026-03-01T00:00:00Z": 10.6,
    "2026-03-02T00:00:00Z": 46.65
  }
}
```

Notes:
- `gap_handling="break"` is the recommended default when missing values should
  stop the integration.
- `gap_handling="ignore"` should only be used intentionally, because it
  connects valid datapoints across gaps.
- If `reset` is active and an interval crosses a reset boundary, the cumulative
  output can contain an additional timestamp exactly at that boundary so that
  the reset is represented correctly.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from hdutils import ComponentInputValidationException

TIME_UNIT_IN_SECONDS = {
    "s": 1.0,
    "min": 60.0,
    "h": 3600.0,
    "d": 86400.0,
}


def parse_fixed_timedelta_string(value: str, input_name: str) -> pd.Timedelta:
    try:
        offset = pd.tseries.frequencies.to_offset(value)
    except ValueError as exc:
        raise ComponentInputValidationException(
            f"{input_name} must be a valid fixed timedelta string like '30min', '2h', or '1D'",
            error_code="422",
            invalid_component_inputs=[input_name],
        ) from exc

    try:
        nanos = offset.nanos
    except ValueError as exc:
        raise ComponentInputValidationException(
            f"{input_name} must be a fixed timedelta string like '30min', '2h', or '1D'",
            error_code="422",
            invalid_component_inputs=[input_name],
        ) from exc

    return pd.to_timedelta(nanos, unit="ns")


def validate_inputs(
    timeseries: pd.Series,
    output_mode: str,
    method: str,
    gap_handling: str,
    max_gap: str | None,
    reset: str | None,
    time_unit: str,
) -> pd.Timedelta | None:
    if not isinstance(timeseries, pd.Series):
        raise ComponentInputValidationException(
            "timeseries must be a pandas Series",
            error_code="422",
            invalid_component_inputs=["timeseries"],
        )
    if timeseries.empty:
        raise ComponentInputValidationException(
            "timeseries must not be empty",
            error_code="422",
            invalid_component_inputs=["timeseries"],
        )
    if not pd.api.types.is_datetime64_any_dtype(timeseries.index):
        raise ComponentInputValidationException(
            "timeseries index must be datetime",
            error_code="422",
            invalid_component_inputs=["timeseries"],
        )
    if not pd.api.types.is_numeric_dtype(timeseries):
        raise ComponentInputValidationException(
            "timeseries values must be numeric",
            error_code="422",
            invalid_component_inputs=["timeseries"],
        )
    if not np.isfinite(timeseries.dropna().to_numpy(dtype=float)).all():
        raise ComponentInputValidationException(
            "timeseries must not contain inf or -inf values",
            error_code="422",
            invalid_component_inputs=["timeseries"],
        )
    if timeseries.dropna().empty:
        raise ComponentInputValidationException(
            "timeseries must contain at least one non-missing numeric value",
            error_code="422",
            invalid_component_inputs=["timeseries"],
        )
    if method not in {"trapezoidal", "rectangle_left", "rectangle_right"}:
        raise ComponentInputValidationException(
            "method must be one of 'trapezoidal', 'rectangle_left', 'rectangle_right'",
            error_code="422",
            invalid_component_inputs=["method"],
        )
    if gap_handling not in {"ignore", "break"}:
        raise ComponentInputValidationException(
            "gap_handling must be one of 'break', 'ignore'",
            error_code="422",
            invalid_component_inputs=["gap_handling"],
        )
    if max_gap is not None:
        if not isinstance(max_gap, str):
            raise ComponentInputValidationException(
                "max_gap must be null or a fixed timedelta string like '2h' or '30min'",
                error_code="422",
                invalid_component_inputs=["max_gap"],
            )
        normalized_max_gap = parse_fixed_timedelta_string(max_gap, "max_gap")
        if normalized_max_gap <= pd.Timedelta(0):
            raise ComponentInputValidationException(
                "max_gap must be greater than 0",
                error_code="422",
                invalid_component_inputs=["max_gap"],
            )
    else:
        normalized_max_gap = None
    if reset not in {None, "hourly", "daily", "weekly", "monthly", "yearly"}:
        raise ComponentInputValidationException(
            "reset must be one of null, 'hourly', 'daily', 'weekly', 'monthly', 'yearly'",
            error_code="422",
            invalid_component_inputs=["reset"],
        )
    if output_mode not in {"series_integrated", "period_sums"}:
        raise ComponentInputValidationException(
            "output_mode must be one of 'series_integrated', 'period_sums'",
            error_code="422",
            invalid_component_inputs=["output_mode"],
        )
    if time_unit not in TIME_UNIT_IN_SECONDS:
        raise ComponentInputValidationException(
            "time_unit must be one of 's', 'min', 'h', 'd'",
            error_code="422",
            invalid_component_inputs=["time_unit"],
        )
    return normalized_max_gap


def prepare_series(timeseries: pd.Series) -> pd.Series:
    prepared = timeseries.sort_index()
    if not prepared.index.is_unique:
        prepared = prepared.groupby(level=0).mean()
    return prepared


def build_integration_intervals(
    output_index: pd.DatetimeIndex,
    series: pd.Series,
    gap_handling: str,
    max_gap: pd.Timedelta | None,
) -> list[tuple[pd.Timestamp, pd.Timestamp, float, float]]:
    intervals: list[tuple[pd.Timestamp, pd.Timestamp, float, float]] = []
    if gap_handling == "ignore":
        valid_series = series.dropna()
        if len(valid_series) < 2:
            return intervals
        for i in range(1, len(valid_series)):
            ts0 = valid_series.index[i - 1]
            ts1 = valid_series.index[i]
            if max_gap is not None and (ts1 - ts0) > max_gap:
                continue
            v0 = float(valid_series.iloc[i - 1])
            v1 = float(valid_series.iloc[i])
            intervals.append((ts0, ts1, v0, v1))
        return intervals

    for i in range(1, len(output_index)):
        ts0 = output_index[i - 1]
        ts1 = output_index[i]
        if max_gap is not None and (ts1 - ts0) > max_gap:
            continue
        v0 = series.iloc[i - 1]
        v1 = series.iloc[i]
        if pd.isna(v0) or pd.isna(v1):
            continue
        intervals.append((ts0, ts1, float(v0), float(v1)))
    return intervals


def determine_period_start(timestamp: pd.Timestamp, reset: str | None) -> pd.Timestamp:
    if reset is None:
        return timestamp
    normalized = timestamp.normalize()
    if reset == "hourly":
        return timestamp.floor("h")
    if reset == "daily":
        return normalized
    if reset == "weekly":
        return normalized - pd.Timedelta(days=int(timestamp.weekday()))
    if reset == "monthly":
        return normalized.replace(day=1)
    return normalized.replace(month=1, day=1)


def determine_next_period_start(
    timestamp: pd.Timestamp,
    reset: str | None,
) -> pd.Timestamp:
    period_start = determine_period_start(timestamp, reset)
    if reset == "hourly":
        return period_start + pd.Timedelta(hours=1)
    if reset == "daily":
        return period_start + pd.Timedelta(days=1)
    if reset == "weekly":
        return period_start + pd.Timedelta(days=7)
    if reset == "monthly":
        return period_start + pd.offsets.MonthBegin(1)
    if reset == "yearly":
        return period_start + pd.offsets.YearBegin(1)
    return timestamp


def split_interval_at_reset_boundaries(
    start_timestamp: pd.Timestamp,
    end_timestamp: pd.Timestamp,
    reset: str | None,
) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    if reset is None:
        return [(start_timestamp, end_timestamp)]

    parts: list[tuple[pd.Timestamp, pd.Timestamp]] = []
    current_start = start_timestamp
    while current_start < end_timestamp:
        next_boundary = determine_next_period_start(current_start, reset)
        current_end = min(end_timestamp, next_boundary)
        parts.append((current_start, current_end))
        current_start = current_end
    return parts


def calculate_segment_area(
    interval_start: pd.Timestamp,
    interval_end: pd.Timestamp,
    start_value: float,
    end_value: float,
    segment_start: pd.Timestamp,
    segment_end: pd.Timestamp,
    method: str,
    time_unit: str,
) -> float:
    interval_seconds = (interval_end - interval_start).total_seconds()
    if interval_seconds <= 0:
        return 0.0

    segment_seconds = (segment_end - segment_start).total_seconds()
    if segment_seconds <= 0:
        return 0.0

    scale = TIME_UNIT_IN_SECONDS[time_unit]
    segment_duration = segment_seconds / scale

    if method == "rectangle_left":
        return start_value * segment_duration
    if method == "rectangle_right":
        return end_value * segment_duration

    start_fraction = (segment_start - interval_start).total_seconds() / interval_seconds
    end_fraction = (segment_end - interval_start).total_seconds() / interval_seconds
    value_at_segment_start = start_value + (end_value - start_value) * start_fraction
    value_at_segment_end = start_value + (end_value - start_value) * end_fraction
    return 0.5 * (value_at_segment_start + value_at_segment_end) * segment_duration


def initialize_period_sums(
    output_index: pd.DatetimeIndex,
    reset: str | None,
) -> dict[pd.Timestamp, float]:
    if len(output_index) == 0:
        return {}
    if reset is None:
        return {output_index[0]: 0.0}

    period_starts = [determine_period_start(ts, reset) for ts in output_index]
    unique_period_starts = pd.Index(period_starts).unique().sort_values()
    return {pd.Timestamp(ts): 0.0 for ts in unique_period_starts}


def calculate_integrated_series_and_period_sums(
    series: pd.Series,
    method: str,
    gap_handling: str,
    max_gap: pd.Timedelta | None,
    reset: str | None,
    time_unit: str,
) -> tuple[pd.Series, pd.Series]:
    original_index = series.index
    intervals = build_integration_intervals(original_index, series, gap_handling, max_gap)

    internal_boundary_timestamps: set[pd.Timestamp] = set()
    for interval_start, interval_end, _, _ in intervals:
        interval_parts = split_interval_at_reset_boundaries(interval_start, interval_end, reset)
        for _, part_end in interval_parts[:-1]:
            internal_boundary_timestamps.add(part_end)

    integrated_index = original_index.union(pd.DatetimeIndex(sorted(internal_boundary_timestamps)))
    incremental_area_at_timestamp = dict.fromkeys(integrated_index, 0.0)
    period_sums_by_period = initialize_period_sums(integrated_index, reset)

    for interval_start, interval_end, start_value, end_value in intervals:
        interval_parts = split_interval_at_reset_boundaries(interval_start, interval_end, reset)
        for part_start, part_end in interval_parts:
            part_area = calculate_segment_area(
                interval_start,
                interval_end,
                start_value,
                end_value,
                part_start,
                part_end,
                method,
                time_unit,
            )
            if reset is None:
                period_key = integrated_index[0]
            else:
                period_key = determine_period_start(part_start, reset)
            period_sums_by_period[period_key] = (
                period_sums_by_period.get(period_key, 0.0) + part_area
            )
            incremental_area_at_timestamp[part_end] = (
                incremental_area_at_timestamp.get(part_end, 0.0) + part_area
            )

    integrated_values = pd.Series(0.0, index=integrated_index, name="series_integrated")
    running_total = 0.0
    current_period_start: pd.Timestamp | None = None
    for timestamp in integrated_index:
        if timestamp in internal_boundary_timestamps:
            running_total += incremental_area_at_timestamp.get(timestamp, 0.0)
            integrated_values.loc[timestamp] = running_total
            running_total = 0.0
            current_period_start = determine_period_start(timestamp, reset)
            continue

        if reset is not None:
            timestamp_period_start = determine_period_start(timestamp, reset)
            if current_period_start is None or timestamp_period_start != current_period_start:
                running_total = 0.0
                current_period_start = timestamp_period_start
        running_total += incremental_area_at_timestamp.get(timestamp, 0.0)
        integrated_values.loc[timestamp] = running_total

    period_sums = pd.Series(period_sums_by_period, dtype=float, name="period_sums").sort_index()

    return integrated_values, period_sums


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "timeseries": {"data_type": "SERIES"},
        "output_mode": {"data_type": "STRING", "default_value": "series_integrated"},
        "method": {"data_type": "STRING", "default_value": "trapezoidal"},
        "gap_handling": {"data_type": "STRING", "default_value": "break"},
        "max_gap": {"data_type": "STRING", "default_value": None},
        "reset": {"data_type": "STRING", "default_value": None},
        "time_unit": {"data_type": "STRING", "default_value": "h"},
    },
    "outputs": {
        "result_series": {"data_type": "SERIES"},
    },
    "name": "Integrate Time Series",
    "category": "Time Series Base Components",
    "description": "Integrate a time series on a datetime axis.",
    "version_tag": "1.0.0",
    "id": "543ffb9a-07da-49b8-83f3-64202de91e54",
    "revision_group_id": "3f56cedc-4241-4ae3-be5c-b85c1987fded",
    "state": "RELEASED",
    "released_timestamp": "2026-05-11T06:00:00+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(
    *,
    timeseries,
    output_mode="series_integrated",
    method="trapezoidal",
    gap_handling="break",
    max_gap=None,
    reset=None,
    time_unit="h",
):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # Step 1: Validate the user inputs.
    normalized_max_gap = validate_inputs(
        timeseries,
        output_mode,
        method,
        gap_handling,
        max_gap,
        reset,
        time_unit,
    )

    # Step 2: Sort the input series and merge duplicate timestamps.
    prepared = prepare_series(timeseries)

    # Step 3: Calculate both possible result series.
    series_integrated, period_sums = calculate_integrated_series_and_period_sums(
        prepared,
        method,
        gap_handling,
        normalized_max_gap,
        reset,
        time_unit,
    )

    # Step 4: Select the configured result series.
    if output_mode == "series_integrated":
        result_series = series_integrated.rename("result_series")
    else:
        result_series = period_sums.rename("result_series")

    # Step 5: Return the selected output series.
    return {
        "result_series": result_series,
    }


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "timeseries",
            "filters": {
                "value": '{\n    "2026-03-01T20:00:00Z": 5.0,\n    "2026-03-01T21:00:00Z": 5.5,\n    "2026-03-01T22:00:00Z": 5.2,\n    "2026-03-01T23:00:00Z": null,\n    "2026-03-02T00:00:00Z": 6.0,\n    "2026-03-02T01:00:00Z": 5.8,\n    "2026-03-02T02:00:00Z": 6.1,\n    "2026-03-02T03:00:00Z": 5.9,\n    "2026-03-02T04:00:00Z": 6.1,\n    "2026-03-02T05:00:00Z": 5.8,\n    "2026-03-02T06:00:00Z": 5.6,\n    "2026-03-02T07:00:00Z": 5.5,\n    "2026-03-02T08:00:00Z": 5.7\n}'
            },
        }
    ]
}

RELEASE_WIRING = {
    "input_wirings": [
        {
            "workflow_input_name": "timeseries",
            "filters": {
                "value": '{\n    "2026-03-01T20:00:00Z": 5.0,\n    "2026-03-01T21:00:00Z": 5.5,\n    "2026-03-01T22:00:00Z": 5.2,\n    "2026-03-01T23:00:00Z": null,\n    "2026-03-02T00:00:00Z": 6.0,\n    "2026-03-02T01:00:00Z": 5.8,\n    "2026-03-02T02:00:00Z": 6.1,\n    "2026-03-02T03:00:00Z": 5.9,\n    "2026-03-02T04:00:00Z": 6.1,\n    "2026-03-02T05:00:00Z": 5.8,\n    "2026-03-02T06:00:00Z": 5.6,\n    "2026-03-02T07:00:00Z": 5.5,\n    "2026-03-02T08:00:00Z": 5.7\n}'
            },
        }
    ]
}

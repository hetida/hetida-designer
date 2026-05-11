"""Documentation for Differentiate Time Series

# Differentiate Time Series

## Description
Component to calculate either the difference or the rate of change between
neighboring timestamps of a time series on a datetime axis. It supports
irregular sampling, defensive gap handling, and an optional maximum allowed
time gap.

## Inputs
- **timeseries** (Pandas Series):
    The input time series. The index must contain timestamps, and the values
    must be numeric.
- **output_mode** (String, default value: "rate"):
    Selects which result is returned.
    - `rate`: returns the change per selected `time_unit`.
    - `difference`: returns the plain value difference between two neighboring
      used timestamps.
- **time_unit** (String, default value: "h"):
    Time unit used to scale the rate result. Must be one of `s`, `min`, `h`,
    or `d`.
    For example, if the values are in `kWh` and `time_unit="h"`, the rate
    output is in `kW`. For `output_mode="difference"`, this input has no
    effect.
- **gap_handling** (String, default value: "break"):
    Controls how missing values are handled during differentiation.
    - `break`: only use directly neighboring timestamps. If one of the two
      endpoint values is missing, no derivative result is created for that
      interval. This is the safer default.
    - `ignore`: skip missing observations and connect the remaining valid
      points. This is a more aggressive option because it differentiates across
      gaps.
- **max_gap** (String, default value: null):
    Optional maximum time gap allowed between two used timestamps. If the time
    difference is larger than this value, no result is created for that
    interval. Use a fixed timedelta string such as `2h`, `30min`, or `1D`, or
    `null` to disable this check.

## Outputs
- **result_series** (Pandas Series):
    The differentiated result series. Each result is placed on the right
    timestamp of the interval it was calculated from.

## Details
1. The input series is sorted by time and duplicate timestamps are merged by mean.
2. Depending on `gap_handling`, missing values are either treated as hard
   breaks or skipped when selecting point pairs.
3. If `max_gap` is set, intervals larger than this threshold are skipped even
   if both endpoint values are valid.
4. For `output_mode="difference"`, the component calculates `y_i - y_(i-1)`.
5. For `output_mode="rate"`, the component calculates `(y_i - y_(i-1)) / dt`
   and scales the result to the selected `time_unit`.
   For `output_mode="difference"`, `time_unit` is ignored.
6. The result of an interval is placed on the right timestamp of that interval.
7. If the series should first be put on a regular time grid, use
   `resample_time_series` upstream. If missing values should first be handled
   explicitly, use `handle_gaps_and_missing_data` upstream and keep
   `gap_handling="break"` here.

## Example
```json
{
  "timeseries": {
    "2026-03-01T00:00:00Z": 10.0,
    "2026-03-01T01:00:00Z": 11.0,
    "2026-03-01T02:00:00Z": 11.5,
    "2026-03-01T03:00:00Z": null,
    "2026-03-01T04:00:00Z": 15.5,
    "2026-03-01T05:00:00Z": 16.0
  },
  "output_mode": "rate",
  "time_unit": "h",
  "gap_handling": "break",
  "max_gap": "2h"
}
```

Expected output:
```json
{
  "result_series": {
    "2026-03-01T01:00:00Z": 1.0,
    "2026-03-01T02:00:00Z": 0.5,
    "2026-03-01T05:00:00Z": 0.5
  }
}
```

Second example with `difference` and `ignore`:
```json
{
  "timeseries": {
    "2026-03-01T00:00:00Z": 100.0,
    "2026-03-01T01:00:00Z": 101.0,
    "2026-03-01T02:00:00Z": null,
    "2026-03-01T03:00:00Z": 106.0,
    "2026-03-01T04:00:00Z": 108.0
  },
  "output_mode": "difference",
  "time_unit": "h",
  "gap_handling": "ignore",
  "max_gap": "3h"
}
```

Expected output:
```json
{
  "result_series": {
    "2026-03-01T01:00:00Z": 1.0,
    "2026-03-01T03:00:00Z": 5.0,
    "2026-03-01T04:00:00Z": 2.0
  }
}
```

Notes:
- `gap_handling="break"` is the recommended default when missing values should
  stop the differentiation.
- `gap_handling="ignore"` should only be used intentionally, because it
  connects valid datapoints across gaps.
- `max_gap` is useful if large time gaps should not produce a difference or
  rate, even when both endpoint values are valid.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from hdutils import ComponentInputValidationException, parse_default_value

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
    time_unit: str,
    gap_handling: str,
    max_gap: str | None,
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
    if timeseries.dropna().shape[0] < 2:
        raise ComponentInputValidationException(
            "timeseries must contain at least two non-missing numeric values",
            error_code="422",
            invalid_component_inputs=["timeseries"],
        )
    if output_mode not in {"rate", "difference"}:
        raise ComponentInputValidationException(
            "output_mode must be one of 'rate' or 'difference'",
            error_code="422",
            invalid_component_inputs=["output_mode"],
        )
    if time_unit not in TIME_UNIT_IN_SECONDS:
        raise ComponentInputValidationException(
            "time_unit must be one of 's', 'min', 'h', or 'd'",
            error_code="422",
            invalid_component_inputs=["time_unit"],
        )
    if gap_handling not in {"break", "ignore"}:
        raise ComponentInputValidationException(
            "gap_handling must be one of 'break' or 'ignore'",
            error_code="422",
            invalid_component_inputs=["gap_handling"],
        )

    parsed_max_gap = None
    if max_gap is not None:
        parsed_max_gap = parse_fixed_timedelta_string(max_gap, "max_gap")
        if parsed_max_gap <= pd.Timedelta(0):
            raise ComponentInputValidationException(
                "max_gap must be greater than zero",
                error_code="422",
                invalid_component_inputs=["max_gap"],
            )

    return parsed_max_gap


def prepare_series(timeseries: pd.Series) -> pd.Series:
    prepared = timeseries.sort_index()
    if not prepared.index.is_unique:
        prepared = prepared.groupby(level=0).mean()
    return prepared.astype(float)


def build_effective_series(series: pd.Series, gap_handling: str) -> pd.Series:
    if gap_handling == "ignore":
        return series.dropna()
    return series


def should_skip_interval(
    left_time: pd.Timestamp,
    right_time: pd.Timestamp,
    max_gap: pd.Timedelta | None,
) -> bool:
    if right_time <= left_time:
        return True
    if max_gap is None:
        return False
    return (right_time - left_time) > max_gap


def calculate_result_series(
    series: pd.Series,
    output_mode: str,
    time_unit: str,
    gap_handling: str,
    max_gap: pd.Timedelta | None,
) -> pd.Series:
    effective = build_effective_series(series, gap_handling)
    results: dict[pd.Timestamp, float] = {}
    scaling_seconds = TIME_UNIT_IN_SECONDS[time_unit]

    if gap_handling == "break":
        for idx in range(1, len(effective)):
            left_time = effective.index[idx - 1]
            right_time = effective.index[idx]
            left_value = effective.iloc[idx - 1]
            right_value = effective.iloc[idx]

            if pd.isna(left_value) or pd.isna(right_value):
                continue
            if should_skip_interval(left_time, right_time, max_gap):
                continue

            value_difference = float(right_value - left_value)
            if output_mode == "difference":
                results[right_time] = value_difference
            else:
                dt_seconds = (right_time - left_time).total_seconds()
                results[right_time] = value_difference / (dt_seconds / scaling_seconds)
    else:
        for idx in range(1, len(effective)):
            left_time = effective.index[idx - 1]
            right_time = effective.index[idx]
            left_value = float(effective.iloc[idx - 1])
            right_value = float(effective.iloc[idx])

            if should_skip_interval(left_time, right_time, max_gap):
                continue

            value_difference = right_value - left_value
            if output_mode == "difference":
                results[right_time] = value_difference
            else:
                dt_seconds = (right_time - left_time).total_seconds()
                results[right_time] = value_difference / (dt_seconds / scaling_seconds)

    if not results:
        return pd.Series(dtype=float, index=pd.DatetimeIndex([], dtype="datetime64[ns]"))
    return pd.Series(results, dtype=float)


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "timeseries": {"data_type": "SERIES"},
        "output_mode": {"data_type": "STRING", "default_value": "rate"},
        "time_unit": {"data_type": "STRING", "default_value": "h"},
        "gap_handling": {"data_type": "STRING", "default_value": "break"},
        "max_gap": {"data_type": "STRING", "default_value": None},
    },
    "outputs": {
        "result_series": {"data_type": "SERIES"},
    },
    "name": "Differentiate Time Series",
    "category": "Time Series Base Components",
    "description": "Calculate differences or rates of change on a datetime axis.",
    "version_tag": "1.0.0",
    "id": "2da73403-dfc7-4168-bbf4-324c4e6c97db",
    "revision_group_id": "0bc7b6d3-f607-4c7d-8c96-85188d09bdb1",
    "state": "RELEASED",
    "released_timestamp": "2026-05-11T08:00:00+02:00",
}


def main(
    *,
    timeseries,
    output_mode=parse_default_value(COMPONENT_INFO, "output_mode"),
    time_unit=parse_default_value(COMPONENT_INFO, "time_unit"),
    gap_handling=parse_default_value(COMPONENT_INFO, "gap_handling"),
    max_gap=parse_default_value(COMPONENT_INFO, "max_gap"),
):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # Step 1: Validate inputs and parse the optional maximum gap.
    parsed_max_gap = validate_inputs(
        timeseries,
        output_mode,
        time_unit,
        gap_handling,
        max_gap,
    )

    # Step 2: Sort the series and merge duplicate timestamps by mean.
    prepared = prepare_series(timeseries)

    # Step 3: Calculate the requested difference or rate series.
    result = calculate_result_series(
        prepared,
        output_mode,
        time_unit,
        gap_handling,
        parsed_max_gap,
    )

    # Step 4: Return the differentiated result series.
    return {
        "result_series": result,
    }


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "timeseries",
            "filters": {
                "value": '{\n    "2026-03-01T00:00:00Z": 10.0,\n    "2026-03-01T01:00:00Z": 11.0,\n    "2026-03-01T02:00:00Z": 11.5,\n    "2026-03-01T03:00:00Z": null,\n    "2026-03-01T04:00:00Z": 15.5,\n    "2026-03-01T05:00:00Z": 16.0\n}'
            },
        },
    ]
}

RELEASE_WIRING = {
    "input_wirings": [
        {
            "workflow_input_name": "timeseries",
            "filters": {
                "value": '{\n    "2026-03-01T00:00:00Z": 10.0,\n    "2026-03-01T01:00:00Z": 11.0,\n    "2026-03-01T02:00:00Z": 11.5,\n    "2026-03-01T03:00:00Z": null,\n    "2026-03-01T04:00:00Z": 15.5,\n    "2026-03-01T05:00:00Z": 16.0\n}'
            },
        },
    ]
}

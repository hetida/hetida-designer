"""Documentation for Detect Threshold Crossings in Time Series

# Detect Threshold Crossings in Time Series

## Description
Component to detect when a time series crosses a fixed threshold. It can detect
upward crossings, downward crossings, or both directions.

## Inputs
- **timeseries** (Pandas Series):
    The input time series. The index must contain timestamps, and the values
    must be numeric.
- **threshold** (Float):
    The threshold value to test against.
- **crossing_type** (String, default value: "both"):
    Selects which crossing direction is detected.
    - `upward`: detect crossings from below the threshold to above it.
    - `downward`: detect crossings from above the threshold to below it.
    - `both`: detect both directions.
- **inclusiveness** (String, default value: "strict"):
    Controls how equality to the threshold is treated.
    - `strict`: use strict comparisons.
    - `inclusive`: treat equality at the current timestamp as part of the
      crossing condition. For example, `8 -> 10` counts as an upward crossing,
      but `10 -> 11` does not.

## Outputs
- **crossing_mask** (Pandas Series):
    Bool series with `True` at detected crossing timestamps and `False`
    otherwise. A crossing is marked on the right timestamp of the interval in
    which the crossing becomes visible.

## Details
1. The input series is sorted by time and duplicate timestamps are merged by mean.
2. The component checks each pair of consecutive timestamps.
3. If one of the two endpoint values is missing, no crossing is emitted for
   that interval.
4. Depending on `crossing_type`, upward crossings, downward crossings, or both
   are detected.
5. Depending on `inclusiveness`, equality to the threshold is either ignored or
   treated as crossing-relevant at the current timestamp.
6. The crossing result of an interval is written to the right timestamp of that
   interval.

## Example
```json
{
  "timeseries": {
    "2026-03-01T00:00:00Z": 8.0,
    "2026-03-01T01:00:00Z": 9.5,
    "2026-03-01T02:00:00Z": 10.5,
    "2026-03-01T03:00:00Z": 11.0,
    "2026-03-01T04:00:00Z": 9.0
  },
  "threshold": 10.0,
  "crossing_type": "both",
  "inclusiveness": "strict"
}
```

Expected output:
```json
{
  "crossing_mask": {
    "2026-03-01T01:00:00Z": false,
    "2026-03-01T02:00:00Z": true,
    "2026-03-01T03:00:00Z": false,
    "2026-03-01T04:00:00Z": true
  }
}
```

Second example with `inclusive` upward detection:
```json
{
  "timeseries": {
    "2026-03-01T00:00:00Z": 8.0,
    "2026-03-01T01:00:00Z": 10.0,
    "2026-03-01T02:00:00Z": 10.0,
    "2026-03-01T03:00:00Z": 11.0
  },
  "threshold": 10.0,
  "crossing_type": "upward",
  "inclusiveness": "inclusive"
}
```

Expected output:
```json
{
  "crossing_mask": {
    "2026-03-01T01:00:00Z": true,
    "2026-03-01T02:00:00Z": false,
    "2026-03-01T03:00:00Z": false
  }
}
```
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from hdutils import ComponentInputValidationException, parse_default_value

CROSSING_TYPES = {"upward", "downward", "both"}
INCLUSIVENESS_MODES = {"strict", "inclusive"}


def validate_inputs(
    timeseries: pd.Series,
    threshold: float,
    crossing_type: str,
    inclusiveness: str,
) -> float:
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

    try:
        parsed_threshold = float(threshold)
    except (TypeError, ValueError) as exc:
        raise ComponentInputValidationException(
            "threshold must be a numeric value",
            error_code="422",
            invalid_component_inputs=["threshold"],
        ) from exc

    if not math.isfinite(parsed_threshold):
        raise ComponentInputValidationException(
            "threshold must be finite",
            error_code="422",
            invalid_component_inputs=["threshold"],
        )

    if crossing_type not in CROSSING_TYPES:
        raise ComponentInputValidationException(
            f"crossing_type must be one of {sorted(CROSSING_TYPES)}",
            error_code="422",
            invalid_component_inputs=["crossing_type"],
        )

    if inclusiveness not in INCLUSIVENESS_MODES:
        raise ComponentInputValidationException(
            f"inclusiveness must be one of {sorted(INCLUSIVENESS_MODES)}",
            error_code="422",
            invalid_component_inputs=["inclusiveness"],
        )

    return parsed_threshold


def prepare_series(timeseries: pd.Series) -> pd.Series:
    prepared = timeseries.sort_index()
    if not prepared.index.is_unique:
        prepared = prepared.groupby(level=0).mean()
    return prepared.astype(float)


def is_upward_crossing(
    previous_value: float, current_value: float, threshold: float, inclusiveness: str
) -> bool:
    if inclusiveness == "strict":
        return previous_value < threshold and current_value > threshold
    return previous_value < threshold and current_value >= threshold


def is_downward_crossing(
    previous_value: float, current_value: float, threshold: float, inclusiveness: str
) -> bool:
    if inclusiveness == "strict":
        return previous_value > threshold and current_value < threshold
    return previous_value > threshold and current_value <= threshold


def detect_crossings(
    series: pd.Series,
    threshold: float,
    crossing_type: str,
    inclusiveness: str,
) -> pd.Series:
    results: dict[pd.Timestamp, bool] = {}

    for idx in range(1, len(series)):
        current_time = series.index[idx]
        previous_value = series.iloc[idx - 1]
        current_value = series.iloc[idx]

        if pd.isna(previous_value) or pd.isna(current_value):
            results[current_time] = False
            continue

        upward = is_upward_crossing(
            float(previous_value), float(current_value), threshold, inclusiveness
        )
        downward = is_downward_crossing(
            float(previous_value), float(current_value), threshold, inclusiveness
        )

        if crossing_type == "upward":
            results[current_time] = upward
        elif crossing_type == "downward":
            results[current_time] = downward
        else:
            results[current_time] = upward or downward

    return pd.Series(results, dtype=bool)


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "timeseries": {"data_type": "SERIES"},
        "threshold": {"data_type": "FLOAT"},
        "crossing_type": {"data_type": "STRING", "default_value": "both"},
        "inclusiveness": {"data_type": "STRING", "default_value": "strict"},
    },
    "outputs": {
        "crossing_mask": {"data_type": "SERIES"},
    },
    "name": "Detect Threshold Crossings in Time Series",
    "category": "Time Series Base Components",
    "description": "Detect upward and downward threshold crossings on a time series.",
    "version_tag": "1.0.0",
    "id": "076036e9-9298-4deb-a0c4-4d2180149d9f",
    "revision_group_id": "cd3d8d41-05ae-4bb4-9266-6350981d08fd",
    "state": "RELEASED",
    "released_timestamp": "2026-05-11T06:00:00+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, timeseries, threshold, crossing_type="both", inclusiveness="strict"):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # Step 1: Validate inputs and parse the threshold.
    threshold = validate_inputs(timeseries, threshold, crossing_type, inclusiveness)

    # Step 2: Sort the series and merge duplicate timestamps by mean.
    prepared = prepare_series(timeseries)

    # Step 3: Detect threshold crossings on consecutive intervals.
    crossing_mask = detect_crossings(prepared, threshold, crossing_type, inclusiveness)

    # Step 4: Return the crossing mask.
    return {
        "crossing_mask": crossing_mask,
    }


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "timeseries",
            "filters": {
                "value": '{\n    "2026-03-01T00:00:00Z": 8.2,\n    "2026-03-01T01:00:00Z": 8.9,\n    "2026-03-01T02:00:00Z": 9.7,\n    "2026-03-01T03:00:00Z": 10.4,\n    "2026-03-01T04:00:00Z": 11.1,\n    "2026-03-01T05:00:00Z": 10.6,\n    "2026-03-01T06:00:00Z": 9.8,\n    "2026-03-01T07:00:00Z": 9.1,\n    "2026-03-01T08:00:00Z": 8.7,\n    "2026-03-01T09:00:00Z": 9.4,\n    "2026-03-01T10:00:00Z": 9.8,\n    "2026-03-01T11:00:00Z": 10.2,\n    "2026-03-01T12:00:00Z": 10.9,\n    "2026-03-01T13:00:00Z": 10.1,\n    "2026-03-01T14:00:00Z": 9.6,\n    "2026-03-01T15:00:00Z": 9.0,\n    "2026-03-01T16:00:00Z": 9.4,\n    "2026-03-01T17:00:00Z": 9.7,\n    "2026-03-01T18:00:00Z": 9.9,\n    "2026-03-01T19:00:00Z": 9.2,\n    "2026-03-01T20:00:00Z": 8.8\n}'
            },
        },
        {"workflow_input_name": "threshold", "filters": {"value": "10.0"}},
    ]
}

RELEASE_WIRING = {
    "input_wirings": [
        {
            "workflow_input_name": "timeseries",
            "filters": {
                "value": '{\n    "2026-03-01T00:00:00Z": 8.2,\n    "2026-03-01T01:00:00Z": 8.9,\n    "2026-03-01T02:00:00Z": 9.7,\n    "2026-03-01T03:00:00Z": 10.4,\n    "2026-03-01T04:00:00Z": 11.1,\n    "2026-03-01T05:00:00Z": 10.6,\n    "2026-03-01T06:00:00Z": 9.8,\n    "2026-03-01T07:00:00Z": 9.1,\n    "2026-03-01T08:00:00Z": 8.7,\n    "2026-03-01T09:00:00Z": 9.4,\n    "2026-03-01T10:00:00Z": 9.8,\n    "2026-03-01T11:00:00Z": 10.2,\n    "2026-03-01T12:00:00Z": 10.9,\n    "2026-03-01T13:00:00Z": 10.1,\n    "2026-03-01T14:00:00Z": 9.6,\n    "2026-03-01T15:00:00Z": 9.0,\n    "2026-03-01T16:00:00Z": 9.4,\n    "2026-03-01T17:00:00Z": 9.7,\n    "2026-03-01T18:00:00Z": 9.9,\n    "2026-03-01T19:00:00Z": 9.2,\n    "2026-03-01T20:00:00Z": 8.8\n}'
            },
        },
        {"workflow_input_name": "threshold", "filters": {"value": "10.0"}},
    ]
}

"""Documentation for Detect Jumps in Time Series

# Detect Jumps in Time Series

## Description
Component to detect jumps in time series data.

## Inputs
- **timeseries** (Pandas Series):
    The input time series. Index must be datetime, values numeric.
- **method** (String, default value: "robust_zscore_on_diff"):
    Jump detection method. One of "threshold_on_derivative",
    "robust_zscore_on_diff".
    - `threshold_on_derivative`: detects jumps via strong changes between
      consecutive values. This is the more specialized option.
      Best suited for:
      - clean signals with low noise
      - fast online checks when simple step detection is enough
      - data where jumps appear as clear single-change events
    - `robust_zscore_on_diff`: scores changes robustly against outliers
      (median/MAD), so isolated spikes are less likely to be treated as jumps.
      This is the recommended default for most users.
      Best suited for:
      - noisy industrial sensor data
      - data with occasional spikes/outliers
      - cases where robust detection is preferred over maximum sensitivity
- **sensitivity** (String, default value: "medium"):
    Controls how easily jumps are accepted after the internal auto-threshold is
    calculated. This is not an absolute jump size. It only changes how strict
    the automatically inferred threshold is.
    - `low`: stricter detection, usually only clearer and stronger jumps
    - `medium`: balanced default behavior
    - `high`: more sensitive detection, so smaller or more borderline jumps
      are more likely to be accepted
- **min_distance** (Integer, default value: 2):
    Minimum distance between two events (samples).
- **direction** (String, default value: "both"):
    Event direction filter. One of "both", "up", "down".
- **smoothing_before** (Boolean, default value: False):
    If True, applies a mild moving average before detection. This can help for
    noisy signals, but it can also make the detected jump timestamp less sharp.

## Outputs
- **jump_mask** (Pandas Series):
    Boolean mask with detected jump positions. A jump is marked at the
    candidate timestamp where the strong change occurs, but only if the
    following points confirm a stable new level.

## Details
1. The input series is sorted by timestamp, duplicate timestamps are merged by mean.
2. Optional smoothing is applied to stabilize detection.
3. A jump score is calculated using the selected method.
4. Transitions over unusually large time gaps are excluded from jump scoring,
   so a jump is not inferred purely across a long data gap.
5. The score is compared against a robust internally determined threshold that
   is scaled by `sensitivity`.
6. Candidates are filtered by direction and persistent post-jump behavior.
7. A candidate is kept at its original change timestamp, but only if the next
   five points confirm a sufficiently stable new level. This helps suppress
   short spikes that immediately return to the old level.
8. Remaining candidates are reduced by minimum event distance.
9. The final jump mask is returned.

## Recommended Usage
Use the defaults first: `method="robust_zscore_on_diff"`,
`sensitivity="medium"`, and `smoothing_before=false`.

If too many jumps are detected, use `sensitivity="low"` first. If clear jumps
are missed, use `sensitivity="high"`. Enable `smoothing_before` only when the
signal is visibly noisy and small fluctuations create false candidates.

For a real jump, the component expects a persistent level change. A single
large spike is usually rejected if the values return quickly to the previous
level.

## Example
```json
{
  "timeseries": {
    "2026-03-01T00:00:00Z": 10.0,
    "2026-03-01T01:00:00Z": 10.1,
    "2026-03-01T02:00:00Z": 10.0,
    "2026-03-01T03:00:00Z": 10.2,
    "2026-03-01T04:00:00Z": 10.1,
    "2026-03-01T05:00:00Z": 10.0,
    "2026-03-01T06:00:00Z": 10.2,
    "2026-03-01T07:00:00Z": 10.1,
    "2026-03-01T08:00:00Z": 10.0,
    "2026-03-01T15:00:00Z": 18.0,
    "2026-03-01T16:00:00Z": 18.1,
    "2026-03-01T17:00:00Z": 18.0,
    "2026-03-01T18:00:00Z": 18.2,
    "2026-03-01T19:00:00Z": 18.1,
    "2026-03-01T20:00:00Z": 18.0,
    "2026-03-01T21:00:00Z": 18.1,
    "2026-03-01T22:00:00Z": 18.0,
    "2026-03-01T23:00:00Z": 31.0,
    "2026-03-02T00:00:00Z": 31.2,
    "2026-03-02T01:00:00Z": 31.1,
    "2026-03-02T02:00:00Z": 31.0,
    "2026-03-02T03:00:00Z": 31.1,
    "2026-03-02T04:00:00Z": 31.0,
    "2026-03-02T05:00:00Z": 31.2
  },
  "method": "robust_zscore_on_diff",
  "sensitivity": "medium",
  "min_distance": 2,
  "direction": "both",
  "smoothing_before": false
}
```

Expected output:
```json
{
  "jump_mask": {
    "2026-03-01T00:00:00Z": false,
    "2026-03-01T01:00:00Z": false,
    "2026-03-01T02:00:00Z": false,
    "2026-03-01T03:00:00Z": false,
    "2026-03-01T04:00:00Z": false,
    "2026-03-01T05:00:00Z": false,
    "2026-03-01T06:00:00Z": false,
    "2026-03-01T07:00:00Z": false,
    "2026-03-01T08:00:00Z": false,
    "2026-03-01T15:00:00Z": false,
    "2026-03-01T16:00:00Z": false,
    "2026-03-01T17:00:00Z": false,
    "2026-03-01T18:00:00Z": false,
    "2026-03-01T19:00:00Z": false,
    "2026-03-01T20:00:00Z": false,
    "2026-03-01T21:00:00Z": false,
    "2026-03-01T22:00:00Z": false,
    "2026-03-01T23:00:00Z": true,
    "2026-03-02T00:00:00Z": false,
    "2026-03-02T01:00:00Z": false,
    "2026-03-02T02:00:00Z": false,
    "2026-03-02T03:00:00Z": false,
    "2026-03-02T04:00:00Z": false,
    "2026-03-02T05:00:00Z": false
  }
}
```
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from hdutils import ComponentInputValidationException

# Set fixed parameters
SMOOTHING_WINDOW = 5
PERSISTENCE_POINTS = 5
PERSISTENCE_TOLERANCE_FACTOR = 1.5
PERSISTENCE_LOOKBACK_POINTS = 10
SPIKE_REBOUND_POINTS = 1
SPIKE_REBOUND_RATIO = 0.6
MAX_ALLOWED_GAP_FACTOR = 3.0
SENSITIVITY_FACTORS = {
    "low": 1.25,
    "medium": 1.0,
    "high": 0.8,
}


def validate_and_normalize_inputs(
    timeseries: pd.Series,
    method: str,
    sensitivity: str,
    min_distance: int,
    direction: str,
) -> None:
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
    if not isinstance(timeseries.index, pd.DatetimeIndex):
        raise ComponentInputValidationException(
            "timeseries index must be a pandas DatetimeIndex",
            error_code="422",
            invalid_component_inputs=["timeseries"],
        )
    if not pd.api.types.is_numeric_dtype(timeseries):
        raise ComponentInputValidationException(
            "timeseries values must be numeric",
            error_code="422",
            invalid_component_inputs=["timeseries"],
        )

    valid_methods = {
        "threshold_on_derivative",
        "robust_zscore_on_diff",
    }
    if method not in valid_methods:
        raise ComponentInputValidationException(
            f"method must be one of {sorted(valid_methods)}",
            error_code="422",
            invalid_component_inputs=["method"],
        )

    if direction not in {"both", "up", "down"}:
        raise ComponentInputValidationException(
            "direction must be one of 'both', 'up', 'down'",
            error_code="422",
            invalid_component_inputs=["direction"],
        )

    if sensitivity not in SENSITIVITY_FACTORS:
        raise ComponentInputValidationException(
            f"sensitivity must be one of {sorted(SENSITIVITY_FACTORS)}",
            error_code="422",
            invalid_component_inputs=["sensitivity"],
        )

    if not isinstance(min_distance, int) or min_distance < 1:
        raise ComponentInputValidationException(
            "min_distance must be an integer >= 1",
            error_code="422",
            invalid_component_inputs=["min_distance"],
        )


def prepare_series(timeseries: pd.Series) -> pd.Series:
    prepared = timeseries.sort_index()
    if not prepared.index.is_unique:
        prepared = prepared.groupby(level=0).mean()
    return prepared


def calculate_dt_seconds(index: pd.Index) -> pd.Series:
    diffs = index.to_series().diff().dt.total_seconds()
    diffs = diffs.replace(0.0, np.nan)
    return diffs


def infer_typical_dt_seconds(index: pd.Index) -> float | None:
    dt_seconds = calculate_dt_seconds(index).dropna()
    positive_dt_seconds = dt_seconds[dt_seconds > 0]
    if positive_dt_seconds.empty:
        return None
    typical_dt_seconds = float(positive_dt_seconds.median())
    if not np.isfinite(typical_dt_seconds) or typical_dt_seconds <= 0:
        return None
    return typical_dt_seconds


def build_large_gap_mask(
    index: pd.Index,
    max_allowed_gap_factor: float,
) -> pd.Series:
    large_gap_mask = pd.Series(False, index=index)
    typical_dt_seconds = infer_typical_dt_seconds(index)
    if typical_dt_seconds is None:
        return large_gap_mask

    dt_seconds = calculate_dt_seconds(index)
    gap_limit_seconds = typical_dt_seconds * max_allowed_gap_factor
    return dt_seconds > gap_limit_seconds


def apply_smoothing(
    series: pd.Series,
    smoothing_before: bool,
    smoothing_window: int,
) -> pd.Series:
    if not smoothing_before:
        return series
    return series.rolling(window=smoothing_window, min_periods=1).mean()


def calculate_difference_per_second(series: pd.Series) -> pd.Series:
    diff_signal = series.diff()
    dt_seconds = calculate_dt_seconds(series.index)
    per_second = diff_signal / dt_seconds
    return per_second.replace([np.inf, -np.inf], np.nan)


def robust_auto_threshold(score: pd.Series) -> float:
    valid = score.dropna()
    if valid.empty:
        return 0.0
    med = float(valid.median())
    mad = float((valid - med).abs().median())
    sigma = 1.4826 * mad
    if sigma == 0.0 or np.isnan(sigma):
        q25 = float(valid.quantile(0.25))
        q75 = float(valid.quantile(0.75))
        iqr = q75 - q25
        sigma = iqr / 1.349 if iqr > 0 else 0.0
    if sigma == 0.0 or np.isnan(sigma):
        # Fallback for almost-constant signals with rare large jumps/spikes.
        # We intentionally keep this low and rely on persistence filters afterwards.
        return max(med, float(valid.quantile(0.90)))
    return med + 3.5 * sigma


def apply_sensitivity_to_threshold(threshold: float, sensitivity: str) -> float:
    return float(threshold) * SENSITIVITY_FACTORS[sensitivity]


def passes_direction(magnitude: float, direction: str) -> bool:
    if direction == "both":
        return True
    if direction == "up":
        return magnitude > 0
    return magnitude < 0


def enforce_min_distance(
    candidates: pd.Index,
    magnitudes: pd.Series,
    min_distance: int,
    index_positions: pd.Series,
) -> pd.Index:
    if len(candidates) == 0:
        return candidates

    kept: list[pd.Timestamp] = []
    last_kept_ts: pd.Timestamp | None = None
    last_kept_pos: int | None = None

    for ts in candidates:
        pos = int(index_positions.loc[ts])
        if last_kept_pos is None or pos - last_kept_pos >= min_distance:
            kept.append(ts)
            last_kept_pos = pos
            last_kept_ts = ts
        elif abs(float(magnitudes.loc[ts])) > abs(float(magnitudes.loc[last_kept_ts])):
            kept[-1] = ts
            last_kept_pos = pos
            last_kept_ts = ts

    return pd.Index(kept)


def remove_spike_rebound_candidates(
    candidates: pd.Index,
    magnitudes: pd.Series,
    index_positions: pd.Series,
    rebound_points: int,
    rebound_ratio: float,
) -> pd.Index:
    """Drop spike-like candidates that are followed or preceded by a quick opposite rebound."""
    if len(candidates) == 0:
        return candidates

    kept: list[pd.Timestamp] = []
    for ts in candidates:
        mag = float(magnitudes.loc[ts]) if pd.notna(magnitudes.loc[ts]) else 0.0
        if mag == 0.0:
            continue

        pos = int(index_positions.loc[ts])
        lo = max(0, pos - rebound_points)
        hi = min(len(magnitudes) - 1, pos + rebound_points)
        neighborhood = magnitudes.iloc[lo : hi + 1].drop(labels=[ts], errors="ignore")

        has_strong_opposite_rebound = False
        for rebound_mag in neighborhood.dropna().to_numpy(dtype=float):
            opposite_sign = (mag > 0 and rebound_mag < 0) or (mag < 0 and rebound_mag > 0)
            strong_enough = abs(rebound_mag) >= rebound_ratio * abs(mag)
            if opposite_sign and strong_enough:
                has_strong_opposite_rebound = True
                break

        if not has_strong_opposite_rebound:
            kept.append(ts)

    return pd.Index(kept)


def filter_persistent_jumps(
    events_idx: pd.Index,
    series: pd.Series,
    index_positions: pd.Series,
    lookback_points: int,
    persistence_points: int,
    tolerance_factor: float,
    large_gap_mask: pd.Series,
) -> pd.Index:
    if len(events_idx) == 0:
        return events_idx

    gap_positions = np.flatnonzero(large_gap_mask.to_numpy(dtype=bool))
    kept: list[pd.Timestamp] = []
    for ts in events_idx:
        pos = int(index_positions.loc[ts])
        previous_gap_positions = gap_positions[gap_positions <= pos]
        previous_gap_pos = (
            int(previous_gap_positions[-1]) if len(previous_gap_positions) > 0 else -1
        )
        pre_start = max(previous_gap_pos + 1, pos - lookback_points)
        pre_values = series.iloc[pre_start:pos].dropna()

        next_gap_positions = gap_positions[gap_positions > pos]
        next_gap_pos = int(next_gap_positions[0]) if len(next_gap_positions) > 0 else len(series)
        post_end = min(next_gap_pos, pos + 1 + persistence_points)
        post_values = series.iloc[pos + 1 : post_end].dropna()

        if len(pre_values) == 0 or len(post_values) < persistence_points:
            continue

        pre_level = float(pre_values.median())
        post_level = float(post_values.median())
        post_spread = float(post_values.std(ddof=0))
        tolerance = max(tolerance_factor * post_spread, 1e-9)

        # A persistent jump needs a meaningful level change.
        if abs(post_level - pre_level) <= tolerance:
            continue

        # The new level must remain stable within a tolerance band.
        stable_ratio = ((post_values - post_level).abs() <= tolerance).mean()
        if stable_ratio < 2 / 3:
            continue

        # Reject short spikes that quickly return near the old level.
        rebound_values = series.iloc[
            pos + 1 + persistence_points : min(next_gap_pos, pos + 1 + 2 * persistence_points)
        ].dropna()
        if len(rebound_values) >= 1:
            returns_to_old = (rebound_values - pre_level).abs() <= tolerance
            if returns_to_old.any():
                continue

        kept.append(ts)

    return pd.Index(kept)


def detect_threshold_on_derivative(
    series: pd.Series,
    sensitivity: str,
) -> tuple[pd.Series, float]:
    derivative = calculate_difference_per_second(series)
    large_gap_mask = build_large_gap_mask(series.index, MAX_ALLOWED_GAP_FACTOR)
    derivative = derivative.mask(large_gap_mask)
    score = derivative.abs()
    used_threshold = apply_sensitivity_to_threshold(robust_auto_threshold(score), sensitivity)
    return score, used_threshold


def detect_robust_zscore_on_diff(
    series: pd.Series,
    sensitivity: str,
) -> tuple[pd.Series, pd.Series, float]:
    diff_signal = series.diff()
    large_gap_mask = build_large_gap_mask(series.index, MAX_ALLOWED_GAP_FACTOR)
    diff_signal = diff_signal.mask(large_gap_mask)
    med = diff_signal.median()
    mad = (diff_signal - med).abs().median()
    scale = 1.4826 * mad
    if scale == 0 or np.isnan(scale):
        scale = diff_signal.std()
    if scale == 0 or np.isnan(scale):
        z = pd.Series(0.0, index=series.index)
    else:
        z = (diff_signal - med) / scale
    score = z.abs()
    used_threshold = apply_sensitivity_to_threshold(robust_auto_threshold(score), sensitivity)
    return score, diff_signal, used_threshold


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "timeseries": {"data_type": "SERIES"},
        "method": {"data_type": "STRING", "default_value": "robust_zscore_on_diff"},
        "sensitivity": {"data_type": "STRING", "default_value": "medium"},
        "min_distance": {"data_type": "INT", "default_value": 2},
        "direction": {"data_type": "STRING", "default_value": "both"},
        "smoothing_before": {"data_type": "BOOLEAN", "default_value": False},
    },
    "outputs": {
        "jump_mask": {"data_type": "SERIES"},
    },
    "name": "Detect Jumps in Time Series",
    "category": "Time Series Base Components",
    "description": "Detect jumps and return a jump mask.",
    "version_tag": "1.0.0",
    "id": "8701e13f-faf4-4a7e-bb5b-724da41d4508",
    "revision_group_id": "70ce7c79-ce2d-4ca2-81a1-80a0920b5bd8",
    "state": "RELEASED",
    "released_timestamp": "2026-05-11T06:00:00+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(
    *,
    timeseries,
    method="robust_zscore_on_diff",
    sensitivity="medium",
    min_distance=2,
    direction="both",
    smoothing_before=False,
):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # Step 1: Validate and normalize user inputs.
    validate_and_normalize_inputs(
        timeseries,
        method,
        sensitivity,
        min_distance,
        direction,
    )

    # Step 2: Prepare input series (sort index, merge duplicate timestamps).
    prepared = prepare_series(timeseries)

    # Step 3: Optionally smooth the series before jump scoring.
    smoothed = apply_smoothing(prepared, smoothing_before, SMOOTHING_WINDOW)
    large_gap_mask = build_large_gap_mask(smoothed.index, MAX_ALLOWED_GAP_FACTOR)

    # Step 4: Calculate score and magnitudes for the selected method.
    if method == "threshold_on_derivative":
        score, used_threshold = detect_threshold_on_derivative(smoothed, sensitivity)
        magnitudes = calculate_difference_per_second(smoothed)
    else:
        score, diff_signal, used_threshold = detect_robust_zscore_on_diff(smoothed, sensitivity)
        magnitudes = diff_signal

    # Step 5: Apply threshold on score to get initial candidate jumps.
    candidate_mask = score > used_threshold
    candidate_mask = candidate_mask.fillna(False)

    # Step 6: Optionally filter candidates by jump direction.
    if direction != "both":
        direction_mask = magnitudes.apply(
            lambda x: passes_direction(float(x) if pd.notna(x) else 0.0, direction)
        )
        candidate_mask = candidate_mask & direction_mask

    # Step 7: Convert surviving candidates into candidate timestamps.
    candidate_index = candidate_mask[candidate_mask].index
    positions = pd.Series(np.arange(len(smoothed.index)), index=smoothed.index)

    # Step 8: Remove spike-like candidates with a strong opposite rebound nearby.
    candidate_index = remove_spike_rebound_candidates(
        candidate_index,
        magnitudes,
        positions,
        SPIKE_REBOUND_POINTS,
        SPIKE_REBOUND_RATIO,
    )

    # Step 9: Enforce persistence to suppress short spike-like events.
    candidate_index = filter_persistent_jumps(
        candidate_index,
        smoothed,
        positions,
        PERSISTENCE_LOOKBACK_POINTS,
        PERSISTENCE_POINTS,
        PERSISTENCE_TOLERANCE_FACTOR,
        large_gap_mask,
    )

    # Step 10: Enforce minimum distance and keep strongest nearby event.
    filtered_index = enforce_min_distance(candidate_index, magnitudes, min_distance, positions)

    # Step 11: Build output mask.
    jump_mask = pd.Series(False, index=smoothed.index)
    if len(filtered_index) > 0:
        jump_mask.loc[filtered_index] = True

    return {
        "jump_mask": jump_mask,
    }


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "timeseries",
            "filters": {
                "value": '{\n    "2026-03-01T00:00:00Z": 10.0,\n    "2026-03-01T01:00:00Z": 10.1,\n    "2026-03-01T02:00:00Z": 10.0,\n    "2026-03-01T03:00:00Z": 10.2,\n    "2026-03-01T04:00:00Z": 10.1,\n    "2026-03-01T05:00:00Z": 10.0,\n    "2026-03-01T06:00:00Z": 10.2,\n    "2026-03-01T07:00:00Z": 10.1,\n    "2026-03-01T08:00:00Z": 10.0,\n    "2026-03-01T15:00:00Z": 18.0,\n    "2026-03-01T16:00:00Z": 18.1,\n    "2026-03-01T17:00:00Z": 18.0,\n    "2026-03-01T18:00:00Z": 18.2,\n    "2026-03-01T19:00:00Z": 18.1,\n    "2026-03-01T20:00:00Z": 18.0,\n    "2026-03-01T21:00:00Z": 18.1,\n    "2026-03-01T22:00:00Z": 18.0,\n    "2026-03-01T23:00:00Z": 31.0,\n    "2026-03-02T00:00:00Z": 31.2,\n    "2026-03-02T01:00:00Z": 31.1,\n    "2026-03-02T02:00:00Z": 31.0,\n    "2026-03-02T03:00:00Z": 31.1,\n    "2026-03-02T04:00:00Z": 31.0,\n    "2026-03-02T05:00:00Z": 31.2\n}'
            },
        }
    ]
}

RELEASE_WIRING = {
    "input_wirings": [
        {
            "workflow_input_name": "timeseries",
            "filters": {
                "value": '{\n    "2026-03-01T00:00:00Z": 10.0,\n    "2026-03-01T01:00:00Z": 10.1,\n    "2026-03-01T02:00:00Z": 10.0,\n    "2026-03-01T03:00:00Z": 10.2,\n    "2026-03-01T04:00:00Z": 10.1,\n    "2026-03-01T05:00:00Z": 10.0,\n    "2026-03-01T06:00:00Z": 10.2,\n    "2026-03-01T07:00:00Z": 10.1,\n    "2026-03-01T08:00:00Z": 10.0,\n    "2026-03-01T15:00:00Z": 18.0,\n    "2026-03-01T16:00:00Z": 18.1,\n    "2026-03-01T17:00:00Z": 18.0,\n    "2026-03-01T18:00:00Z": 18.2,\n    "2026-03-01T19:00:00Z": 18.1,\n    "2026-03-01T20:00:00Z": 18.0,\n    "2026-03-01T21:00:00Z": 18.1,\n    "2026-03-01T22:00:00Z": 18.0,\n    "2026-03-01T23:00:00Z": 31.0,\n    "2026-03-02T00:00:00Z": 31.2,\n    "2026-03-02T01:00:00Z": 31.1,\n    "2026-03-02T02:00:00Z": 31.0,\n    "2026-03-02T03:00:00Z": 31.1,\n    "2026-03-02T04:00:00Z": 31.0,\n    "2026-03-02T05:00:00Z": 31.2\n}'
            },
        }
    ]
}

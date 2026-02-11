"""Documentation for Simple Time Series Forecast

# Generic Fast Time Series Forecast

## Description
Quick forecaster for arbitrary time series. It resamples irregular data to a
regular grid, cleans missing values, and offers several forecasting strategies focused
on responsiveness. The default ``auto_select`` approach select the best of three implemented forecasting
strategies.

## Inputs
- **series** (Pandas Series):
    Time series with a ``DatetimeIndex``. Irregular sampling, gaps, Null- and infinite values are allowed.
- **forecast_steps** (Integer, optional):
    Number of forecasted points. Must be a positive integer.
- **forecast_horizon** (String, optional, default value: "2D"):
    Alternative to ``forecast_steps``. Duration formatted like ``"2D"`` or ``"12H"``.
- **method** (String, default value: "auto_select"):
    Forecasting strategy. Supported values: ``auto_select``, ``linear_trend``,
    ``moving_average`` or ``seasonal_trend``.
- **plot_confidence_interval** (Boolean, default value: True):
    If True, a light confidence band based on recent residuals is plotted.

## Outputs
- **plot** (Plotly JSON):
    Visualisation containing both the original time series and the forecast
    (optionally with a confidence band).

## Remarks
- The component is designed for robustness and speed rather than absolute accuracy.
- ``seasonal_trend`` works in three intuitive steps: smooth the signal with a rolling
  average to capture the slowly changing baseline, measure the typical ups and downs
  for each position within a detected season (for example, each hour of the day), and
  add the two pieces together for the forecast horizon.
- If no reliable season length can be inferred, the logic automatically falls back to
  the method linear_trend.
- Large gaps remain unfilled to avoid synthetic bridging values.
- Hours that are almost always zero in the recent history (last seven days) are
  forced to be zero in the forecast as well.

## Example
```json
{
  "series": {
    "2023-01-01T00:03:00+00:00": 20.0,
    "2023-01-01T01:08:00+00:00": 22.0,
    "2023-01-01T02:05:00+00:00": 25.0,
    "2023-01-01T03:12:00+00:00": 27.0,
    "2023-01-01T04:04:00+00:00": 26.1,
    "2023-01-01T05:09:00+00:00": 23.2,
    "2023-01-01T06:02:00+00:00": 21.1,
    "2023-01-01T07:15:00+00:00": 20.0,
    "2023-01-01T08:07:00+00:00": 19.0,
    "2023-01-01T09:11:00+00:00": 21.0,
    "2023-01-01T10:05:00+00:00": 24.1,
    "2023-01-01T11:10:00+00:00": 28.0,
    "2023-01-01T12:06:00+00:00": 30.2,
    "2023-01-01T13:08:00+00:00": 28.9,
    "2023-01-01T14:02:00+00:00": 27.1,
    "2023-01-01T15:14:00+00:00": 24.2,
    "2023-01-01T16:09:00+00:00": 22.1,
    "2023-01-01T17:01:00+00:00": 21.0,
    "2023-01-01T18:06:00+00:00": 20.2,
    "2023-01-01T19:10:00+00:00": 19.0,
    "2023-01-01T20:04:00+00:00": 18.0,
    "2023-01-01T21:16:00+00:00": 19.1,
    "2023-01-01T22:05:00+00:00": 20.0,
    "2023-01-01T23:12:00+00:00": 21.0,
    "2023-01-02T00:04:00+00:00": 20.5,
    "2023-01-02T01:11:00+00:00": 22.4,
    "2023-01-02T02:06:00+00:00": 25.6,
    "2023-01-02T03:13:00+00:00": 27.6,
    "2023-01-02T04:03:00+00:00": 26.6,
    "2023-01-02T05:08:00+00:00": 23.6,
    "2023-01-02T06:04:00+00:00": 21.6,
    "2023-01-02T07:12:00+00:00": 20.6,
    "2023-01-02T08:03:00+00:00": 19.7,
    "2023-01-02T09:15:00+00:00": 21.6,
    "2023-01-02T10:07:00+00:00": 24.6,
    "2023-01-02T11:09:00+00:00": 28.6,
    "2023-01-02T12:02:00+00:00": 30.6,
    "2023-01-02T13:11:00+00:00": 29.5,
    "2023-01-02T14:05:00+00:00": 27.6,
    "2023-01-02T15:10:00+00:00": 24.6,
    "2023-01-02T16:04:00+00:00": 22.6,
    "2023-01-02T17:08:00+00:00": 21.6,
    "2023-01-02T18:01:00+00:00": 20.6,
    "2023-01-02T19:14:00+00:00": 19.6,
    "2023-01-02T20:06:00+00:00": 18.6,
    "2023-01-02T21:12:00+00:00": 19.6,
    "2023-01-02T22:08:00+00:00": 20.6,
    "2023-01-02T23:05:00+00:00": 21.6
  },
  "forecast_horizon": "2D",
  "method": "seasonal_trend"
}
```
"""

# Load packages
from collections.abc import Callable

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from hdutils import ComponentInputValidationException, plotly_fig_to_json_dict

### Set some default values
# clean_time_series_by_interpolation
MAX_INTERPOLATION_GAP_STEPS = 4
# detect_seasonal_floor_slots
SEASONAL_FLOOR_TOLERANCE_FRACTION = 0.01
SEASONAL_FLOOR_MIN_FRACTION = 0.6
# detect_daily_zero_hours
DAILY_ZERO_LOOKBACK_DAYS = 7
DAILY_ZERO_TOLERANCE = 1e-6
DAILY_ZERO_REQUIRED_DAYS = 4
# seasonal_trend_forecast
SEASONAL_TREND_TOLERANCE_FRACTION = 0.1
SEASONAL_TREND_MIN_CHANGE_FRACTION = 0.05
SEASONAL_TREND_REDUCTION_FACTOR = 0.8
SEASONAL_TREND_MAX_ITERATIONS = 12
SEASONAL_FLOOR_TOLERANCE_FRACTION = 0.01
SEASONAL_ALIGNMENT_WINDOW = 10
SEASONAL_FLOOR_BLEND_MIN = 0.35
SEASONAL_FLOOR_BLEND_MAX = 0.9
# confidence interval defaults
CONFIDENCE_MAX_RESIDUALS = 200
CONFIDENCE_ROLLING_WINDOW = 5
CONFIDENCE_Z_VALUE = 1.96


### Function regarding Step 1 in the main function
def validate_inputs(
    forecast_steps, forecast_horizon, method
) -> tuple[int | None, pd.Timedelta | None, str]:
    """Validate and normalize user inputs for the forecast."""
    steps_value: int | None = None
    horizon_value: pd.Timedelta | None = None

    if forecast_steps is not None and forecast_horizon is not None:
        raise ComponentInputValidationException(
            "Please provide either `forecast_steps` or `forecast_horizon`, not both.",
            error_code="422",
            invalid_component_inputs=["forecast_steps", "forecast_horizon"],
        )

    if forecast_steps is not None:
        if not isinstance(forecast_steps, int) or forecast_steps <= 0:
            raise ComponentInputValidationException(
                "`forecast_steps` must be a positive integer",
                error_code="422",
                invalid_component_inputs=["forecast_steps"],
            )
        steps_value = forecast_steps
    elif forecast_horizon is not None:
        horizon_text = str(forecast_horizon).strip()
        if horizon_text:
            try:
                horizon_value = pd.to_timedelta(horizon_text)
            except (TypeError, ValueError) as exc:
                raise ComponentInputValidationException(
                    "`forecast_horizon` must be a valid duration string (e.g. '12H' or '2D')",
                    error_code="422",
                    invalid_component_inputs=["forecast_horizon"],
                ) from exc
            if horizon_value <= pd.Timedelta(0):
                raise ComponentInputValidationException(
                    "`forecast_horizon` must describe a positive duration",
                    error_code="422",
                    invalid_component_inputs=["forecast_horizon"],
                )

    if steps_value is None and horizon_value is None:
        horizon_value = pd.Timedelta(days=2)

    method_normalised = str(method).lower()
    if method_normalised not in {
        "linear_trend",
        "moving_average",
        "seasonal_trend",
        "auto_select",
    }:
        raise ComponentInputValidationException(
            "`method` must be one of 'auto_select', 'linear_trend', 'moving_average' or 'seasonal_trend'",
            error_code="422",
            invalid_component_inputs=["method"],
        )

    return steps_value, horizon_value, method_normalised


### Functions regarding Step 2 in the main function
# Time series resampling (median_diff)
def resample_time_series_if_needed(
    series: pd.Series,
) -> tuple[pd.Series, pd.Timedelta | None]:
    """Ensures regular sampling by rounding and interpolating if needed.

    Returns the (possibly resampled) series together with the inferred median
    time step if it could be computed.
    """
    # Check the series
    if series.empty:
        raise ComponentInputValidationException(
            "The input data must not be empty!",
            error_code="EmptyDataFrame",
            invalid_component_inputs=["series"],
        )
    if not pd.api.types.is_datetime64_any_dtype(series.index.dtype):
        raise ComponentInputValidationException(
            "Indices of series must be datetime, but are of type "
            + str(series.index.dtype),
            error_code="422",
            invalid_component_inputs=["series"],
        )
    # Order the series
    ordered = series.sort_index()
    if not ordered.index.is_unique:
        ordered = ordered.groupby(level=0).mean()
    # Resample the series to median diff
    resampled = ordered
    needs_resample = False
    inferred_freq: pd.Timedelta | None = None
    if len(ordered) >= 2:
        diffs = ordered.index.to_series().diff().dropna()
        if not diffs.empty:
            positive_diffs = diffs[diffs > pd.Timedelta(0)]
            if not positive_diffs.empty:
                median_diff = positive_diffs.median()
                inferred_freq = median_diff
                tolerance = pd.Timedelta(microseconds=1)
                is_regular = (positive_diffs - median_diff).abs().le(tolerance).all()
                if not is_regular:
                    rounded = ordered.index.round(median_diff)
                    grouped = ordered.groupby(rounded).mean().sort_index()
                    if len(grouped) >= 2:
                        regular_index = pd.date_range(
                            start=grouped.index.min(),
                            end=grouped.index.max(),
                            freq=median_diff,
                        )
                        resampled = grouped.reindex(regular_index).interpolate(
                            method="time"
                        )
                        needs_resample = True

    return (resampled if needs_resample else ordered, inferred_freq)


# Time series interpolation
def clean_time_series_by_interpolation(
    series: pd.Series,
    max_gap_steps: int = MAX_INTERPOLATION_GAP_STEPS,
) -> pd.Series:
    """Replace non-numeric entries, interpolate missing values, drop NaNs."""
    # Interpolate the series
    cleaned = pd.to_numeric(series, errors="coerce")
    cleaned = cleaned.replace([np.inf, -np.inf], np.nan)
    method = "time" if isinstance(cleaned.index, pd.DatetimeIndex) else "linear"
    interpolated = cleaned.interpolate(
        method=method,
        limit=max_gap_steps,
        limit_direction="both",
    )
    # Remove large gaps
    if interpolated.isna().any() and max_gap_steps >= 0:
        na_mask = interpolated.isna()
        if na_mask.any():
            run_ids = (na_mask != na_mask.shift()).cumsum()
            run_lengths = na_mask.groupby(run_ids).transform("sum")
            long_gap_mask = run_lengths > max_gap_steps
            interpolated[long_gap_mask] = np.nan
    # Drop missing values
    cleaned = interpolated.dropna()
    if len(cleaned) < 3:
        raise ComponentInputValidationException(
            "After cleaning missing or infinite values, not enough data points remain (>= 3 required)",
            error_code="422",
            invalid_component_inputs=["series"],
        )
    return cleaned


# Detect common lower bound in the time series
def infer_common_floor(series: pd.Series, min_fraction: float = 0.05) -> float | None:
    """Detect a frequently occurring lower bound."""
    min_value = float(series.min())
    max_value = float(series.max())
    value_range = max_value - min_value
    tolerance = max(value_range * 0.05, 1e-9)
    fraction_near_min = float((series <= min_value + tolerance).mean())
    if fraction_near_min >= min_fraction:
        return min_value

    return None


### Functions regarding Step 4 in the main function
# Detect seasonal floor slots
def detect_seasonal_floor_slots(
    series: pd.Series,
    season_length: int,
    floor_value: float,
    tolerance_fraction: float = SEASONAL_FLOOR_TOLERANCE_FRACTION,
    min_fraction: float = SEASONAL_FLOOR_MIN_FRACTION,
) -> dict[int, float]:
    # Check input data
    if season_length < 1 or floor_value is None:
        return {}

    history = series.tail(season_length * 6)
    if history.empty:
        return {}
    # Detect floor slots
    values = history.to_numpy(dtype=float)
    indices = np.arange(len(history))

    floor_slots: dict[int, float] = {}
    value_range = history.max() - history.min()
    tolerance = max(value_range * tolerance_fraction, 1e-6)
    limit = floor_value + tolerance

    for slot in range(season_length):
        slot_mask = indices % season_length == slot
        slot_values = values[slot_mask]
        if slot_values.size == 0:
            continue
        fraction_at_floor = (slot_values <= limit).mean()
        if fraction_at_floor >= min_fraction:
            floor_slots[slot] = floor_value

    return floor_slots


# Detect hours showing only zeros within the last week
def detect_daily_zero_hours(
    series: pd.Series,
    lookback_days: int = DAILY_ZERO_LOOKBACK_DAYS,
    tolerance: float = DAILY_ZERO_TOLERANCE,
    required_zero_days: int = DAILY_ZERO_REQUIRED_DAYS,
) -> set[int]:
    # Check input data
    if not isinstance(series.index, pd.DatetimeIndex) or series.empty:
        return set()
    # Detect zero hours
    window_start = series.index.max() - pd.Timedelta(days=lookback_days)
    recent = series[series.index >= window_start]
    if recent.empty:
        return set()

    zero_hours: set[int] = set()
    grouped = recent.groupby(recent.index.hour)
    for hour, values in grouped:
        per_day = values.groupby(values.index.normalize())
        zero_per_day = per_day.apply(lambda x: (x.abs() <= tolerance).all())
        zero_day_count = int(zero_per_day.sum())
        if zero_day_count >= required_zero_days:
            zero_hours.add(int(hour))

    return zero_hours


def estimate_residual_scale(
    series: pd.Series,
    rolling_window: int = CONFIDENCE_ROLLING_WINDOW,
    max_points: int = CONFIDENCE_MAX_RESIDUALS,
) -> float | None:
    """Estimate residual scale quickly via a backward-looking rolling mean and MAD."""
    if series.empty:
        return None
    window = max(3, min(rolling_window, len(series)))
    trend = (
        series.rolling(window=window, min_periods=max(2, window // 2)).mean().shift(1)
    )
    residuals = (series - trend).dropna()
    if residuals.empty:
        return None
    residuals = residuals.tail(max_points)
    median = float(residuals.median())
    mad = float((residuals - median).abs().median())
    scale = 1.4826 * mad if mad > 0 else float(residuals.std(ddof=0))
    if not np.isfinite(scale) or scale <= 0:
        return None
    return scale


# Moving average forecast
def moving_average_forecast(series: pd.Series, steps: int) -> pd.Series:
    """Forecast using the mean of the most recent observations matching the horizon."""
    # Check input data
    if steps <= 0:
        raise ComponentInputValidationException(
            "`steps` must be a positive integer",
            error_code="422",
            invalid_component_inputs=["forecast_steps"],
        )
    window = min(steps, len(series))
    if window == 0:
        raise ComponentInputValidationException(
            "Moving average forecast requires at least one data point",
            error_code="422",
            invalid_component_inputs=["series"],
        )
    # Calculate forecast
    avg = float(series.tail(window).mean())
    return pd.Series([avg] * steps)


# Linear trend forecast
def linear_trend_forecast(series: pd.Series, steps: int) -> pd.Series:
    """Forecast by extending a least-squares trend over uniformly spaced observations."""
    # Calculate forecast
    positions = np.arange(len(series), dtype=float)
    slope, intercept = np.polyfit(positions, series.to_numpy(dtype=float), 1)
    future_positions = np.arange(len(series), len(series) + steps, dtype=float)
    trend_values = slope * future_positions + intercept
    return pd.Series(trend_values)


# Infer season length
def infer_season_length_steps(
    freq: pd.Timedelta, series_length: int, min_repeats: int = 2
) -> int | None:
    """Find a plausible seasonal period based on common cycles."""

    if freq <= pd.Timedelta(0):
        return None

    candidates = [
        pd.Timedelta(days=28),
        pd.Timedelta(days=7),
        pd.Timedelta(days=1),
        pd.Timedelta(hours=12),
        pd.Timedelta(hours=8),
        pd.Timedelta(hours=6),
        pd.Timedelta(hours=4),
        pd.Timedelta(hours=1),
    ]

    for candidate in candidates:
        approx_steps = int(round(candidate / freq))
        if approx_steps < 2:
            continue
        # Require at least two complete seasons so the seasonal mean is stable
        if series_length < approx_steps * min_repeats:
            continue
        estimated_cycle = freq * approx_steps
        if abs(estimated_cycle - candidate) <= candidate * 0.1:
            return approx_steps

    return None


### Seasonal trend forecast
# Step 1: Focus on the recent portion of the series so current patterns dominate the decomposition
def prepare_recent_history(
    series: pd.Series, season_length: int
) -> tuple[pd.Series, np.ndarray, np.ndarray]:
    tail_length = season_length * 7
    working_series = series.tail(tail_length)
    values = working_series.to_numpy(dtype=float)
    positions = np.arange(len(values), dtype=float)
    return working_series, values, positions


# Step 2: Smooth the trend with a rolling mean and gently fill remaining gaps afterwards
def smooth_trend_values(
    working_series: pd.Series,
    season_length: int,
    values: np.ndarray,
    positions: np.ndarray,
) -> np.ndarray:
    trend_series = (
        working_series.rolling(
            window=season_length, center=True, min_periods=max(2, season_length // 2)
        )
        .mean()
        .interpolate(method="time")
    )
    trend_series = trend_series.ffill().bfill()
    if trend_series.isna().any():
        slope, intercept = np.polyfit(positions, values, 1)
        trend_series = pd.Series(
            slope * positions + intercept, index=working_series.index
        )
    return trend_series.to_numpy(dtype=float)


# Step 3: Derive the seasonal profile from the average residual for each seasonal position
def compute_seasonal_pattern(
    values: np.ndarray,
    trend_values: np.ndarray,
    season_length: int,
    index: pd.DatetimeIndex,
    frequency: pd.Timedelta,
) -> np.ndarray:
    residuals = values - trend_values
    seasonal_pattern = np.zeros(season_length, dtype=float)
    seasonal_counts = np.zeros(season_length, dtype=int)
    origin = index[0]
    step_numbers = np.rint((index - origin) / frequency).astype(int)
    for step_number, residual in zip(step_numbers, residuals):
        slot = int(step_number % season_length)
        seasonal_pattern[slot] += residual
        seasonal_counts[slot] += 1
    seasonal_counts = np.where(seasonal_counts == 0, 1, seasonal_counts)
    seasonal_pattern = seasonal_pattern / seasonal_counts
    seasonal_pattern -= seasonal_pattern.mean()
    return seasonal_pattern


# Step 4: Extend the trend component via linear regression on the smoothed trend values
def build_trend_extension(
    trend_values: np.ndarray,
    positions: np.ndarray,
    steps: int,
) -> tuple[np.ndarray, float, Callable[[float], np.ndarray]]:
    slope, _ = np.polyfit(positions, trend_values, 1)
    future_idx = np.arange(len(positions), len(positions) + steps, dtype=float)

    def build_trend_series(slope_factor: float) -> np.ndarray:
        scaled_slope = slope * slope_factor
        intercept_local = trend_values[-1] - scaled_slope * (len(positions) - 1)
        return scaled_slope * future_idx + intercept_local

    return build_trend_series(1.0), slope, build_trend_series


# Step 5: Make sure that the trend is not determining the forecast too strong
def enforce_trend_bounds(
    forecast_values: np.ndarray,
    trend_forecast: np.ndarray,
    seasonal_future: np.ndarray,
    slope: float,
    values: np.ndarray,
    steps: int,
    season_length: int,
    build_trend_series: Callable[[float], np.ndarray],
) -> tuple[np.ndarray, np.ndarray, bool, float]:
    value_min = float(values.min())
    value_max = float(values.max())
    value_range = max(value_max - value_min, 1e-9)
    tolerance = value_range * SEASONAL_TREND_TOLERANCE_FRACTION
    trend_used = True
    maximum_change = abs(slope) * max(steps, season_length)
    if maximum_change < value_range * SEASONAL_TREND_MIN_CHANGE_FRACTION:
        trend_used = False
    lower_bound = value_min - tolerance
    upper_bound = value_max + tolerance

    def within_bounds(vals: np.ndarray) -> bool:
        return vals.min() >= lower_bound and vals.max() <= upper_bound

    if trend_used and not within_bounds(forecast_values):
        if slope == 0:
            trend_used = False
        else:
            # Shrink the slope gradually until the forecast remains within the soft bounds
            factor = 1.0
            adjusted_forecast = forecast_values
            for _ in range(SEASONAL_TREND_MAX_ITERATIONS):
                factor *= SEASONAL_TREND_REDUCTION_FACTOR
                candidate_trend = build_trend_series(factor)
                candidate = candidate_trend + seasonal_future
                if within_bounds(candidate):
                    adjusted_forecast = candidate
                    trend_forecast = candidate_trend
                    break
            else:
                trend_used = False
                trend_forecast = build_trend_series(0.0)
                adjusted_forecast = trend_forecast + seasonal_future
            forecast_values = adjusted_forecast

    # Forecast in case of missing trend
    if not trend_used:
        baseline = float(trend_forecast[-1])
        trend_forecast = np.full(steps, baseline, dtype=float)
        forecast_values = trend_forecast + seasonal_future

    return forecast_values, trend_forecast, trend_used, value_range


# Step 6: Detect seasonal slots that usually touch the floor and pin those forecast points
def apply_floor_alignment(
    forecast_values: np.ndarray,
    values: np.ndarray,
    season_length: int,
    floor_value: float | None,
    value_range: float,
) -> np.ndarray:
    if floor_value is None or season_length <= 0:
        return forecast_values

    floor_tolerance = max(value_range * SEASONAL_FLOOR_TOLERANCE_FRACTION, 1e-9)
    slot_floor_fraction = np.zeros(season_length, dtype=float)
    indices = np.arange(len(values))
    for slot in range(season_length):
        slot_values = values[indices % season_length == slot]
        if slot_values.size == 0:
            continue
        fraction_at_floor = float((slot_values <= floor_value + floor_tolerance).mean())
        if fraction_at_floor >= SEASONAL_FLOOR_MIN_FRACTION:
            slot_floor_fraction[slot] = fraction_at_floor

    for step in range(len(forecast_values)):
        slot = (len(values) + step) % season_length
        fraction = slot_floor_fraction[slot]
        if fraction <= 0:
            continue
        # Blend towards floor instead of hard pinning to reduce step-like jumps.
        strength = (fraction - SEASONAL_FLOOR_MIN_FRACTION) / (
            1.0 - SEASONAL_FLOOR_MIN_FRACTION
        )
        alpha = SEASONAL_FLOOR_BLEND_MIN + (
            SEASONAL_FLOOR_BLEND_MAX - SEASONAL_FLOOR_BLEND_MIN
        ) * np.clip(strength, 0.0, 1.0)
        forecast_values[step] = (1.0 - alpha) * forecast_values[
            step
        ] + alpha * floor_value
    return forecast_values


# Main function for seasonal trend forecast
def seasonal_trend_forecast(
    series: pd.Series,
    steps: int,
    season_length: int,
    frequency: pd.Timedelta,
    floor_value: float | None = None,
) -> tuple[pd.Series, bool]:
    """Forecast via additive decomposition: rolling trend plus seasonal mean profile."""
    # Check input data
    if season_length < 2:
        raise ValueError("season_length must be >= 2")
    if len(series) < season_length * 2:
        raise ComponentInputValidationException(
            "Seasonal trend forecast requires at least two complete seasons.",
            error_code="422",
            invalid_component_inputs=["series"],
        )
    # Step 1 to 6
    working_series, values, positions = prepare_recent_history(series, season_length)
    trend_values = smooth_trend_values(working_series, season_length, values, positions)
    seasonal_pattern = compute_seasonal_pattern(
        values,
        trend_values,
        season_length,
        working_series.index,
        frequency,
    )

    trend_forecast, slope, build_trend_series = build_trend_extension(
        trend_values, positions, steps
    )
    future_index = pd.date_range(
        start=working_series.index[-1] + frequency,
        periods=steps,
        freq=frequency,
    )
    origin = working_series.index[0]
    future_steps = np.rint((future_index - origin) / frequency).astype(int)
    seasonal_future = seasonal_pattern[future_steps % season_length]
    forecast_values = trend_forecast + seasonal_future

    (
        forecast_values,
        trend_forecast,
        trend_used,
        value_range,
    ) = enforce_trend_bounds(
        forecast_values,
        trend_forecast,
        seasonal_future,
        slope,
        values,
        steps,
        season_length,
        build_trend_series,
    )

    forecast_values = apply_floor_alignment(
        forecast_values, values, season_length, floor_value, value_range
    )

    return pd.Series(forecast_values), trend_used


# Generate complete forecast series
def build_forecast_series(
    base_series: pd.Series, values: pd.Series, freq: pd.Timedelta
) -> pd.Series:
    """Combine forecast values with extrapolated timestamps."""

    start_time = base_series.index[-1] + freq
    forecast_index = pd.date_range(start=start_time, periods=len(values), freq=freq)
    return pd.Series(values.values, index=forecast_index)


# Align forecast start to last value
def align_seasonal_forecast_start(
    values: pd.Series, reference_value: float
) -> pd.Series:
    if values.empty:
        return values
    offset = reference_value - float(values.iloc[0])
    if offset == 0:
        return values
    return values + offset


# Specific forecast methods
def run_selected_method(
    series: pd.Series,
    steps: int,
    frequency: pd.Timedelta,
    floor_value: float | None,
    method: str,
) -> tuple[pd.Series, str, bool, bool | None]:
    # Some parameters
    seasonal_used = False
    trend_component_used: bool | None = None
    effective_method = method
    season_length_used: int | None = None
    base_length = len(series)
    # Different methods, including fallbacks
    if method == "seasonal_trend":
        season_length = infer_season_length_steps(frequency, len(series))
        if season_length is None:
            forecast_values = linear_trend_forecast(series, steps)
            effective_method = "linear_trend"
        else:
            season_length_used = season_length
            try:
                forecast_values, trend_component_used = seasonal_trend_forecast(
                    series,
                    steps,
                    season_length,
                    frequency,
                    floor_value=floor_value,
                )
                seasonal_used = True
            except ComponentInputValidationException:
                forecast_values = linear_trend_forecast(series, steps)
                effective_method = "linear_trend"
    elif method == "linear_trend":
        forecast_values = linear_trend_forecast(series, steps)
    elif method == "moving_average":
        forecast_values = moving_average_forecast(series, steps)
    else:
        # defensive fallback, same as moving average with a horizon-based window
        forecast_values = moving_average_forecast(series, steps)
        effective_method = "moving_average"

    if (
        effective_method == "seasonal_trend"
        and season_length_used
        and floor_value is not None
    ):
        floor_slots = detect_seasonal_floor_slots(
            series, season_length_used, floor_value
        )
        if floor_slots:
            for step in range(steps):
                slot = (base_length + step) % season_length_used
                if slot in floor_slots:
                    forecast_values.iloc[step] = floor_slots[slot]

    if floor_value is not None:
        forecast_values = forecast_values.clip(lower=floor_value)

    return forecast_values, effective_method, seasonal_used, trend_component_used


# Auto-select forecast
def auto_select_forecast(
    series: pd.Series,
    steps: int,
    frequency: pd.Timedelta,
    floor_value: float | None,
) -> tuple[pd.Series, str, bool, bool | None]:
    # List of possible methods, ordered
    candidates = ["seasonal_trend", "linear_trend", "moving_average"]
    last_result: tuple[pd.Series, str, bool, bool | None] | None = None

    for candidate in candidates:
        result = run_selected_method(series, steps, frequency, floor_value, candidate)
        forecast_values, effective_method, seasonal_used, trend_used = result
        last_result = result

        if effective_method == candidate:
            return result

    # if every candidate fell back to an alternative, return the last computed result
    if last_result is None:
        raise ComponentInputValidationException(
            "Unable to compute forecast using any available method.",
            error_code="422",
            invalid_component_inputs=["series"],
        )

    return last_result


### Functions regarding Step 2 in the main function
# Confidence interval helpers and plot
def build_confidence_interval(
    forecast_series: pd.Series,
    residual_scale: float,
    floor_value: float | None,
    zero_hours: set[int],
    z_value: float = CONFIDENCE_Z_VALUE,
) -> tuple[pd.Series, pd.Series]:
    # widen uncertainty gently with horizon length using a log curve
    steps = np.arange(1, len(forecast_series) + 1, dtype=float)
    growth = 1.0 + 0.1 * np.log1p(steps - 1.0)
    scale = residual_scale * growth
    spread = z_value * scale
    lower = forecast_series - spread
    upper = forecast_series + spread

    if floor_value is not None:
        lower = lower.clip(lower=floor_value)

    if zero_hours and isinstance(forecast_series.index, pd.DatetimeIndex):
        mask = np.isin(forecast_series.index.hour.astype(int), list(zero_hours))
        if mask.any():
            lower = lower.copy()
            upper = upper.copy()
            lower.iloc[mask] = 0.0
            upper.iloc[mask] = 0.0

    return lower, upper


def build_forecast_plot(
    series: pd.Series,
    forecast: pd.Series,
    lower: pd.Series | None = None,
    upper: pd.Series | None = None,
) -> go.Figure:
    """Create a plot showing original and forecast values."""

    combined = pd.concat([series.tail(1), forecast])
    fig = go.Figure(
        [
            go.Scatter(
                name="Original",
                x=series.index,
                y=series.values,
                mode="lines",
                line={"color": "#2FAE53"},
            ),
            go.Scatter(
                name="Forecast",
                x=combined.index,
                y=combined.values,
                mode="lines",
                line={"color": "#EB7C45"},
            ),
        ]
    )

    if lower is not None and upper is not None:
        fig.add_trace(
            go.Scatter(
                name="Forecast Upper",
                x=upper.index,
                y=upper.values,
                mode="lines",
                line={"color": "rgba(235,124,69,0.25)", "width": 0},
                showlegend=False,
            )
        )
        fig.add_trace(
            go.Scatter(
                name="Forecast Interval",
                x=lower.index,
                y=lower.values,
                mode="lines",
                line={"color": "rgba(235,124,69,0.25)", "width": 0},
                fill="tonexty",
                fillcolor="rgba(235,124,69,0.15)",
                showlegend=True,
            )
        )

    if series.min() <= 0:
        fig.add_hline(y=0, line={"color": "gray", "width": 1, "dash": "dash"})

    return fig


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "series": {"data_type": "SERIES"},
        "forecast_steps": {"data_type": "INT", "default_value": None},
        "forecast_horizon": {"data_type": "STRING", "default_value": "2D"},
        "method": {"data_type": "STRING", "default_value": "auto_select"},
        "plot_confidence_interval": {"data_type": "BOOLEAN", "default_value": True},
    },
    "outputs": {
        "plot": {"data_type": "PLOTLYJSON"},
    },
    "name": "Simple Time Series Forecast",
    "category": "Time Series Analysis",
    "description": "Quick forecast baseline for arbitrary time series inputs.",
    "version_tag": "1.2.0",
    "id": "662a3790-18b2-427a-a00c-37cf06efa3fd",
    "revision_group_id": "e2f66407-8297-44fe-8a91-0ed6ce72f553",
    "state": "DRAFT",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(
    *,
    series,
    forecast_steps=None,
    forecast_horizon="2D",
    method="auto_select",
    plot_confidence_interval=True,
):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.

    ### Step 1: Validate the input
    steps_value, horizon_value, method_normalised = validate_inputs(
        forecast_steps, forecast_horizon, method
    )

    ### Step 2: Resample and clean the time series
    prepared, inferred_frequency = resample_time_series_if_needed(series)
    cleaned = clean_time_series_by_interpolation(
        prepared,
        max_gap_steps=MAX_INTERPOLATION_GAP_STEPS,
    )
    floor_value = infer_common_floor(cleaned)

    ### Step 3: Determine number of forecast steps from forecast horizon
    if inferred_frequency is None:
        raise ComponentInputValidationException(
            "The series index does not expose a consistent positive step size.",
            error_code="422",
            invalid_component_inputs=["series"],
        )
    frequency = inferred_frequency

    if steps_value is None and horizon_value is not None:
        ratio = horizon_value / frequency
        steps_computed = int(np.ceil(ratio)) if ratio > 0 else 0
        steps_value = max(1, steps_computed)
    forecast_steps = steps_value

    ### Step 4: Produce forecast values using the selected strategy
    seasonal_used = False
    trend_component_used: bool | None = None
    effective_method = method_normalised
    if method_normalised == "auto_select":
        # Try the seasonal methods first, then fall back to trend-based variants
        forecast_values, effective_method, seasonal_used, trend_component_used = (
            auto_select_forecast(
                cleaned,
                forecast_steps,
                frequency,
                floor_value,
            )
        )
    else:
        (
            forecast_values,
            effective_method,
            seasonal_used,
            trend_component_used,
        ) = run_selected_method(
            cleaned,
            forecast_steps,
            frequency,
            floor_value,
            method_normalised,
        )

    if floor_value is not None:
        forecast_values = forecast_values.clip(lower=floor_value)

    forecast_series = build_forecast_series(cleaned, forecast_values, frequency)

    zero_hours = detect_daily_zero_hours(cleaned)
    if zero_hours and isinstance(forecast_series.index, pd.DatetimeIndex):
        mask = forecast_series.index.hour.astype(int)
        zero_indices = np.isin(mask, list(zero_hours))
        if zero_indices.any():
            forecast_series.iloc[zero_indices] = 0.0

    lower_band: pd.Series | None = None
    upper_band: pd.Series | None = None
    if plot_confidence_interval:
        residual_scale = estimate_residual_scale(cleaned)
        if residual_scale is not None:
            lower_band, upper_band = build_confidence_interval(
                forecast_series,
                residual_scale,
                floor_value,
                zero_hours,
            )
            # attach last observed point to bands for a continuous polygon, mirroring exponential_smoothing
            last_value = float(cleaned.iloc[-1])
            last_index = cleaned.index[-1]
            prefix = pd.Series([last_value], index=[last_index])
            lower_band = pd.concat([prefix, lower_band])
            upper_band = pd.concat([prefix, upper_band])

    ### Step 5: Create plot
    plot = plotly_fig_to_json_dict(
        build_forecast_plot(
            cleaned,
            forecast_series,
            lower=lower_band,
            upper=upper_band,
        )
    )

    return {"plot": plot}


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "series",
            "filters": {
                "value": '{\n    "2023-01-01T00:03:00+00:00": 20.0,\n    "2023-01-01T01:08:00+00:00": 22.0,\n    "2023-01-01T02:05:00+00:00": 25.0,\n    "2023-01-01T03:12:00+00:00": 27.0,\n    "2023-01-01T04:04:00+00:00": 26.1,\n    "2023-01-01T05:09:00+00:00": 23.2,\n    "2023-01-01T06:02:00+00:00": 21.1,\n    "2023-01-01T07:15:00+00:00": 20.0,\n    "2023-01-01T08:07:00+00:00": 19.0,\n    "2023-01-01T09:11:00+00:00": 21.0,\n    "2023-01-01T10:05:00+00:00": 24.1,\n    "2023-01-01T11:10:00+00:00": 28.0,\n    "2023-01-01T12:06:00+00:00": 30.2,\n    "2023-01-01T13:08:00+00:00": 28.9,\n    "2023-01-01T14:02:00+00:00": 27.1,\n    "2023-01-01T15:14:00+00:00": 24.2,\n    "2023-01-01T16:09:00+00:00": 22.1,\n    "2023-01-01T17:01:00+00:00": 21.0,\n    "2023-01-01T18:06:00+00:00": 20.2,\n    "2023-01-01T19:10:00+00:00": 19.0,\n    "2023-01-01T20:04:00+00:00": 18.0,\n    "2023-01-01T21:16:00+00:00": 19.1,\n    "2023-01-01T22:05:00+00:00": 20.0,\n    "2023-01-01T23:12:00+00:00": 21.0,\n    "2023-01-02T00:04:00+00:00": 20.5,\n    "2023-01-02T01:11:00+00:00": 22.4,\n    "2023-01-02T02:06:00+00:00": 25.6,\n    "2023-01-02T03:13:00+00:00": 27.6,\n    "2023-01-02T04:03:00+00:00": 26.6,\n    "2023-01-02T05:08:00+00:00": 23.6,\n    "2023-01-02T06:04:00+00:00": 21.6,\n    "2023-01-02T07:12:00+00:00": 20.6,\n    "2023-01-02T08:03:00+00:00": 19.7,\n    "2023-01-02T09:15:00+00:00": 21.6,\n    "2023-01-02T10:07:00+00:00": 24.6,\n    "2023-01-02T11:09:00+00:00": 28.6,\n    "2023-01-02T12:02:00+00:00": 30.6,\n    "2023-01-02T13:11:00+00:00": 29.5,\n    "2023-01-02T14:05:00+00:00": 27.6,\n    "2023-01-02T15:10:00+00:00": 24.6,\n    "2023-01-02T16:04:00+00:00": 22.6,\n    "2023-01-02T17:08:00+00:00": 21.6,\n    "2023-01-02T18:01:00+00:00": 20.6,\n    "2023-01-02T19:14:00+00:00": 19.6,\n    "2023-01-02T20:06:00+00:00": 18.6,\n    "2023-01-02T21:12:00+00:00": 19.6,\n    "2023-01-02T22:08:00+00:00": 20.6,\n    "2023-01-02T23:05:00+00:00": 21.6\n}'
            },
        },
        {"workflow_input_name": "forecast_horizon", "filters": {"value": "2D"}},
        {"workflow_input_name": "method", "filters": {"value": "auto_select"}},
        {
            "workflow_input_name": "plot_confidence_interval",
            "filters": {"value": "True"},
        },
    ]
}
RELEASE_WIRING = {
    "input_wirings": [
        {
            "workflow_input_name": "series",
            "filters": {
                "value": '{\n    "2023-01-01T00:03:00+00:00": 20.0,\n    "2023-01-01T01:08:00+00:00": 22.0,\n    "2023-01-01T02:05:00+00:00": 25.0,\n    "2023-01-01T03:12:00+00:00": 27.0,\n    "2023-01-01T04:04:00+00:00": 26.1,\n    "2023-01-01T05:09:00+00:00": 23.2,\n    "2023-01-01T06:02:00+00:00": 21.1,\n    "2023-01-01T07:15:00+00:00": 20.0,\n    "2023-01-01T08:07:00+00:00": 19.0,\n    "2023-01-01T09:11:00+00:00": 21.0,\n    "2023-01-01T10:05:00+00:00": 24.1,\n    "2023-01-01T11:10:00+00:00": 28.0,\n    "2023-01-01T12:06:00+00:00": 30.2,\n    "2023-01-01T13:08:00+00:00": 28.9,\n    "2023-01-01T14:02:00+00:00": 27.1,\n    "2023-01-01T15:14:00+00:00": 24.2,\n    "2023-01-01T16:09:00+00:00": 22.1,\n    "2023-01-01T17:01:00+00:00": 21.0,\n    "2023-01-01T18:06:00+00:00": 20.2,\n    "2023-01-01T19:10:00+00:00": 19.0,\n    "2023-01-01T20:04:00+00:00": 18.0,\n    "2023-01-01T21:16:00+00:00": 19.1,\n    "2023-01-01T22:05:00+00:00": 20.0,\n    "2023-01-01T23:12:00+00:00": 21.0,\n    "2023-01-02T00:04:00+00:00": 20.5,\n    "2023-01-02T01:11:00+00:00": 22.4,\n    "2023-01-02T02:06:00+00:00": 25.6,\n    "2023-01-02T03:13:00+00:00": 27.6,\n    "2023-01-02T04:03:00+00:00": 26.6,\n    "2023-01-02T05:08:00+00:00": 23.6,\n    "2023-01-02T06:04:00+00:00": 21.6,\n    "2023-01-02T07:12:00+00:00": 20.6,\n    "2023-01-02T08:03:00+00:00": 19.7,\n    "2023-01-02T09:15:00+00:00": 21.6,\n    "2023-01-02T10:07:00+00:00": 24.6,\n    "2023-01-02T11:09:00+00:00": 28.6,\n    "2023-01-02T12:02:00+00:00": 30.6,\n    "2023-01-02T13:11:00+00:00": 29.5,\n    "2023-01-02T14:05:00+00:00": 27.6,\n    "2023-01-02T15:10:00+00:00": 24.6,\n    "2023-01-02T16:04:00+00:00": 22.6,\n    "2023-01-02T17:08:00+00:00": 21.6,\n    "2023-01-02T18:01:00+00:00": 20.6,\n    "2023-01-02T19:14:00+00:00": 19.6,\n    "2023-01-02T20:06:00+00:00": 18.6,\n    "2023-01-02T21:12:00+00:00": 19.6,\n    "2023-01-02T22:08:00+00:00": 20.6,\n    "2023-01-02T23:05:00+00:00": 21.6\n}'
            },
        },
        {"workflow_input_name": "forecast_horizon", "filters": {"value": "2D"}},
        {"workflow_input_name": "method", "filters": {"value": "auto_select"}},
        {
            "workflow_input_name": "plot_confidence_interval",
            "filters": {"value": "True"},
        },
    ]
}

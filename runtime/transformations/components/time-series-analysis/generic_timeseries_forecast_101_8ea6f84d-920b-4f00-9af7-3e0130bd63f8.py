"""Documentation for Generic Time Series Forecast

# Generic Fast Time Series Forecast

## Description
Quick baseline forecaster for arbitrary time series. It resamples irregular data to a
regular grid, cleans missing values, and offers several forecasting strategies focused
on responsiveness. The default ``seasonal_trend`` approach separates a gently smoothed
trend from recurring daily or weekly patterns and adds both parts together to project
the future.

## Inputs
- **series** (Pandas Series):
    Time series with a ``DatetimeIndex``. Irregular sampling and gaps are allowed.
- **forecast_steps** (Integer, optional):
    Number of forecasted points. Must be a positive integer.
- **forecast_horizon** (String, optional, default value: "2D"):
    Alternative to ``forecast_steps``. Duration formatted like ``"2D"`` or ``"12H"``.
- **method** (String, default value: "auto_select"):
    Forecasting strategy. Supported values: ``auto_select``, ``linear_trend``,
    ``moving_average``, ``seasonal_trend`` oder ``fourier_trend``.

## Outputs
- **plot** (Plotly JSON):
    Visualisation containing both the history and the forecast.

## Remarks
- Designed for robustness and speed rather than absolute accuracy.
- Resampling and interpolation mirror the behaviour of the exponential smoothing component.
- ``fourier_trend`` erweitert den linearen Trend um wenige Sinus- und
  Kosinus-Terme eines plausiblen Saisonzyklus.
- ``moving_average`` automatically limits the window to the available number of points.
- ``linear_trend`` fits a least-squares line to the regularised series.
- ``seasonal_trend`` (Standard) works in three intuitive steps: smooth the signal with a rolling
  average to capture the slowly changing baseline, measure the typical ups and downs
  for each position within a detected season (for example, each hour of the day), and
  add the two pieces together for the forecast horizon.
- If no reliable season length can be inferred, the logic automatically falls back to
  the linear trend.
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

from typing import Dict, Optional, Set, Tuple
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from hdutils import ComponentInputValidationException, plotly_fig_to_json_dict
DEFAULT_FORECAST_HORIZON = pd.Timedelta(days=2)
SEASONAL_TREND_TOLERANCE_FRACTION = 0.1
SEASONAL_TREND_MIN_CHANGE_FRACTION = 0.05
SEASONAL_TREND_REDUCTION_FACTOR = 0.8
SEASONAL_TREND_MAX_ITERATIONS = 12
SEASONAL_FLOOR_TOLERANCE_FRACTION = 0.01
SEASONAL_ALIGNMENT_WINDOW = 10
SEASONAL_FLOOR_MIN_FRACTION = 0.6
DAILY_ZERO_LOOKBACK_DAYS = 7
DAILY_ZERO_TOLERANCE = 1e-6
DAILY_ZERO_MIN_FRACTION = 0.95
DAILY_ZERO_MIN_SAMPLES = 3


def resample_time_series_if_needed(
    series: pd.Series,
) -> Tuple[pd.Series, Optional[pd.Timedelta]]:
    """Ensure regular sampling by rounding and interpolating if needed.

    Returns the (possibly resampled) series together with the inferred median
    time step if it could be computed.
    """

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

    ordered = series.sort_index()
    if not ordered.index.is_unique:
        ordered = ordered.groupby(level=0).mean()

    resampled = ordered
    needs_resample = False
    inferred_freq: Optional[pd.Timedelta] = None

    if len(ordered) >= 2:
        diffs = ordered.index.to_series().diff().dropna()
        if not diffs.empty:
            positive_diffs = diffs[diffs > pd.Timedelta(0)]
            if not positive_diffs.empty:
                median_diff = positive_diffs.median()
                inferred_freq = median_diff
                # A tiny tolerance buffer allows minor rounding deviations in the timestamps.
                tolerance = pd.Timedelta(microseconds=1)
                is_regular = median_diff <= pd.Timedelta(0) or (
                    (positive_diffs - median_diff).abs().le(tolerance).all()
                )
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


def clean_time_series_by_interpolation(
    series: pd.Series, min_required_points: int = 3
) -> pd.Series:
    """Replace non-numeric entries, interpolate missing values, drop residual NaNs."""

    cleaned = pd.to_numeric(series, errors="coerce")
    cleaned = cleaned.replace([np.inf, -np.inf], np.nan)
    method = "time" if isinstance(cleaned.index, pd.DatetimeIndex) else "linear"
    cleaned = cleaned.interpolate(method=method).dropna()
    if len(cleaned) < min_required_points:
        raise ComponentInputValidationException(
            "After cleaning missing or infinite values, not enough data points remain (>= 3 required)",
            error_code="422",
            invalid_component_inputs=["series"],
        )
    return cleaned


def infer_common_floor(series: pd.Series, min_fraction: float = 0.05) -> Optional[float]:
    """Detect a frequently occurring lower bound."""

    if len(series) < 5:
        return None

    min_value = float(series.min())
    max_value = float(series.max())
    if not np.isfinite(min_value) or not np.isfinite(max_value):
        return None

    value_range = max_value - min_value
    tolerance = max(value_range * 0.05, 1e-9)
    fraction_near_min = float((series <= min_value + tolerance).mean())
    if fraction_near_min >= min_fraction:
        return min_value

    return None


def detect_seasonal_floor_slots(
    series: pd.Series,
    season_length: int,
    floor_value: float,
    tolerance_fraction: float = SEASONAL_FLOOR_TOLERANCE_FRACTION,
    min_fraction: float = SEASONAL_FLOOR_MIN_FRACTION,
) -> Dict[int, float]:
    if season_length < 1 or floor_value is None:
        return {}

    history = series.tail(season_length * 6)
    if history.empty:
        return {}

    values = history.to_numpy(dtype=float)
    indices = np.arange(len(history))

    floor_slots: Dict[int, float] = {}
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


def detect_daily_zero_hours(
    series: pd.Series,
    lookback_days: int = DAILY_ZERO_LOOKBACK_DAYS,
    tolerance: float = DAILY_ZERO_TOLERANCE,
    min_fraction: float = DAILY_ZERO_MIN_FRACTION,
    min_samples: int = DAILY_ZERO_MIN_SAMPLES,
) -> Set[int]:
    if not isinstance(series.index, pd.DatetimeIndex) or series.empty:
        return set()

    window_start = series.index.max() - pd.Timedelta(days=lookback_days)
    recent = series[series.index >= window_start]
    if recent.empty:
        return set()

    zero_hours: Set[int] = set()
    grouped = recent.groupby(recent.index.hour)
    for hour, values in grouped:
        count = len(values)
        if count < min_samples:
            continue
        share_zero = (values.abs() <= tolerance).mean()
        if share_zero >= min_fraction:
            zero_hours.add(int(hour))

    return zero_hours


def moving_average_forecast(series: pd.Series, steps: int) -> pd.Series:
    """Forecast using the mean of the most recent observations matching the horizon."""

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

    avg = float(series.tail(window).mean())
    return pd.Series([avg] * steps)


def linear_trend_forecast(series: pd.Series, steps: int) -> pd.Series:
    """Forecast by extending a least-squares trend over uniformly spaced observations."""

    positions = np.arange(len(series), dtype=float)
    slope, intercept = np.polyfit(positions, series.to_numpy(dtype=float), 1)
    future_positions = np.arange(len(series), len(series) + steps, dtype=float)
    trend_values = slope * future_positions + intercept
    return pd.Series(trend_values)


def fourier_trend_forecast(
    series: pd.Series,
    steps: int,
    season_length: int,
    max_harmonics: int = 3,
) -> pd.Series:
    """Forecast with a linear drift plus Fourier terms of a seasonal cycle."""

    if season_length < 2:
        raise ComponentInputValidationException(
            "Fourier-based forecasting requires a seasonal length of at least two steps.",
            error_code="422",
            invalid_component_inputs=["series"],
        )
    if len(series) < 2:
        raise ComponentInputValidationException(
            "Fourier-based forecasting needs at least two data points.",
            error_code="422",
            invalid_component_inputs=["series"],
        )

    values = series.to_numpy(dtype=float)
    positions = np.arange(len(values), dtype=float)

    usable_harmonics = max(1, min(max_harmonics, season_length // 2))

    design_columns = [np.ones_like(positions), positions]
    for harmonic in range(1, usable_harmonics + 1):
        angle = 2.0 * np.pi * harmonic * positions / season_length
        design_columns.append(np.sin(angle))
        design_columns.append(np.cos(angle))
    design_matrix = np.column_stack(design_columns)

    try:
        coefficients, *_ = np.linalg.lstsq(design_matrix, values, rcond=None)
    except np.linalg.LinAlgError as exc:
        raise ComponentInputValidationException(
            "Unable to compute Fourier fit for the provided series.",
            error_code="422",
            invalid_component_inputs=["series"],
        ) from exc

    future_positions = np.arange(len(values), len(values) + steps, dtype=float)
    future_columns = [np.ones_like(future_positions), future_positions]
    for harmonic in range(1, usable_harmonics + 1):
        angle = 2.0 * np.pi * harmonic * future_positions / season_length
        future_columns.append(np.sin(angle))
        future_columns.append(np.cos(angle))
    future_matrix = np.column_stack(future_columns)

    forecast_values = future_matrix @ coefficients
    return pd.Series(forecast_values)


def infer_season_length_steps(
    freq: pd.Timedelta, series_length: int, min_repeats: int = 2
) -> Optional[int]:
    """Find a plausible seasonal period in *number of observations* based on common cycles."""

    if freq <= pd.Timedelta(0):
        return None

    candidates = [
        pd.Timedelta(days=7),
        pd.Timedelta(days=1),
        pd.Timedelta(hours=12),
        pd.Timedelta(hours=8),
        pd.Timedelta(hours=6),
        pd.Timedelta(hours=4),
    ]

    for candidate in candidates:
        approx_steps = int(round(candidate / freq))
        if approx_steps < 2:
            continue
        # Require at least two complete seasons so the seasonal mean is stable.
        if series_length < approx_steps * min_repeats:
            continue
        estimated_cycle = freq * approx_steps
        if abs(estimated_cycle - candidate) <= candidate * 0.1:
            return approx_steps

    return None


def seasonal_trend_forecast(
    series: pd.Series,
    steps: int,
    season_length: int,
    floor_value: Optional[float] = None,
) -> Tuple[pd.Series, bool]:
    """Forecast via additive decomposition: rolling trend plus seasonal mean profile.

    Returns both the forecast series and a flag indicating whether a trend component
    contributed to the result.
    """

    if season_length < 2:
        raise ValueError("season_length must be >= 2")
    if len(series) < season_length * 2:
        raise ComponentInputValidationException(
            "Seasonal trend forecast requires at least two complete seasons.",
            error_code="422",
            invalid_component_inputs=["series"],
        )

    # Focus on the recent portion of the series so current patterns dominate the decomposition.
    tail_length = max(season_length * 4, season_length * 2)
    working_series = series.tail(tail_length)
    values = working_series.to_numpy(dtype=float)
    positions = np.arange(len(values), dtype=float)

    # Smooth the trend with a rolling mean and gently fill remaining gaps afterwards.
    trend_series = (
        working_series.rolling(
            window=season_length, center=True, min_periods=max(2, season_length // 2)
        )
        .mean()
        .interpolate(method="time")
    )
    trend_series = trend_series.ffill().bfill()
    if trend_series.isna().any():
        # Fallback: rely on a simple linear trend if smoothing fails completely.
        slope, intercept = np.polyfit(positions, values, 1)
        trend_series = pd.Series(
            slope * positions + intercept, index=working_series.index
        )

    trend_values = trend_series.to_numpy(dtype=float)

    # Derive the seasonal profile from the average residual for each seasonal position.
    residuals = values - trend_values
    seasonal_pattern = np.zeros(season_length, dtype=float)
    seasonal_counts = np.zeros(season_length, dtype=int)
    for idx, residual in enumerate(residuals):
        slot = idx % season_length
        seasonal_pattern[slot] += residual
        seasonal_counts[slot] += 1
    seasonal_counts = np.where(seasonal_counts == 0, 1, seasonal_counts)
    seasonal_pattern = seasonal_pattern / seasonal_counts
    seasonal_pattern -= seasonal_pattern.mean()

    # Extend the trend component via linear regression on the smoothed trend values.
    slope, _ = np.polyfit(positions, trend_values, 1)
    future_idx = np.arange(len(values), len(values) + steps, dtype=float)

    def build_trend_series(slope_factor: float) -> np.ndarray:
        scaled_slope = slope * slope_factor
        intercept_local = trend_values[-1] - scaled_slope * (len(values) - 1)
        return scaled_slope * future_idx + intercept_local

    trend_forecast = build_trend_series(1.0)

    seasonal_future = seasonal_pattern[
        (np.arange(len(values), len(values) + steps) % season_length)
    ]

    forecast_values = trend_forecast + seasonal_future

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
            # Shrink the slope gradually until the forecast remains within the soft bounds.
            factor = 1.0
            adjusted_forecast = forecast_values
            for _ in range(SEASONAL_TREND_MAX_ITERATIONS):
                factor *= SEASONAL_TREND_REDUCTION_FACTOR
                candidate = build_trend_series(factor) + seasonal_future
                if within_bounds(candidate):
                    adjusted_forecast = candidate
                    trend_forecast = build_trend_series(factor)
                    break
            else:
                trend_used = False
                trend_forecast = build_trend_series(0.0)
                adjusted_forecast = trend_forecast + seasonal_future

            forecast_values = adjusted_forecast

    if not trend_used:
        baseline = float(trend_values[-1])
        trend_forecast = np.full(steps, baseline, dtype=float)
        forecast_values = trend_forecast + seasonal_future

    # Keep the first forecast point in sync with the latest observation.
    offset = float(values[-1] - forecast_values[0])
    forecast_values = forecast_values + offset

    if floor_value is not None and season_length > 0:
        # Detect seasonal slots that usually touch the floor and pin those forecast points.
        floor_tolerance = max(value_range * SEASONAL_FLOOR_TOLERANCE_FRACTION, 1e-9)
        slot_floor_mask = np.zeros(season_length, dtype=bool)
        indices = np.arange(len(values))
        for slot in range(season_length):
            slot_values = values[indices % season_length == slot]
            if slot_values.size == 0:
                continue
            if ((slot_values <= floor_value + floor_tolerance).mean()) >= 0.6:
                slot_floor_mask[slot] = True

        for step in range(1, steps):
            slot = (len(values) + step) % season_length
            if slot_floor_mask[slot]:
                forecast_values[step] = floor_value

    return pd.Series(forecast_values), trend_used


def build_forecast_series(
    base_series: pd.Series, values: pd.Series, freq: pd.Timedelta
) -> pd.Series:
    """Combine forecast values with extrapolated timestamps."""

    start_time = base_series.index[-1] + freq
    forecast_index = pd.date_range(start=start_time, periods=len(values), freq=freq)
    return pd.Series(values.values, index=forecast_index)


def align_seasonal_forecast_start(values: pd.Series, reference_value: float) -> pd.Series:
    if values.empty:
        return values
    offset = reference_value - float(values.iloc[0])
    if offset == 0:
        return values
    return values + offset


def run_selected_method(
    series: pd.Series,
    steps: int,
    frequency: pd.Timedelta,
    floor_value: Optional[float],
    method: str,
) -> Tuple[pd.Series, str, bool, Optional[bool]]:
    seasonal_used = False
    trend_component_used: Optional[bool] = None
    effective_method = method
    season_length_used: Optional[int] = None
    base_length = len(series)

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
                    floor_value=floor_value,
                )
                seasonal_used = True
            except ComponentInputValidationException:
                forecast_values = linear_trend_forecast(series, steps)
                effective_method = "linear_trend"
    elif method == "fourier_trend":
        season_length = infer_season_length_steps(frequency, len(series))
        if season_length is None:
            forecast_values = linear_trend_forecast(series, steps)
            effective_method = "linear_trend"
        else:
            season_length_used = season_length
            try:
                forecast_values = fourier_trend_forecast(
                    series,
                    steps,
                    season_length,
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
        effective_method in {"seasonal_trend", "fourier_trend"}
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

    if effective_method in {"seasonal_trend", "fourier_trend"}:
        # Use the average of the most recent observations to soften seasonal alignment.
        tail_length = min(len(series), SEASONAL_ALIGNMENT_WINDOW)
        tail_window = series.tail(tail_length)
        reference_value = float(tail_window.mean()) if not tail_window.empty else np.nan
        if not np.isnan(reference_value):
            forecast_values = align_seasonal_forecast_start(forecast_values, reference_value)

    if floor_value is not None:
        forecast_values = forecast_values.clip(lower=floor_value)

    return forecast_values, effective_method, seasonal_used, trend_component_used


def auto_select_forecast(
    series: pd.Series,
    steps: int,
    frequency: pd.Timedelta,
    floor_value: Optional[float],
) -> Tuple[pd.Series, str, bool, Optional[bool]]:
    candidates = ["seasonal_trend", "fourier_trend", "linear_trend", "moving_average"]
    last_result: Optional[Tuple[pd.Series, str, bool, Optional[bool]]] = None

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


def build_forecast_plot(
    series: pd.Series,
    forecast: pd.Series,
    effective_method: str,
    seasonal_used: bool,
    trend_used: Optional[bool],
) -> go.Figure:
    """Create a plot closely mirroring the exponential smoothing visualisation."""

    combined = pd.concat([series.tail(1), forecast])
    fig = go.Figure(
        [
            go.Scatter(
                name="Forecast",
                x=combined.index,
                y=combined.values,
                mode="lines",
                line={"color": "#fc7d0b"},
            ),
            go.Scatter(
                name="Observed Value",
                x=series.index,
                y=series.values,
                mode="lines",
                line={"color": "#1f77b4"},
            ),
        ]
    )

    if series.min() <= 0:
        fig.add_hline(y=0, line={"color": "gray", "width": 1, "dash": "dash"})

    fig.update_layout(title="Generic Time Series Forecast")

    return fig


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "series": {"data_type": "SERIES"},
        "forecast_steps": {"data_type": "INT", "default_value": None},
        "forecast_horizon": {"data_type": "STRING", "default_value": "2D"},
        "method": {"data_type": "STRING", "default_value": "auto_select"},
    },
    "outputs": {
        "plot": {"data_type": "PLOTLYJSON"},
    },
    "name": "Generic Fast Time Series Forecast",
    "category": "Time Series Analysis",
    "description": "Quick forecast baseline for arbitrary time series inputs.",
    "version_tag": "1.0.1",
    "id": "5823ad3c-e2eb-4760-bd58-495055288fe4",
    "revision_group_id": "e2f66407-8297-44fe-8a91-0ed6ce72f553",
    "state": "DRAFT",
}


def main(
    *,
    series,
    forecast_steps=None,
    forecast_horizon=None,
    method="auto_select",
):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.

    # Step 1: Validate input parameters
    steps_value: Optional[int] = None
    horizon_value: Optional[pd.Timedelta] = None

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
        # Use the documented default horizon if nothing explicit was supplied.
        horizon_value = DEFAULT_FORECAST_HORIZON

    method_normalised = str(method).lower()
    if method_normalised not in {
        "linear_trend",
        "moving_average",
        "seasonal_trend",
        "fourier_trend",
        "auto_select",
    }:
        raise ComponentInputValidationException(
            "`method` must be one of 'auto_select', 'linear_trend', 'moving_average', 'seasonal_trend', or 'fourier_trend'",
            error_code="422",
            invalid_component_inputs=["method"],
        )

    # Step 2: Resample and clean the series
    prepared, inferred_frequency = resample_time_series_if_needed(series)
    cleaned = clean_time_series_by_interpolation(prepared)
    floor_value = infer_common_floor(cleaned)

    # Step 3: Determine frequency for extrapolating timestamps
    if inferred_frequency is None:
        raise ComponentInputValidationException(
            "Die Zeitachse der Serie weist keinen konsistenten positiven Abstand auf.",
            error_code="422",
            invalid_component_inputs=["series"],
        )
    frequency = inferred_frequency

    if steps_value is None and horizon_value is not None:
        ratio = horizon_value / frequency
        steps_computed = int(np.ceil(ratio)) if ratio > 0 else 0
        steps_value = max(1, steps_computed)
    forecast_steps = steps_value

    # Step 4: Produce forecast values using the selected strategy
    seasonal_used = False
    trend_component_used: Optional[bool] = None
    effective_method = method_normalised
    if method_normalised == "auto_select":
        # Try the seasonal methods first, then fall back to trend-based variants.
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

    # Step 5: Create outputs (series + plot)
    plot = plotly_fig_to_json_dict(
        build_forecast_plot(
            cleaned,
            forecast_series,
            effective_method,
            seasonal_used,
            trend_component_used,
        )
    )

    return {"plot": plot}


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "series",
            "filters": {
                "value": """{
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
}"""
            },
        },
        {"workflow_input_name": "forecast_horizon", "filters": {"value": "2D"}},
        {"workflow_input_name": "method", "filters": {"value": "auto_select"}},
    ]
}
RELEASE_WIRING = {
    "input_wirings": TEST_WIRING_FROM_PY_FILE_IMPORT["input_wirings"],
}

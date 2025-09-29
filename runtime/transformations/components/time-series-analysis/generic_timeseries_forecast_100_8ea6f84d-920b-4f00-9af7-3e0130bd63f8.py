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
- **forecast_steps** (Integer):
    Number of forecasted points. Must be a positive integer.
- **method** (String, default value: "seasonal_trend"):
    Forecasting strategy. Supported values: ``linear_trend``, ``moving_average``,
    ``last_value`` or ``seasonal_trend``.

## Outputs
- **plot** (Plotly JSON):
    Visualisation containing both the history and the forecast, including fallback
    information in the subtitle.

## Remarks
- Designed for robustness and speed rather than absolute accuracy.
- Resampling and interpolation mirror the behaviour of the exponential smoothing component.
- ``moving_average`` automatically limits the window to the available number of points.
- ``linear_trend`` fits a least-squares line to the regularised series.
- ``seasonal_trend`` works in three intuitive steps: smooth the signal with a rolling
  average to capture the slowly changing baseline, measure the typical ups and downs
  for each position within a detected season (for example, each hour of the day), and
  add the two pieces together for the forecast horizon.
- ``last_value`` simply repeats the most recent observation.
- ``seasonal_trend`` is the default as long as enough complete seasons are present.
- If no reliable season length can be inferred, the logic automatically falls back to
  the linear trend.
- The plot subtitle reveals the actually used method and whether the seasonal profile
  was active.

## Example
```json
{
  "series": {
    "2023-01-01T00:00:00Z": 10,
    "2023-01-01T01:00:00Z": 12,
    "2023-01-01T03:00:00Z": 15
  },
  "forecast_steps": 4,
  "method": "moving_average"
}
```
"""

from typing import Optional, Tuple

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from hdutils import ComponentInputValidationException, plotly_fig_to_json_dict


def resample_time_series_if_needed(series: pd.Series) -> Tuple[pd.Series, Optional[pd.Timedelta]]:
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
            "Indices of series must be datetime, but are of type " + str(series.index.dtype),
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
                # Ein minimaler Toleranzpuffer erlaubt kleine Rundungsfehler in den Zeitstempeln.
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
                        resampled = grouped.reindex(regular_index).interpolate(method="time")
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


def infer_common_floor(series: pd.Series, min_fraction: float = 0.2) -> Optional[float]:
    """Detect a frequently occurring lower bound (e.g. 0 for Verbrauchsdaten)."""

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


def last_value_forecast(series: pd.Series, steps: int) -> pd.Series:
    """Repeat the last observed value."""

    return pd.Series([series.iloc[-1]] * steps)


def moving_average_forecast(series: pd.Series, steps: int, window_size: int) -> pd.Series:
    """Forecast with the mean of the trailing window."""

    window = max(1, min(window_size, len(series)))
    avg = float(series.tail(window).mean())
    return pd.Series([avg] * steps)


def linear_trend_forecast(series: pd.Series, steps: int) -> pd.Series:
    """Forecast by extending a least-squares trend over uniformly spaced observations."""

    # Positions 0..n-1 are sufficient because the series is already regularised.
    positions = np.arange(len(series), dtype=float)
    slope, intercept = np.polyfit(positions, series.to_numpy(dtype=float), 1)
    future_positions = np.arange(len(series), len(series) + steps, dtype=float)
    trend_values = slope * future_positions + intercept
    return pd.Series(trend_values)


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
        # Die Serie muss mindestens zwei vollständige Saisons enthalten, damit der Mittelwert stabil ist.
        if series_length < approx_steps * min_repeats:
            continue
        estimated_cycle = freq * approx_steps
        if abs(estimated_cycle - candidate) <= candidate * 0.1:
            return approx_steps

    return None


def seasonal_trend_forecast(series: pd.Series, steps: int, season_length: int) -> pd.Series:
    """Forecast via additive Zerlegung: Trend (gleitend) + saisonales Mittelwertmuster."""

    if season_length < 2:
        raise ValueError("season_length must be >= 2")
    if len(series) < season_length * 2:
        raise ComponentInputValidationException(
            "Seasonal trend forecast benötigt mindestens zwei vollständige Saisons.",
            error_code="422",
            invalid_component_inputs=["series"],
        )

    # Für das Zerlegen reicht ein Tail, damit aktuelle Muster dominieren.
    tail_length = max(season_length * 4, season_length * 2)
    working_series = series.tail(tail_length)
    values = working_series.to_numpy(dtype=float)
    positions = np.arange(len(values), dtype=float)

    # Trend mit gleitendem Durchschnitt glätten; anschließend Lücken sanft auffüllen.
    trend_series = (
        working_series.rolling(window=season_length, center=True, min_periods=max(2, season_length // 2))
        .mean()
        .interpolate(method="time")
    )
    trend_series = trend_series.ffill().bfill()
    if trend_series.isna().any():
        # Fallback: einfacher Lineartrend, falls Glättung komplett fehlschlägt.
        slope, intercept = np.polyfit(positions, values, 1)
        trend_series = pd.Series(slope * positions + intercept, index=working_series.index)

    trend_values = trend_series.to_numpy(dtype=float)

    # Saisonales Profil aus Mittelwert der Trend-residuals je Saisonposition.
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

    # Trend-Fortschreibung: lineare Regression auf geglätteten Trendwerten,
    # allerdings mit gedämpfter Steigung, damit saisonale Muster dominieren.
    slope, intercept = np.polyfit(positions, trend_values, 1)
    damping = np.clip(season_length / len(values), 0.1, 0.5)
    slope *= damping
    # Anker die Gerade an den letzten geglätteten Trendwert, um Sprünge zu vermeiden.
    intercept = trend_values[-1] - slope * (len(values) - 1)
    future_idx = np.arange(len(values), len(values) + steps, dtype=float)
    trend_forecast = slope * future_idx + intercept

    seasonal_future = seasonal_pattern[(np.arange(len(values), len(values) + steps) % season_length)]

    forecast_values = trend_forecast + seasonal_future
    return pd.Series(forecast_values)


def build_forecast_series(
    base_series: pd.Series, values: pd.Series, freq: pd.Timedelta
) -> pd.Series:
    """Combine forecast values with extrapolated timestamps."""

    start_time = base_series.index[-1] + freq
    forecast_index = pd.date_range(start=start_time, periods=len(values), freq=freq)
    return pd.Series(values.values, index=forecast_index)


def _build_method_subtitle(
    requested_method: str, effective_method: str, seasonal_used: bool
) -> str:
    """Compose subtitle showing the actually used method and seasonal status."""

    method_part = (
        f"Verwendete Methode: {effective_method}"
        if effective_method == requested_method
        else f"Verwendete Methode: {effective_method} (Fallback für {requested_method})"
    )
    season_part = f"Saison aktiv: {'ja' if seasonal_used else 'nein'}"
    return f"{method_part} | {season_part}"


def build_forecast_plot(
    series: pd.Series,
    forecast: pd.Series,
    steps: int,
    requested_method: str,
    effective_method: str,
    seasonal_used: bool,
) -> go.Figure:
    """Create a plot closely mirroring the exponential smoothing visualisation."""

    combined = pd.concat([series.tail(1), forecast])
    traces = [
        go.Scatter(
            name="Forecast",
            x=combined.index,
            y=combined.values,
            mode="lines+markers",
            line={"color": "#fc7d0b"},
        ),
        go.Scatter(
            name="Observed Value",
            x=series.index,
            y=series.values,
            mode="lines+markers",
            line={"color": "#1f77b4"},
        ),
    ]

    fig = go.Figure(traces)

    if series.min() <= 0:
        fig.add_hline(y=0, line={"color": "gray", "width": 1, "dash": "dash"})

    fig.update_layout(
        xaxis={
            "showline": True,
            "showgrid": False,
            "showticklabels": True,
            "linecolor": "rgb(204, 204, 204)",
            "linewidth": 2,
            "ticks": "outside",
            "tickfont": {"family": "Arial", "size": 12, "color": "rgb(82, 82, 82)"},
        },
        yaxis={
            "showgrid": True,
            "zeroline": False,
            "showline": True,
            "showticklabels": True,
        },
        autosize=False,
        width=1600,
        height=700,
        margin={"autoexpand": False, "l": 50, "r": 250, "t": 100, "b": 50},
        showlegend=True,
        plot_bgcolor="white",
        annotations=[
            {
                "xref": "paper",
                "yref": "paper",
                "x": 0.0,
                "y": 1.05,
                "xanchor": "left",
                "yanchor": "bottom",
                "text": "Generic Fast Time Series Forecast",
                "font": {"family": "Arial", "size": 30, "color": "rgb(37,37,37)"},
                "showarrow": False,
            },
            {
                "xref": "paper",
                "yref": "paper",
                "x": 0.0,
                "y": 1.0,
                "xanchor": "left",
                "yanchor": "bottom",
                "text": f"Forecast horizon: {steps}",
                "font": {"family": "Arial", "size": 20, "color": "rgb(37,37,37)"},
                "showarrow": False,
            },
            {
                "xref": "paper",
                "yref": "paper",
                "x": 0.0,
                "y": 0.96,
                "xanchor": "left",
                "yanchor": "bottom",
                "text": _build_method_subtitle(requested_method, effective_method, seasonal_used),
                "font": {"family": "Arial", "size": 18, "color": "rgb(90,90,90)"},
                "showarrow": False,
            },
        ],
    )

    return fig


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "series": {"data_type": "SERIES"},
        "forecast_steps": {"data_type": "INT"},
        "method": {"data_type": "STRING", "default_value": "seasonal_trend"},
    },
    "outputs": {
        "plot": {"data_type": "PLOTLYJSON"},
    },
    "name": "Generic Fast Time Series Forecast",
    "category": "Time Series Analysis",
    "description": "Quick forecast baseline for arbitrary time series inputs.",
    "version_tag": "1.0.0",
    "id": "8ea6f84d-920b-4f00-9af7-3e0130bd63f8",
    "revision_group_id": "e2f66407-8297-44fe-8a91-0ed6ce72f553",
    "state": "DRAFT",
}


def main(
    *,
    series,
    forecast_steps,
    method="seasonal_trend",
):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.

    # Step 1: Validate input parameters
    if not isinstance(forecast_steps, int) or forecast_steps <= 0:
        raise ComponentInputValidationException(
            "`forecast_steps` must be a positive integer",
            error_code="422",
            invalid_component_inputs=["forecast_steps"],
        )

    method_normalised = str(method).lower()
    if method_normalised not in {"linear_trend", "moving_average", "last_value", "seasonal_trend"}:
        raise ComponentInputValidationException(
            "`method` must be one of 'linear_trend', 'moving_average', 'seasonal_trend', or 'last_value'",
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

    # Step 4: Produce forecast values using the selected strategy
    seasonal_used = False
    effective_method = method_normalised
    if method_normalised == "moving_average":
        default_window = max(1, min(5, len(cleaned)))
        forecast_values = moving_average_forecast(cleaned, forecast_steps, default_window)
    elif method_normalised == "seasonal_trend":
        season_length = infer_season_length_steps(frequency, len(cleaned))
        if season_length is None:
            # Fallback auf linearen Trend, wenn keine solide Saisonlänge erkannt werden kann.
            forecast_values = linear_trend_forecast(cleaned, forecast_steps)
            effective_method = "linear_trend"
        else:
            try:
                forecast_values = seasonal_trend_forecast(cleaned, forecast_steps, season_length)
                seasonal_used = True
            except ComponentInputValidationException:
                # Wenn die Zerlegung trotz erkannter Saison scheitert, liefern wir den linearen Trend.
                forecast_values = linear_trend_forecast(cleaned, forecast_steps)
                effective_method = "linear_trend"
    elif method_normalised == "linear_trend":
        forecast_values = linear_trend_forecast(cleaned, forecast_steps)
    else:
        forecast_values = last_value_forecast(cleaned, forecast_steps)

    if floor_value is not None:
        forecast_values = forecast_values.clip(lower=floor_value)

    forecast_series = build_forecast_series(cleaned, forecast_values, frequency)

    # Step 5: Create outputs (series + plot)
    plot = plotly_fig_to_json_dict(
        build_forecast_plot(
            cleaned,
            forecast_series,
            forecast_steps,
            method_normalised,
            effective_method,
            seasonal_used,
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
        {"workflow_input_name": "forecast_steps", "filters": {"value": "5"}},
        {"workflow_input_name": "method", "filters": {"value": "seasonal_trend"}},
    ]
}
RELEASE_WIRING = {
    "input_wirings": TEST_WIRING_FROM_PY_FILE_IMPORT["input_wirings"],
}

"""Documentation of Exponential Smoothing Forecast

# Exponential Smoothing Forecast

## Description

The component is designed to generate forecasts for some time series via an *Exponential Smoothing*
model. This function is particularly useful in time series analysis for predicting future values
based on the established patterns in the historical data. It provides a simple yet effective way
to forecast data points for both short-term (in-sample) and long-term (out-of-sample) predictions.

## Inputs

- **series** (Pandas Series):
    The Series containing the time series data. Indices must be Datetime.
- **number_of_forecast_steps** (Integer):
    The number of steps to forecast ahead.
- **seasonal_periods** (Integer, default value: None):
    The number of observations that constitute a full seasonal cycle. If not provided, it will be
    inferred.
- **test_size** (Float, default value: 0):
    The proportion of the dataset to include in the testing set.
- **hyperparameter_tuning_iterations** (Integer, default value: 200):
    The number of iterations for the random search in the hyperparameter tuning.
- **confidence_level** (Float, default value: 0.05):
    Confidence level to calculate the forecast interval.
- **plot_in_sample_forecast** (Boolean, default value: False):
    Whether to include the in-sample forecast on the testing data in the plot.
- **plot_marker** (Boolean, default value: True):
    Whether to include markers in the plot.
- **auto_estimate_seasonality** (Boolean, default value: True):
    If True and `seasonal_periods` is not provided, estimate season length via ACF.
- **acf_threshold** (Float, default value: 0.3):
    Minimum ACF value required to accept a lag as season length.

## Outputs

- **plot** (Plotly Figure):
    Time series plot including forecast and confidence interval.

## Details

This function is essential for users who need to project future values in time series data.
By providing both in-sample and out-of-sample forecasts, it allows users to gauge the model's
performance on known data and to predict future trends. Additionally, confidence intervals for the
forecasts are added. The component is divided into several steps, summarized as follows:
1. Check if the time series has consistent intervals between its indices. If not, resample to the most common interval.
2. Clean the series: replace ±Inf with NaN, interpolate missing values (method="time" for DatetimeIndex, otherwise "linear"), and drop remaining NaNs. Require at least 3 points.
3. Adjust the time series so that all its values are positive.
4. Split the time series into training and testing sets.
5. Optimize hyperparameters for the Exponential Smoothing model using random search.
6. Train an Exponential Smoothing model with optimized hyperparameters.
7. Forecast future values using the trained Exponential Smoothing model.
8. Create a Plotly time series plot including forecasts and confidence intervals.

## Seasonality Estimation

If `seasonal_periods` is not provided, it is estimated from the training data using the autocorrelation function (ACF). The strongest plausible lag above a threshold is selected, subject to the constraint that at least two full seasons are present in the training window.

## Confidence Interval

The forecast confidence interval is only displayed if it is meaningful: at least three valid residual pairs (in-sample vs. test) are available and the RMSE is greater than a tiny threshold; otherwise, the interval is omitted for clarity.

## Fallback

If the hyperparameter search does not yield a valid parameter combination (e.g., due to short series, unsuitable seasonal_periods, or numeric issues), the component falls back to a simple ETS(A,N,N) model without trend or seasonality.

## Example

Example input:
```
{
    "series": {
        "2023-09-04T00:00:00.000Z": 201,
        "2023-09-05T00:00:00.000Z": 194,
        "2023-09-06T00:00:00.000Z": 281,
        "2023-09-07T00:00:00.000Z": 279,
        "2023-09-08T00:00:00.000Z": 375,
        "2023-09-09T00:00:00.000Z": 393,
        "2023-09-10T00:00:00.000Z": 390,
        "2023-09-11T00:00:00.000Z": 220,
        "2023-09-12T00:00:00.000Z": 222,
        "2023-09-13T00:00:00.000Z": 312,
        "2023-09-14T00:00:00.000Z": 277,
        "2023-09-15T00:00:00.000Z": 332,
        "2023-09-16T00:00:00.000Z": 401,
        "2023-09-17T00:00:00.000Z": 400,
        "2023-09-18T00:00:00.000Z": 291,
        "2023-09-19T00:00:00.000Z": 282,
        "2023-09-20T00:00:00.000Z": 316,
        "2023-09-21T00:00:00.000Z": 305,
        "2023-09-22T00:00:00.000Z": 333,
        "2023-09-23T00:00:00.000Z": 398,
        "2023-09-24T00:00:00.000Z": 414
    },
    "steps": 7,
    "seasonal_periods": 7
}
```
"""

import random

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy import stats
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.stattools import acf as sm_acf

from hdutils import ComponentInputValidationException, plotly_fig_to_json_dict


def resample_time_series_if_needed(series: pd.Series):
    """Return a regularly sampled copy of the time series if needed."""

    if not series:
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
    should_resample = False

    if len(ordered) >= 2:
        diffs = ordered.index.to_series().diff().dropna()
        if not diffs.empty:
            positive_diffs = diffs[diffs > pd.Timedelta(0)]
            if not positive_diffs.empty:
                median_diff = positive_diffs.median()
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
                        should_resample = True

    return resampled if should_resample else ordered


def clean_time_series_by_interpolation(series: pd.Series, min_required_points: int = 3):
    """Cleans a time series by replacing Inf with NaN, interpolating, and dropping remaining NaNs.

    Inputs:
    series (Pandas Series):
        The time series with a Datetime index.
    min_required_points (Integer, optional):
        Minimum number of points required after cleaning. Default is 3.

    Outputs:
    series (Pandas Series):
        Cleaned series with no NaN/Inf values.
    """
    # Coerce non-numeric values to NaN to avoid statsmodels errors on object dtypes
    series = pd.to_numeric(series, errors="coerce")
    series = series.replace([np.inf, -np.inf], np.nan)
    method = "time" if pd.api.types.is_datetime64_any_dtype(series.index.dtype) else "linear"
    series = series.interpolate(method=method)
    series = series.dropna()
    if len(series) < min_required_points:
        raise ComponentInputValidationException(
            "After cleaning missing or infinite values, not enough data points remain (>= 3 required)",
            error_code=422,
            invalid_component_inputs=["series"],
        )
    return series


def estimate_seasonal_periods_acf(train: pd.Series, acf_threshold: float = 0.3) -> int | None:
    """Estimate seasonal_periods using ACF on the training series.

    Considers lags in [2, max_period] and returns the lag with the highest
    autocorrelation above `acf_threshold`. Returns None if no suitable lag.
    """
    n = len(train)
    if n < 6:
        return None

    # Plausible upper bound by data length
    max_by_len = max(2, n // 2)
    max_by_freq = max_by_len
    if isinstance(train.index, pd.DatetimeIndex):
        try:
            freq = pd.infer_freq(train.index)
        except ValueError:
            freq = None
        if freq:
            f = freq.upper()
            if f.startswith("H"):
                max_by_freq = min(max_by_len, 24 * 7)
            elif f.startswith("D"):
                max_by_freq = min(max_by_len, 365)
            elif f.startswith("W"):
                max_by_freq = min(max_by_len, 52)
            elif f.startswith("M"):
                max_by_freq = min(max_by_len, 12)

    max_period = max(2, max_by_freq)
    if max_period <= 2:
        return None

    # Compute ACF up to max_period
    try:
        acf_vals = sm_acf(train.values, nlags=max_period, fft=True)
    except ValueError:
        return None

    best_lag = None
    best_val = -1.0
    for lag in range(2, len(acf_vals)):
        val = acf_vals[lag]
        if val >= acf_threshold and val > best_val:
            best_val = val
            best_lag = lag

    return int(best_lag) if best_lag is not None else None


def ensure_positivity(series: pd.Series):
    """Adjusts a time series so that all its values are positive.

    Inputs:
    series (Pandas Series):
        The time series data with Datetime index.

    Outputs:
    series (Pandas Series):
        The adjusted time series with all values being positive.
    min_value (Float):
        Minimum value of the time series.
    """
    # Ensure positivity
    min_value = series.min()
    if min_value <= 0:
        series = series - min_value + 1

    return series, min_value


def series_has_variation(series: pd.Series) -> bool:
    """Return True when the series contains more than one distinct value."""

    if series.empty:
        return False

    return bool(series.diff().dropna().ne(0).any())


def train_test_split_func(series: pd.Series, test_size: float = None):
    """Splits a Series into training and testing sets.

    Inputs:
    series (Pandas Series):
        The Pandas Series to split.
    test_size (Float, optional):
        The proportion of the series to include in the test set. Default is 0.

    Outputs:
    train (Pandas Series):
        Time series containing the training data.
    test (Pandas Series):
        Time series containing the testing data.
    """
    # Parameter validations
    if test_size and (not 0.1 <= test_size <= 0.3):
        raise ComponentInputValidationException(
            "`test_size` should be between 0.1 and 0.3 "
            "to get results having some valid interpretation",
            error_code=422,
            invalid_component_inputs=["test_size"],
        )
    # Split the data into training and testing datasets
    if test_size > 0:
        train, test = train_test_split(series, test_size=test_size, shuffle=False)
    else:
        train = series
        test = series

    return train, test


def hyper_tuning_grid_search(
    train: pd.Series,
    test: pd.Series,
    seasonal_periods: int = None,
    hyperparameter_tuning_iterations: int = 200,
):
    """Optimizes hyperparameters for the Exponential Smoothing model using random search.

    Inputs:
    train (Pandas Series):
        Series containing the training data.
    test (Pandas Series):
        Series containing the test data.
    seasonal_periods (Integer, optional):
        The number of observations that constitute a full seasonal cycle. Default is None.
    hyperparameter_tuning_iterations (Integer, optional):
        The number of iterations for the random search. Default is 200.

    Outputs:
    best_alpha (Float):
        Optimized smoothing parameter for the level component.
    best_beta (Float):
        Optimized smoothing parameter for the trend component.
    best_gamma (Float):
        Optimized smoothing parameter for the seasonal component.
    best_phi (Float):
        Optimized smoothing parameter for the damping trend component.
    best_score (Float):
        Root mean squared error (RMSE) of the respective optimized model.
    best_trend (String):
        Optimized type of trend component.
    best_seasonal (String):
        Optimized type of seasonal component.
    """
    # Parameter validations
    if seasonal_periods and (not isinstance(seasonal_periods, int) or seasonal_periods <= 0):
        raise ComponentInputValidationException(
            "`seasonal_periods` must be a positive integer",
            error_code=422,
            invalid_component_inputs=["seasonal_periods"],
        )
    if (
        not isinstance(hyperparameter_tuning_iterations, int)
        or hyperparameter_tuning_iterations <= 0
    ):
        raise ComponentInputValidationException(
            "`hyperparameter_tuning_iterations` must be a positive integer",
            error_code=422,
            invalid_component_inputs=["hyperparameter_tuning_iterations"],
        )

    train = train.sort_index()

    # Parameter tuning
    best_alpha, best_beta, best_gamma, best_phi, best_score = (
        None,
        None,
        None,
        None,
        float("inf"),
    )
    trend_pos = ["add", "mul", None]
    seasonal_pos = ["add", "mul", None] if seasonal_periods else [None]
    random.seed(42)
    for _ in range(hyperparameter_tuning_iterations):
        alpha = round(random.uniform(0, 1), 2)  # noqa: S311
        beta = round(random.uniform(0, 1), 2)  # noqa: S311
        gamma = round(random.uniform(0, 1), 2)  # noqa: S311
        phi = round(random.uniform(0, 1), 2)  # noqa: S311
        trend = random.choice(trend_pos)  # noqa: S311
        seasonal = random.choice(seasonal_pos)  # noqa: S311
        # Train model (guard against invalid parameter combinations)
        try:
            use_boxcox_param = series_has_variation(train)
            model = ExponentialSmoothing(
                train,
                trend=trend,
                seasonal=seasonal,
                seasonal_periods=seasonal_periods,
                use_boxcox=use_boxcox_param,
                initialization_method="estimated",
            )
            fitted_model = model.fit(
                smoothing_level=alpha,
                smoothing_trend=beta,
                smoothing_seasonal=gamma,
                damping_trend=phi,
            )
            # In-sample forecast
            y_pred = (
                fitted_model.fittedvalues
                if train.equals(test)
                else fitted_model.forecast(len(test))
            )
        except ValueError:
            continue
        # Robust alignment and filtering of NaN/Inf for scoring
        df_eval = pd.concat([test.rename("y_true"), y_pred.rename("y_pred")], axis=1, join="inner")
        df_eval = df_eval.replace([np.inf, -np.inf], np.nan).dropna()
        # Update parameter
        if len(df_eval) > 0:
            score = np.sqrt(mean_squared_error(df_eval["y_pred"], df_eval["y_true"]))
            if score < best_score:
                (
                    best_alpha,
                    best_beta,
                    best_gamma,
                    best_phi,
                    best_score,
                    best_trend,
                    best_seasonal,
                ) = (alpha, beta, gamma, phi, score, trend, seasonal)

    return (
        best_alpha,
        best_beta,
        best_gamma,
        best_phi,
        best_score,
        best_trend,
        best_seasonal,
    )


def train_exponential_smoothing(
    train: pd.Series,
    seasonal_periods: int = None,
    trend: str = None,
    seasonal: str = None,
    alpha: float = None,
    beta: float = None,
    gamma: float = None,
    phi: float = None,
):
    """Trains an Exponential Smoothing model with specified hyperparameters.

    Inputs:
    train (Pandas Series):
        Series containing the training data.
    seasonal_periods (Integer, optional):
        Number of observations that constitute a full seasonal cycle. Default is None.
    trend (String, optional):
        Type of trend component ('add', 'mul', or None). Default is None.
    seasonal (String, optional):
        Type of seasonal component ('add', 'mul', or None). Default is None.
    alpha, beta, gamma, phi (Float, optional):
        Smoothing parameters for level, trend, seasonal, and damping trend. Default is None.

    Outputs:
    model_fit:
        A fitted Exponential Smoothing model.
    """
    # Parameter validations
    if trend not in ["add", "mul", None]:
        raise ComponentInputValidationException(
            "`trend` must be 'add', 'mul', or None",
            error_code=422,
            invalid_component_inputs=["trend"],
        )
    if seasonal not in ["add", "mul", None]:
        raise ComponentInputValidationException(
            "`seasonal` must be 'add', 'mul', or None",
            error_code=422,
            invalid_component_inputs=["seasonal"],
        )
    if seasonal_periods is not None and (
        not isinstance(seasonal_periods, int) or seasonal_periods <= 0
    ):
        raise ComponentInputValidationException(
            "`seasonal_periods` must be a positive integer",
            error_code=422,
            invalid_component_inputs=["seasonal_periods"],
        )
    if not all(x is None or 0 <= x <= 1 for x in [alpha, beta, gamma, phi]):
        raise ComponentInputValidationException(
            "`alpha`, `beta`, `gamma`, `phi` must be between 0 and 1 or None",
            error_code=422,
            invalid_component_inputs=["alpha", "beta", "gamma", "phi"],
        )

    train = train.sort_index()

    # Model training
    # If no seasonal_periods are provided, enforce non-seasonal model
    if seasonal_periods is None:
        seasonal = None
    use_boxcox_param = series_has_variation(train)
    model = ExponentialSmoothing(
        train,
        trend=trend,
        seasonal=seasonal,
        seasonal_periods=seasonal_periods,
        use_boxcox=use_boxcox_param,
        initialization_method="estimated",
    )
    model_fit = model.fit(
        smoothing_level=alpha,
        smoothing_trend=beta,
        smoothing_seasonal=gamma,
        damping_trend=phi,
    )

    return model_fit


def forecast_exponential_smoothing(
    trained_model,
    series: pd.Series,
    test: pd.Series,
    number_of_forecast_steps: int,
    mse: float,
    min_value: float,
    confidence_level: float = 0.05,
):
    """Forecasting future values using a trained Exponential Smoothing model.
    Furthermore, if min_value is negative, the time series and forecasts are readjusted
    to their original scale.

    Inputs:
    trained_model:
        A trained Exponential Smoothing model.
    series (Pandas Series):
        Series containing the underlying time series data.
    test (Pandas Series):
        Series containing the testing data.
    number_of_forecast_steps (Integer):
        The number of steps to forecast ahead.
    mse (Float):
        Root Mean Squared Error (RMSE) evaluated on the testing data.
    min_value (Float):
        Minimum of the time series.
    confidence_level (Float, optional):
        Confidence level used to calculate the forecast interval. Default value is 0.05.

    Outputs:
    series (Pandas Series):
        Series containing the time series data.
    in-sample forecast (Pandas Series):
        The in-sample forecast.
    out-of-sample forecast (Pandas Series):
        The out-of-sample forecast.
    conf_interval_upper_limit (Pandas Series):
        Series containing the upper limits of the confidence interval of the forecast.
    conf_interval_lower_limit (Pandas Series):
        Series containing the lower limits of the confidence interval of the forecast.
    """
    # Parameter validations
    if not isinstance(number_of_forecast_steps, int) or number_of_forecast_steps <= 0:
        raise ComponentInputValidationException(
            "`number_of_forecast_steps` must be a positive integer",
            error_code=422,
            invalid_component_inputs=["number_of_forecast_steps"],
        )
    if not 0 < confidence_level < 1:
        raise ComponentInputValidationException(
            "`confidence_level` must be between 0 and 1",
            error_code=422,
            invalid_component_inputs=["confidence_level"],
        )

    # Forecast
    if series.equals(test):
        in_sample_forecast = np.round(trained_model.fittedvalues, 2)
        out_of_sample_forecast = np.round(trained_model.forecast(steps=number_of_forecast_steps), 2)
    else:
        forecast = trained_model.forecast(steps=number_of_forecast_steps + len(test))
        in_sample_forecast = np.round(forecast[: len(test)], 2)
        out_of_sample_forecast = np.round(forecast[-number_of_forecast_steps:], 2)

    # Confidence interval
    level = 1 - confidence_level / 2
    conf_interval_upper_limit = out_of_sample_forecast + stats.norm.ppf(level) * mse
    conf_interval_lower_limit = out_of_sample_forecast - stats.norm.ppf(level) * mse
    value_before = series.iloc[-1]
    index_before = series.index[-1]
    value_before_series = pd.Series([value_before], index=[index_before])
    conf_interval_upper_limit = pd.concat([value_before_series, conf_interval_upper_limit])
    conf_interval_lower_limit = pd.concat([value_before_series, conf_interval_lower_limit])

    # Sort indices
    series = series.sort_index()
    in_sample_forecast = in_sample_forecast.sort_index()
    out_of_sample_forecast = out_of_sample_forecast.sort_index()
    conf_interval_upper_limit = conf_interval_upper_limit.sort_index()
    conf_interval_lower_limit = conf_interval_lower_limit.sort_index()

    # Add last value of the original series to the out-of-sample forecast
    out_of_sample_forecast = pd.concat([value_before_series, out_of_sample_forecast])

    # If the minimum is negative, the time series data are adjusted to their original values
    if min_value <= 0:
        series = series + min_value - 1
        in_sample_forecast = in_sample_forecast + min_value - 1
        out_of_sample_forecast = out_of_sample_forecast + min_value - 1
        conf_interval_upper_limit = conf_interval_upper_limit + min_value - 1
        conf_interval_lower_limit = conf_interval_lower_limit + min_value - 1

    return (
        series,
        in_sample_forecast,
        out_of_sample_forecast,
        conf_interval_upper_limit,
        conf_interval_lower_limit,
    )


def timeseries_plot_including_predictions(
    series: pd.Series,
    test: pd.Series,
    in_sample_forecast: pd.Series,
    out_of_sample_forecast: pd.Series,
    conf_interval_upper_limit: pd.Series,
    conf_interval_lower_limit: pd.Series,
    mse: float,
    min_value: float,
    plot_in_sample_forecast: bool = False,
    plot_marker: bool = True,
    seasonal_note: str = None,
):
    """Creates a Plotly time series plot including predictions and confidence intervals.

    Inputs:
    series (Pandas Series):
        The Time Series containing the observed values.
    test (Pandas Series):
        The testing data.
    in_sample_forecast (Pandas Series):
        Series containing the in-sample forecast values.
    out_of_sample_forecast (Pandas Series):
        Series containing the out-of-sample forecast values.
    conf_interval_upper_limit (Pandas Series):
        Series containing the upper limit of the confidence interval of the forecast.
    conf_interval_lower_limit (Pandas Series):
        Series containing the lower limit of the confidence interval of the forecast.
    mse (Float):
        Root Mean Squared Error (RMSE) of the optimized Exponential Smoothing model.
    min_value (Float):
        If negative, the zero line is included in the plot.
    plot_in_sample_forecast (Bool, optional):
        If True, it plots the in-sample forecast also. Default value is False.
    plot_marker (Bool, optional):
        Whether to include markers in the plot. Default value is True.

    Outputs:
    fig (Plotly Figure):
        Time series plot including predictions and confidence intervals
    """
    # Decide whether to show confidence interval based on RMSE and residual availability
    df_eval_ci = (
        pd.concat([in_sample_forecast.rename("yhat"), test.rename("y")], axis=1, join="inner")
        .replace([np.inf, -np.inf], np.nan)
        .dropna()
    )
    valid_pairs = len(df_eval_ci)
    show_conf = np.isfinite(mse) and (mse > 1e-8) and (valid_pairs >= 3)

    traces = []
    if show_conf:
        traces.extend(
            [
                go.Scatter(
                    name="Confidence Interval",
                    x=conf_interval_upper_limit.index,
                    y=conf_interval_upper_limit,
                    mode="lines",
                    line={"width": 0},
                    showlegend=False,
                ),
                go.Scatter(
                    name="Confidence Interval",
                    x=conf_interval_lower_limit.index,
                    y=conf_interval_lower_limit,
                    mode="lines",
                    line={"width": 0},
                    showlegend=True,
                    fillcolor="rgba(68, 68, 68, 0.3)",
                    fill="tonexty",
                ),
            ]
        )

    # Forecast traces
    traces.append(
        go.Scatter(
            name="Out-of-Sample Forecast" if plot_in_sample_forecast else "Forecast",
            x=out_of_sample_forecast.index,
            y=out_of_sample_forecast,
            mode="lines+markers" if plot_marker else "lines",
            line={"color": "#fc7d0b"},
        )
    )
    if plot_in_sample_forecast:
        traces.append(
            go.Scatter(
                name="In-Sample Forecast",
                x=in_sample_forecast.index,
                y=in_sample_forecast,
                mode="lines+markers" if plot_marker else "lines",
                line={"color": "#fc7d0b", "dash": "dash"},
            )
        )
    traces.append(
        go.Scatter(
            name="Observed Value",
            x=series.index,
            y=series,
            mode="lines+markers" if plot_marker else "lines",
            line={"color": "#1f77b4"},
        )
    )

    fig = go.Figure(traces)

    if min_value <= 0:
        fig.add_hline(y=0, line={"color": "gray", "width": 1, "dash": "dash"})

    # Layout options
    fig.update_layout(
        xaxis={
            "showline": True,
            "showgrid": False,
            "showticklabels": True,
            "linecolor": "rgb(204, 204, 204)",
            "linewidth": 2,
            "ticks": "outside",
            "tickfont": {
                "family": "Arial",
                "size": 12,
                "color": "rgb(82, 82, 82)",
            },
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
        margin={
            "autoexpand": False,
            "l": 50,
            "r": 250,
            "t": 100,
            "b": 50,
        },
        showlegend=True,
        plot_bgcolor="white",
    )

    # Annotations (subtitle removed for clarity)
    annotations = []

    annotations.append(
        {
            "xref": "paper",
            "yref": "paper",
            "x": 0.0,
            "y": 1.05,
            "xanchor": "left",
            "yanchor": "bottom",
            "text": "Time Series Forecast, based on some Exponential Smoothing Model",
            "font": {"family": "Arial", "size": 30, "color": "rgb(37,37,37)"},
            "showarrow": False,
        }
    )
    if seasonal_note:
        annotations.append(
            {
                "xref": "paper",
                "yref": "paper",
                "x": 0.0,
                "y": 1.0,
                "xanchor": "left",
                "yanchor": "bottom",
                "text": seasonal_note,
                "font": {"family": "Arial", "size": 16, "color": "rgb(90,90,90)"},
                "showarrow": False,
            }
        )
    fig.update_layout(annotations=annotations)

    return fig


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "series": {"data_type": "SERIES"},
        "number_of_forecast_steps": {"data_type": "INT"},
        "seasonal_periods": {"data_type": "INT", "default_value": None},
        "test_size": {"data_type": "FLOAT", "default_value": 0.0},
        "hyperparameter_tuning_iterations": {"data_type": "INT", "default_value": 200},
        "confidence_level": {"data_type": "FLOAT", "default_value": 0.05},
        "plot_in_sample_forecast": {"data_type": "BOOLEAN", "default_value": False},
        "plot_marker": {"data_type": "BOOLEAN", "default_value": True},
        "auto_estimate_seasonality": {"data_type": "BOOLEAN", "default_value": True},
        "acf_threshold": {"data_type": "FLOAT", "default_value": 0.3},
    },
    "outputs": {
        "plot": {"data_type": "PLOTLYJSON"},
    },
    "name": "Exponential Smoothing",
    "category": "Time Series Analysis",
    "description": "Exponential Smoothing Plot",
    "version_tag": "1.0.1",
    "id": "8c5f6a7e-2b1d-4f6c-9d9e-c7e3b4a2c1d0",
    "revision_group_id": "b1e582b3-b2a8-47a8-a019-e0a0ba0f1d87",
    "state": "RELEASED",
    "released_timestamp": "2025-09-15T12:00:00+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(
    *,
    series,
    number_of_forecast_steps,
    seasonal_periods=None,
    test_size=0.0,
    hyperparameter_tuning_iterations=200,
    confidence_level=0.05,
    plot_in_sample_forecast=False,
    plot_marker=True,
    auto_estimate_seasonality=True,
    acf_threshold=0.3,
):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    # Step 1: Check if the time series has consistent intervals between its indices.
    series = resample_time_series_if_needed(series=series)
    # Step 2: Clean series (handle NaN/Inf values via interpolation)
    series = clean_time_series_by_interpolation(series=series)
    # Step 3: Ensure positivity.
    series, min_value = ensure_positivity(series=series)
    # Step 4: Split the time series into training and testing sets.
    train, test = train_test_split_func(series=series, test_size=test_size)
    # Auto-estimate seasonal_periods if not provided
    seasonal_note = None
    if seasonal_periods is None and auto_estimate_seasonality:
        est_sp = estimate_seasonal_periods_acf(train, acf_threshold=acf_threshold)
        if est_sp is not None and len(train) >= 2 * est_sp:
            seasonal_periods = est_sp
            seasonal_note = f"Estimated season length: {est_sp}"
    # Validate seasonal_periods against training length: require >= 2 full seasons
    if seasonal_periods is not None and len(train) < 2 * int(seasonal_periods):
        raise ComponentInputValidationException(
            "seasonal_periods requires at least 2 full seasons in training data",
            error_code=422,
            invalid_component_inputs=["seasonal_periods"],
        )
    # Step 5: Optimize hyperparameters for the Exponential Smoothing model using random search.
    (
        best_alpha,
        best_beta,
        best_gamma,
        best_phi,
        best_score,
        best_trend,
        best_seasonal,
    ) = hyper_tuning_grid_search(
        train=train,
        test=test,
        seasonal_periods=seasonal_periods,
        hyperparameter_tuning_iterations=hyperparameter_tuning_iterations,
    )
    # Step 6: Train Exponential Smoothing model (with fallback if tuning failed)
    if np.isfinite(best_score):
        model_fit = train_exponential_smoothing(
            train=train,
            seasonal_periods=seasonal_periods,
            trend=best_trend,
            seasonal=best_seasonal,
            alpha=best_alpha,
            beta=best_beta,
            gamma=best_gamma,
            phi=best_phi,
        )
    else:
        # Fallback to a simple ETS(A,N,N) model with auto-estimated params
        model_fit = train_exponential_smoothing(
            train=train,
            seasonal_periods=seasonal_periods,
            trend=None,
            seasonal=None,
            alpha=None,
            beta=None,
            gamma=None,
            phi=None,
        )
        # Compute a robust RMSE for display/CI
        y_pred_fb = model_fit.fittedvalues if train.equals(test) else model_fit.forecast(len(test))
        df_eval_fb = (
            pd.concat(
                [test.rename("y_true"), y_pred_fb.rename("y_pred")],
                axis=1,
                join="inner",
            )
            .replace([np.inf, -np.inf], np.nan)
            .dropna()
        )
        best_score = (
            float(np.sqrt(mean_squared_error(df_eval_fb["y_pred"], df_eval_fb["y_true"])))
            if len(df_eval_fb) > 0
            else 0.0
        )
    # Step 7: Forecast future values and confidence intervals. If min_value is negative,
    #           the time series data are adjusted to their original values.
    (
        series,
        in_sample_forecast,
        out_of_sample_forecast,
        conf_interval_upper_limit,
        conf_interval_lower_limit,
    ) = forecast_exponential_smoothing(
        trained_model=model_fit,
        series=series,
        test=test,
        number_of_forecast_steps=number_of_forecast_steps,
        mse=best_score,
        min_value=min_value,
        confidence_level=confidence_level,
    )
    # Step 8: Create a Plotly time series plot including forecasts and confidence intervals.
    fig = timeseries_plot_including_predictions(
        series=series,
        test=test,
        in_sample_forecast=in_sample_forecast,
        out_of_sample_forecast=out_of_sample_forecast,
        conf_interval_upper_limit=conf_interval_upper_limit,
        conf_interval_lower_limit=conf_interval_lower_limit,
        mse=best_score,
        min_value=min_value,
        plot_in_sample_forecast=plot_in_sample_forecast,
        plot_marker=plot_marker,
        seasonal_note=seasonal_note,
    )

    return {"plot": plotly_fig_to_json_dict(fig)}


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "series",
            "filters": {
                "value": '{\n    "2023-09-04T00:00:00.000Z": 201,\n    "2023-09-05T00:00:00.000Z": 194,\n    "2023-09-06T00:00:00.000Z": 281,\n    "2023-09-07T00:00:00.000Z": 279,\n    "2023-09-08T00:00:00.000Z": 375,\n    "2023-09-09T00:00:00.000Z": 393,\n    "2023-09-10T00:00:00.000Z": 390,\n    "2023-09-11T00:00:00.000Z": 220,\n    "2023-09-12T00:00:00.000Z": 222,\n    "2023-09-13T00:00:00.000Z": 312,\n    "2023-09-14T00:00:00.000Z": 277,\n    "2023-09-15T00:00:00.000Z": 332,\n    "2023-09-16T00:00:00.000Z": 401,\n    "2023-09-17T00:00:00.000Z": 400,\n    "2023-09-18T00:00:00.000Z": 291,\n    "2023-09-19T00:00:00.000Z": 282,\n    "2023-09-20T00:00:00.000Z": 316,\n    "2023-09-21T00:00:00.000Z": 305,\n    "2023-09-22T00:00:00.000Z": 333,\n    "2023-09-23T00:00:00.000Z": 398,\n    "2023-09-24T00:00:00.000Z": 414\n}\n'
            },
        },
        {"workflow_input_name": "number_of_forecast_steps", "filters": {"value": "7"}},
        {"workflow_input_name": "seasonal_periods", "filters": {"value": "7"}},
    ]
}
RELEASE_WIRING = {
    "input_wirings": [
        {
            "workflow_input_name": "series",
            "filters": {
                "value": '{\n    "2023-09-04T00:00:00.000Z": 201,\n    "2023-09-05T00:00:00.000Z": 194,\n    "2023-09-06T00:00:00.000Z": 281,\n    "2023-09-07T00:00:00.000Z": 279,\n    "2023-09-08T00:00:00.000Z": 375,\n    "2023-09-09T00:00:00.000Z": 393,\n    "2023-09-10T00:00:00.000Z": 390,\n    "2023-09-11T00:00:00.000Z": 220,\n    "2023-09-12T00:00:00.000Z": 222,\n    "2023-09-13T00:00:00.000Z": 312,\n    "2023-09-14T00:00:00.000Z": 277,\n    "2023-09-15T00:00:00.000Z": 332,\n    "2023-09-16T00:00:00.000Z": 401,\n    "2023-09-17T00:00:00.000Z": 400,\n    "2023-09-18T00:00:00.000Z": 291,\n    "2023-09-19T00:00:00.000Z": 282,\n    "2023-09-20T00:00:00.000Z": 316,\n    "2023-09-21T00:00:00.000Z": 305,\n    "2023-09-22T00:00:00.000Z": 333,\n    "2023-09-23T00:00:00.000Z": 398,\n    "2023-09-24T00:00:00.000Z": 414\n}\n'
            },
        },
        {"workflow_input_name": "number_of_forecast_steps", "filters": {"value": "7"}},
        {"workflow_input_name": "seasonal_periods", "filters": {"value": "7"}},
    ]
}

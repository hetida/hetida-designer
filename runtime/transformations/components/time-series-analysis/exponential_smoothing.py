"""Module Docstring of Exponential Smoothing Forecast

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
    Significance level to compare the p-value with when analyzing the residuals of the model,
    and to calculate the confidence interval for the forecast.
- **plot_in_sample_forecast** (Boolean, default value: False):
    Whether to include the in-sample forecast on the testing data in the plot.
- **plot_marker** (Boolean, default value: True):
    Whether to include markers in the plot.

## Outputs

- **plot** (Plotly Figure):
    Time series plot including forecast and confidence interval.

## Details

This function is essential for users who need to project future values in time series data.
By providing both in-sample and out-of-sample forecasts, it allows users to gauge the model's
performance on known data and to predict future trends. Additionally, confidence intervals for the
forecasts are added. The component is devided into several steps, that can be summarized as follows:
1. Check if the time series has consistent intervals between its indices.
If not, resample the series to the most common interval.
2. Adjust the time series so that all its values are positive.
3. Split the time series into training and testing sets.
4. Optimize hyperparameters for the Exponential Smoothing model using random search.
5. Train some Exponential Smoothing model with optimized hyperparameters.
6. Forecast future values using the trained Exponential Smoothing model.
7. Create a Plotly time series plot including forecasts and confidence intervals.

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

from hdutils import ComponentInputValidationException, plotly_fig_to_json_dict


def resample_time_series_if_needed(series: pd.Series):
    """Checks if a time series has consistent intervals between its indices.
    If not, it resamples the series to the most common interval.

    Inputs:
    series (Pandas Series):
        The time series with a Datetime index.

    Outputs:
    series (Pandas Series):
        The resampled time series if necessary.
    """
    # Parameter validations
    if len(series) == 0:
        raise ComponentInputValidationException(
            "The input data must not be empty!",
            error_code="EmptyDataFrame",
            invalid_component_inputs=["series"],
        )
    if pd.api.types.is_datetime64_any_dtype(series.index.dtype) is False:
        raise ComponentInputValidationException(
            "Indices of series must be datetime, but are of type " + str(series.index.dtype),
            error_code="422",
            invalid_component_inputs=["series"],
        )

    # Calculate differences between timestamps
    time_diffs = series.index.to_series().diff().dropna()

    # Determine the "normal" interval as the most common value in the differences
    normal_diff = time_diffs.value_counts().idxmax()

    # Check if all intervals are equal to the "normal" interval
    if not all(time_diffs == normal_diff):
        # Create a new index with the "normal" interval
        new_index = pd.date_range(
            start=series.index.min(), end=series.index.max(), freq=normal_diff
        )
        # Resample the series to the new index
        series = series.reindex(new_index).interpolate()

    return series


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
        Mean squared error (MSE) of the respective optimized model.
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
    pos = ["add", "mul", None]
    random.seed(42)
    for _ in range(hyperparameter_tuning_iterations):
        alpha = round(random.uniform(0, 1), 2)  # noqa: S311
        beta = round(random.uniform(0, 1), 2)  # noqa: S311
        gamma = round(random.uniform(0, 1), 2)  # noqa: S311
        phi = round(random.uniform(0, 1), 2)  # noqa: S311
        trend = random.choice(pos)  # noqa: S311
        seasonal = random.choice(pos)  # noqa: S311
        # Train model
        model = ExponentialSmoothing(
            train,
            trend=trend,
            seasonal=seasonal,
            seasonal_periods=seasonal_periods,
            use_boxcox=True,
            initialization_method="estimated",
        )
        fitted_model = model.fit(
            smoothing_level=alpha,
            smoothing_trend=beta,
            smoothing_seasonal=gamma,
            damping_trend=phi,
        )
        # In-sample forecast
        if train.equals(test):
            y_pred = fitted_model.fittedvalues
        else:
            y_pred = fitted_model.forecast(len(test))
        test = test[~test.isin([np.nan, np.inf, -np.inf])]
        y_pred = y_pred[~y_pred.isin([np.nan, np.inf, -np.inf])]
        # Update parameter
        if len(test) == len(y_pred):
            score = np.sqrt(mean_squared_error(y_pred, test))
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
    model = ExponentialSmoothing(
        train,
        trend=trend,
        seasonal=seasonal,
        seasonal_periods=seasonal_periods,
        use_boxcox=True,
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
        Mean Squared Error evaluated on the testing data.
    min_value (Float):
        Minimum of the time series.
    confidence_level (Float, optional):
        Significance level to calculate the confidence interval. Default value is 0.05.

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
    confidence_level: float = 0.05,
    plot_in_sample_forecast: bool = False,
    plot_marker: bool = True,
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
        Mean Squared Error of the optimized Exponential Smoothing model.
    min_value (Float):
        If negative, the zero line is included in the plot.
    confidence_level (Float, optional):
        Significance level to compare the p-value of the Shapiro-Wilk Test with.
        Default value is 0.05.
    plot_in_sample_forecast (Bool, optional):
        If True, it plots the in-sample forecast also. Default value is False.
    plot_marker (Bool, optional):
        Whether to include markers in the plot. Default value is True.

    Outouts:
    fig (Plotly Figure):
        Time series plot including predictions and confindence intervals
    """
    # Creating the figure
    if plot_in_sample_forecast:
        fig = go.Figure(
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
                go.Scatter(
                    name="Out-of-Sample Forecast",
                    x=out_of_sample_forecast.index,
                    y=out_of_sample_forecast,
                    mode="lines+markers" if plot_marker else "lines",
                    line={"color": "#fc7d0b"},
                ),
                go.Scatter(
                    name="In-Sample Forecast",
                    x=in_sample_forecast.index,
                    y=in_sample_forecast,
                    mode="lines+markers" if plot_marker else "lines",
                    line={"color": "#fc7d0b", "dash": "dash"},
                ),
                go.Scatter(
                    name="Observed Value",
                    x=series.index,
                    y=series,
                    mode="lines+markers" if plot_marker else "lines",
                    line={"color": "#1f77b4"},
                ),
            ]
        )
    else:
        fig = go.Figure(
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
                go.Scatter(
                    name="Forecast",
                    x=out_of_sample_forecast.index,
                    y=out_of_sample_forecast,
                    mode="lines+markers" if plot_marker else "lines",
                    line={"color": "#fc7d0b"},
                ),
                go.Scatter(
                    name="Observed Value",
                    x=series.index,
                    y=series,
                    mode="lines+markers" if plot_marker else "lines",
                    line={"color": "#1f77b4"},
                ),
            ]
        )

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

    # Perform the Shapiro-Wilk Test for normality of residuals
    residuals = sorted([x - y for x, y in zip(in_sample_forecast.values, test.values, strict=True)])
    p_value = np.round(stats.shapiro(residuals)[1], 2)

    # Annotations
    annotations = []
    if p_value > confidence_level:
        conf_text = (
            f"and the residuals are likely normal. Thus, the {int((1-confidence_level)*100)}% "
            "confidence interval does have a valid interpretation."
        )
    else:
        conf_text = (
            f"and the residuals are likely not normal. Thus, the {int((1-confidence_level)*100)}% "
            "confidence interval does not have a valid interpretation."
        )

    annotations.append(
        {
            "xref": "paper",
            "yref": "paper",
            "x": 0.0,
            "y": 1.05,
            "xanchor": "left",
            "yanchor": "bottom",
            "text": (
                "Time Series Plot including Forecast and Confidence Interval, "
                "based on some Exponential Smoothing model"
            ),
            "font": {"family": "Arial", "size": 30, "color": "rgb(37,37,37)"},
            "showarrow": False,
        }
    )
    annotations.append(
        {
            "xref": "paper",
            "yref": "paper",
            "x": 0.0,
            "y": 1.0,
            "xanchor": "left",
            "yanchor": "bottom",
            "text": f"The mean squared error (MSE) of the model is {np.round(mse, 2)} {conf_text}",
            "font": {"family": "Arial", "size": 20, "color": "rgb(37,37,37)"},
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
        "test_size": {"data_type": "FLOAT", "default_value": 0},
        "hyperparameter_tuning_iterations": {"data_type": "INT", "default_value": 200},
        "confidence_level": {"data_type": "FLOAT", "default_value": 0.05},
        "plot_in_sample_forecast": {"data_type": "BOOLEAN", "default_value": False},
        "plot_marker": {"data_type": "BOOLEAN", "default_value": True},
    },
    "outputs": {
        "plot": {"data_type": "PLOTLYJSON"},
    },
    "name": "Exponential Smoothing",
    "category": "Time Series Analysis",
    "description": "Exponential Smoothing Plot",
    "version_tag": "1.0.0",
    "id": "61ef085b-0a83-443b-a4ee-dc1cc6ce1077",
    "revision_group_id": "b1e582b3-b2a8-47a8-a019-e0a0ba0f1d87",
    "state": "RELEASED",
}


def main(
    *,
    series,
    number_of_forecast_steps,
    seasonal_periods=None,
    test_size=0,
    hyperparameter_tuning_iterations=200,
    confidence_level=0.05,
    plot_in_sample_forecast=False,
    plot_marker=True,
):
    """entrypoint function for this component"""
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    # Step 1: Check if the time series has consistent intervals between its indices.
    series = resample_time_series_if_needed(series=series)
    # Step 2: Ensure positivity.
    series, min_value = ensure_positivity(series=series)
    # Step 3: Split the time series into training and testing sets.
    train, test = train_test_split_func(series=series, test_size=test_size)
    # Step 4: Optimize hyperparameters for the Exponential Smoothing model using random search.
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
    # Step 5: Train some Exponential Smoothing model with optimized hyperparameters.
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
    # Step 6: Forecast future values and confidence intervals. If min_value is negative,
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
    # Step 7: Create a Plotly time series plot including forecasts and confidence intervals.
    fig = timeseries_plot_including_predictions(
        series=series,
        test=test,
        in_sample_forecast=in_sample_forecast,
        out_of_sample_forecast=out_of_sample_forecast,
        conf_interval_upper_limit=conf_interval_upper_limit,
        conf_interval_lower_limit=conf_interval_lower_limit,
        mse=best_score,
        confidence_level=confidence_level,
        min_value=min_value,
        plot_in_sample_forecast=plot_in_sample_forecast,
        plot_marker=plot_marker,
    )

    return {"plot": plotly_fig_to_json_dict(fig)}


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "series",
            "adapter_id": "direct_provisioning",
            "filters": {
                "value": """{
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
}
"""
            },
        },
        {
            "workflow_input_name": "number_of_forecast_steps",
            "adapter_id": "direct_provisioning",
            "filters": {"value": 7},
        },
        {
            "workflow_input_name": "seasonal_periods",
            "adapter_id": "direct_provisioning",
            "use_default_value": False,
            "filters": {"value": 7},
        },
    ]
}

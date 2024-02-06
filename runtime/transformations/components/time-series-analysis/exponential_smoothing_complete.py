"""Module Docstring of Exponential Smoothing Forecast Plot

# Exponential Smoothing Forecast Plot

## Description

The component is designed to generate forecasts for some time series via an Exponential Smoothing
model. This function is particularly useful in time series analysis for predicting future values
based on the established patterns in the historical data. It provides a simple yet effective way
to forecast data points for both short-term (in-sample) and long-term (out-of-sample) predictions.

## Inputs

- **series** (Pandas Series):
    The Series containing the time series data.
- **steps** (Integer):
    The number of steps to forecast ahead.
- **test_size** (Float, default value: 0.3):
    The proportion of the dataset to include in the test split.
- **shuffle** (Boolean, default value: False):
    Whether or not to shuffle the data before splitting.
- **seasonal_periods** (Integer, default value: None):
    The number of observations that constitute a full seasonal cycle.
- **use_boxcox** (Boolean, default value: True): Whether to apply Box-Cox transformation.
- **initialization_method** (String, default value: "estimated"):
    Method for initializing the model ('estimated', 'heuristic', 'legacy-heuristic', None).
- **iterations** (Integer, default value: 100):
    The number of iterations for the random search in the hyperparameter tuning.
- **alpha** (Float, default value: 0.05):
    Significance level to compare the p-value with.

## Outputs

- **fig** (Plotly Figure):
    Time series plot including in-sample and out-of-sample predictions.

## Details

This function is essential for users who need to project future values in time series data.
By providing both in-sample and out-of-sample forecasts, it allows users to gauge the model's
performance on known data and to predict future trends. The component is devided in several steps,
that can be summarized as follows:
1. Split the time series into training and testing sets
2. Optimize hyperparameters for the Exponential Smoothing model using random search
3. Train some Exponential Smoothing model with optimized hyperparameters
4. Forecast future values using the trained Exponential Smoothing model
5. Decide whether to include some confidence interval for the out-of-sample forecast,
based on the normality of the residuals specified by the Shapiro-Wilk Test
6. Create a Plotly time series plot including in-sample and out-of-sample forecasts,
with optional confidence intervals

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
        "2023-09-12T00:00:00.000Z": 262,
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
    "steps": 7
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

from hetdesrun.runtime.exceptions import ComponentInputValidationException
from hetdesrun.utils import plotly_fig_to_json_dict


def train_test_split_func(
    series: pd.Series,
    test_size: float = 0.3,
    shuffle: bool = False
):
    """Splits a Series into training and testing sets.

    Inputs:
    series (Pandas Series): T
        he Pandas Series to split.
    test_size (Float, optional):
        The proportion of the series to include in the test set. Default is 0.3.
    shuffle (Bool, optional):
        Whether or not to shuffle the data before splitting. Default is False.

    Outputs:
    train (Pandas Series): A series containing the training data.
    test (Pandas Series): A series containing the testing data.
    """
    # Parameter validations
    if len(series) == 0:
        raise ComponentInputValidationException(
            "The input data must not be empty!",
            error_code="EmptyDataFrame",
            invalid_component_inputs=["series"],
        )
    try:
        series.index = pd.to_datetime(series.index, utc=True)
    except:
        raise ComponentInputValidationException(
            "Indices of series must be datetime, but are of type "
            + str(series.index.dtype),
            error_code="422",
            invalid_component_inputs=["series"],
        )
    if not 0 < test_size < 1:
        raise ComponentInputValidationException(
            "`test_size` must be between 0 and 1",
            error_code=422,
            invalid_component_inputs=["test_size"],
        )

    # Split the data into training and testing datasets
    train, test = train_test_split(series, test_size=test_size, shuffle=shuffle)

    return train, test

def hyper_tuning_grid_search(
    train: pd.Series,
    test: pd.Series,
    seasonal_periods: int=None,
    iterations: int=200,
    use_boxcox: bool=True,
    initialization_method: str="estimated"
):
    """Optimizes hyperparameters for the Exponential Smoothing model using random search.

    Inputs:
    train (Pandas Series):
        Series containing the training data.
    test (Pandas Series):
        Series containing the test data.
    seasonal_periods (Integer, optional):
        The number of observations that constitute a full seasonal cycle. Default is None.
    use_boxcox (Bool, optional): Whether to apply Box-Cox transformation. Default is True.
    initialization_method (String, optional):
        Method for initializing the model ('estimated', 'heuristic', 'legacy-heuristic', None).
        Default is 'estimated'.
    iterations (Integer, optional):
        The number of iterations for the random search. Default is 200.

    Outputs:
    Best alpha, beta, gamma, phi values, trend, seasonal and the corresponding mean squared error.
    """
    # Parameter validations
    if seasonal_periods and (not isinstance(seasonal_periods, int) or seasonal_periods <= 0):
        raise ComponentInputValidationException(
        "seasonal_periods must be a positive integer",
        error_code=422,
        invalid_component_inputs=["seasonal_periods"],
        )
    if not isinstance(iterations, int) or iterations <= 0:
        raise ComponentInputValidationException(
            "iterations must be a positive integer",
            error_code=422,
            invalid_component_inputs=["iterations"],
        )

    train = train.sort_index()

    # Parameter tuning
    best_alpha, best_beta, best_gamma, best_phi, best_score = None, None, None, None, float("inf")
    pos = ["add", "mul", None]
    random.seed(42)
    for _ in range(iterations):
        alpha = round(random.uniform(0, 1), 2)
        beta = round(random.uniform(0, 1), 2)
        gamma = round(random.uniform(0, 1), 2)
        phi = round(random.uniform(0, 1), 2)
        trend = random.choice(pos)
        seasonal = random.choice(pos)

        model = ExponentialSmoothing(
            train,
            trend=trend,
            seasonal=seasonal,
            seasonal_periods=seasonal_periods,
            use_boxcox=use_boxcox,
            initialization_method=initialization_method
        )
        fitted_model = model.fit(
            smoothing_level=alpha,
            smoothing_trend=beta,
            smoothing_seasonal=gamma,
            damping_trend=phi
        )
        y_pred = fitted_model.forecast(len(test))
        if len(test) == len(y_pred.dropna()):
            score = np.sqrt(mean_squared_error(y_pred, test))
            if score < best_score:
                best_alpha, best_beta, best_gamma, best_phi, best_score, best_trend, best_seasonal \
                    = alpha, beta, gamma, phi, score, trend, seasonal

    return best_alpha, best_beta, best_gamma, best_phi, best_score, best_trend, best_seasonal

def train_exponential_smoothing(
    series: pd.Series,
    seasonal_periods: int=None,
    trend: str=None,
    seasonal: str=None,
    alpha: float=None,
    beta: float=None,
    gamma: float=None,
    phi: float=None,
    use_boxcox: bool=True,
    initialization_method: str="estimated"
):
    """Trains an Exponential Smoothing model with specified hyperparameters.

    Inputs:
    series (Pandas Series):
        Series containing the training data.
    seasonal_periods (Integer, optional):
        Number of observations that constitute a full seasonal cycle. Default is None.
    trend (String, optional):
        Type of trend component ('add', 'mul', or None). Default is None.
    seasonal (String, optional):
        Type of seasonal component ('add', 'mul', or None). Default is None.
    alpha, beta, gamma, phi (Float, optional):
        Smoothing parameters for level, trend, seasonal, and damping trend. Default is None.
    use_boxcox (Bool, optional):
        Whether to apply Box-Cox transformation. Default is True.
    initialization_method (String, optional):
        Method for initializing the model ('estimated', 'heuristic', 'legacy-heuristic', None).
        Default is 'estimated'.

    Outputs:
    model_fit: A fitted Exponential Smoothing model.
    """
    # Parameter validations
    if trend not in ["add", "mul", None]:
        raise ComponentInputValidationException(
            "trend must be 'add', 'mul', or None",
            error_code=422,
            invalid_component_inputs=["trend"],
        )
    if seasonal not in ["add", "mul", None]:
        raise ComponentInputValidationException(
            "seasonal must be 'add', 'mul', or None",
            error_code=422,
            invalid_component_inputs=["seasonal"],
        )
    if seasonal_periods is not None and (not isinstance(seasonal_periods, int)
                                         or seasonal_periods <= 0):
        raise ComponentInputValidationException(
            "seasonal_periods must be a positive integer",
            error_code=422,
            invalid_component_inputs=["seasonal_periods"],
        )
    if not all(x is None or 0 <= x <= 1 for x in [alpha, beta, gamma, phi]):
        raise ComponentInputValidationException(
            "alpha, beta, gamma, phi must be between 0 and 1 or None",
            error_code=422,
            invalid_component_inputs=["alpha", "beta", "gamma", "phi"],
        )
    valid_initialization_methods = ["estimated", "heuristic", "legacy-heuristic", "none"]
    if initialization_method not in valid_initialization_methods:
        raise ComponentInputValidationException(
            f"initialization_method must be one of {valid_initialization_methods}",
            error_code=422,
            invalid_component_inputs=["initialization_method"],
        )

    series = series.sort_index()

    # Model training
    model = ExponentialSmoothing(
        series,
        trend=trend,
        seasonal=seasonal,
        seasonal_periods=seasonal_periods,
        use_boxcox=use_boxcox,
        initialization_method=initialization_method
    )
    model_fit = model.fit(
        smoothing_level=alpha,
        smoothing_trend=beta,
        smoothing_seasonal=gamma,
        damping_trend=phi
    )

    return model_fit

def forecast_exponential_smoothing(
    trained_model,
    series: pd.Series,
    steps: int
):
    """Forecasting future values using a trained Exponential Smoothing model.

    Inputs:
    trained_model: A trained Exponential Smoothing model.
    series (Pandas Series): Series containing the testing data.
    steps (Integer): The number of steps to forecast ahead.

    Outputs:
    Tuple containing in-sample forecast and out-of-sample forecast.
    """
    # Parameter validations
    if not isinstance(steps, int) or steps <= 0:
        raise ComponentInputValidationException(
            "steps must be a positive integer",
            error_code=422,
            invalid_component_inputs=["steps"],
        )

    # Forecast
    forecast = trained_model.forecast(steps=steps+len(series))
    in_sample_forecast = np.round(forecast[:len(series)], 2)
    out_of_sample_forecast = np.round(forecast[-steps:], 2)

    return in_sample_forecast, out_of_sample_forecast

def timeseries_plot_including_predictions(
    data: pd.Series,
    in_sample_forecast: pd.Series,
    out_of_sample_forecast: pd.Series,
    mse: float,
    p_value: float,
    conf_interval: bool,
    alpha: float=0.05
) -> go.Figure:
    """Creates a Plotly time series plot including in-sample and out-of-sample predictions.

    Inputs:
    data (Pandas Series):
        Series containing the observed values.
    in_sample_forecast (Pandas Series):
        Series containing in-sample forecast values.
    out_of_sample_forecast (Pandas Series):
        Series containing out-of-sample forecast values.
    mse (Float):
        Mean Squared Error evaluated on the testing data.
    p_value (Float):
        P-Value of the Shapiro Wilk Test for normality of residuals.
    conf_interval (Bool):
        If True, it plots the confidence intervals.
    alpha (Float, optional):
        Confindence Level to compare the p-value with. Default value is 0.05.

    Outouts:
    fig (Plotly Figure): Time series plot including in-sample and out-of-sample predictions
    """
    # Sorting indices
    data = data.sort_index()
    in_sample_forecast = in_sample_forecast.sort_index()
    out_of_sample_forecast = out_of_sample_forecast.sort_index()

    # Creating the figure (Observed Values and Forecasts)
    fig = go.Figure([
        go.Scatter(
            name="Observed Value",
            x=data.index,
            y=data,
            mode="lines",
            line={"color": "#1f77b4"},
        ),
        go.Scatter(
            name="In-Sample Forecast",
            x=in_sample_forecast.index,
            y=in_sample_forecast,
            mode="lines",
            line={"color": "#fc7d0b"},
        ),
        go.Scatter(
            name="Out-of-Sample Forecast",
            x=out_of_sample_forecast.index,
            y=out_of_sample_forecast,
            mode="lines",
            line={"color": "#fc7d0b", "dash": "dash"},
        )
    ])

    # Adding confidence intervals if specified
    if conf_interval:
        fig.add_traces([
            go.Scatter(
                name="Upper Bound",
                x=out_of_sample_forecast.index,
                y=out_of_sample_forecast + 1.96*mse,
                mode="lines",
                line={"width": 0},
                showlegend=False,
            ),
            go.Scatter(
                name="Lower Bound",
                x=out_of_sample_forecast.index,
                y=out_of_sample_forecast - 1.96*mse,
                mode="lines",
                line={"width": 0},
                showlegend=False,
                fillcolor="rgba(68, 68, 68, 0.3)",
                fill="tonexty"
            )
        ])

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
        plot_bgcolor="white"
    )

    #Annotations
    annotations = []
    if conf_interval:
        conf_text = f"Residuals are likely normal, since p-value ({p_value}) is larger than alpha ({alpha}). Thus, the confindence interval is plotted."
    else:
        conf_text = f"Residuals are likely not normal, since p-value ({p_value}) is smaller than alpha ({alpha}). Thus, the confidence interval is not plotted."

    annotations.append({"xref": "paper", "yref": "paper", "x": 0.0, "y": 1.05,
                              "xanchor": "left", "yanchor": "bottom",
                              "text": "Time Series Plot including In-Sample and Out-Of-Sample Forecast, based on some Exponential Smoothing model",
                              "font": {"family": "Arial",
                                        "size": 30,
                                        "color": "rgb(37,37,37)"},
                              "showarrow": False})
    annotations.append({"xref": "paper", "yref": "paper", "x": 0.0, "y": 1.0,
                              "xanchor": "left", "yanchor": "bottom",
                              "text": f"Mean squared error: {np.round(mse, 2)}. {conf_text}",
                              "font": {"family": "Arial",
                                        "size": 20,
                                        "color": "rgb(37,37,37)"},
                              "showarrow": False})
    fig.update_layout(annotations=annotations)

    return fig

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "series": {"data_type": "SERIES"},
        "steps": {"data_type": "INT"},
        "test_size": {"data_type": "FLOAT", "default_value": 0.3},
        "shuffle": {"data_type": "BOOLEAN", "default_value": False},
        "seasonal_periods": {"data_type": "INT", "default_value": None},
        "use_boxcox": {"data_type": "BOOLEAN", "default_value": True},
        "iterations": {"data_type": "INT", "default_value": 200},
        "initialization_method": {"data_type": "STRING", "default_value": "estimated"},
        "alpha": {"data_type": "FLOAT", "default_value": 0.05},
    },
    "outputs": {
        "plot": {"data_type": "PLOTLYJSON"},
    },
    "name": "Exponential Smoothing",
    "category": "Time Series Analysis",
    "description": "Exponential Smoothing Plot",
    "version_tag": "1.0.0",
    "id": "4401536d-9046-4ccf-87b6-f3c4e4f91f0e",
    "revision_group_id": "b0dc6744-bcea-4407-b6f5-142f95e5b4da",
    "state": "RELEASED",
}

def main(*, series, steps, test_size=0.3, shuffle=False, seasonal_periods=None, use_boxcox=True,
         iterations=200, initialization_method="estimated", alpha=0.05):
    """entrypoint function for this component"""
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    # Step 1: Split the time series into training and testing sets
    train, test = train_test_split_func(
        series=series,
        test_size=test_size,
        shuffle=shuffle
    )
    # Step 2: Optimize hyperparameters for the Exponential Smoothing model using random search
    best_alpha, best_beta, best_gamma, best_phi, best_score, best_trend, best_seasonal = \
        hyper_tuning_grid_search(
            train=train,
            test=test,
            seasonal_periods=seasonal_periods,
            iterations=iterations,
            use_boxcox=use_boxcox,
            initialization_method=initialization_method
        )
    # Step 3: Train some Exponential Smoothing model with optimized hyperparameters
    model_fit = train_exponential_smoothing(
        series=train,
        seasonal_periods=seasonal_periods,
        trend=best_trend,
        seasonal=best_seasonal,
        alpha=best_alpha,
        beta=best_beta,
        gamma=best_gamma,
        phi=best_phi,
        use_boxcox=use_boxcox,
        initialization_method=initialization_method
    )
    # Step 4: Forecast future values using the trained Exponential Smoothing model
    in_sample_forecast, out_of_sample_forecast = forecast_exponential_smoothing(
        trained_model=model_fit,
        series=test,
        steps=steps
    )
    # Step 5: Decide whether to include some confidence interval for the out-of-sample forecast,
    #           based on the normality of the residuals specified by the Shapiro-Wilk Test
    residuals = sorted([x - y for x, y in zip(in_sample_forecast.values, test.values)])
    p_value = np.round(stats.shapiro(residuals)[1], 2)
    conf_interval = p_value > alpha
    # Step 6: Create a Plotly time series plot including in-sample and out-of-sample forecasts,
    #           with optional confidence intervals
    fig = timeseries_plot_including_predictions(
        data=series,
        in_sample_forecast=in_sample_forecast,
        out_of_sample_forecast=out_of_sample_forecast,
        conf_interval=conf_interval,
        mse=best_score,
        p_value=p_value,
        alpha=alpha
    )

    return {"plot": plotly_fig_to_json_dict(fig)}

TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "series",
            "adapter_id": "direct_provisioning",
            "filters": {
                "value":
"""{
    "2023-09-04T00:00:00.000Z": 201,
    "2023-09-05T00:00:00.000Z": 194,
    "2023-09-06T00:00:00.000Z": 281,
    "2023-09-07T00:00:00.000Z": 279,
    "2023-09-08T00:00:00.000Z": 375,
    "2023-09-09T00:00:00.000Z": 393,
    "2023-09-10T00:00:00.000Z": 390,
    "2023-09-11T00:00:00.000Z": 220,
    "2023-09-12T00:00:00.000Z": 262,
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
            }
        },
        {
            "workflow_input_name": "steps",
            "adapter_id": "direct_provisioning",
            "filters": {
                "value": 7
            }
        }
    ]
}

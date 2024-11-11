"""Module Docstring of Partial Autocorrelation Function

# Partial Autocorrelation Function

## Description

This function is designed to plot the *Autocorrelation Function (ACF)* or *Partial Autocorrelation
Function (PACF)* for a given time series data. ACF and PACF plots are essential tools in time series
analysis, particularly useful in identifying the type and level of autocorrelation present in the
data. Understanding these aspects is crucial for effective modeling and forecasting in time series
analysis.

- **ACF (Autocorrelation Function)** measures the correlation between time series observations and
  their lags. It is used to identify the presence of autocorrelation in data, which is a key factor
  in selecting appropriate models for time series forecasting. ACF helps in determining the memory
  of a time series, showing how data points are related to their past values.

- **PACF (Partial Autocorrelation Function)**, on the other hand, measures the correlation between
  the time series and its lags, controlling for the values of the intermediate lags. This is
  particularly helpful in identifying the order of autoregressive (AR) processes in ARIMA modeling.
  PACF plots can suggest the number of AR terms that should be included in a time series model.

Visualizing ACF and PACF gives a clear insight into the lag structure of the time series, aiding in
model selection and parameter tuning for time series forecasting models like ARIMA. These plots help
to distinguish between random and systematic patterns in the data, which is fundamental in
understanding the behavior of the time series and making accurate predictions.

## Inputs

- **series** (Pandas Series):
    The time series data for which to compute ACF or PACF. The index must be datetime.

- **lags** (Int, default value: 20):
    The number of lags to compute for ACF/PACF. Default is 20.

- **confidence_level** (Float, default value: 0.05):
    The significance level for confidence intervals. Default is 0.05.

- **plot_pacf** (Bool, default value: False):
    A flag to determine whether to plot PACF (True) or ACF (False).
    Defaults to plotting ACF (False).

## Outputs

- **plot**:
    A Plotly figure object containing the ACF or PACF plot.

## Details

The visualization of ACF and PACF is instrumental in time series analysis for identifying
autocorrelation patterns. It assists in:
- Determining the necessary lags for autoregressive models.
- Diagnosing the data for randomness or seasonality.
- Guiding the model selection process for accurate time series forecasting.

## Examples

Example input:
```
{
    "data": {
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
    "lags": 10,
    "alpha": 0.05,
    "plot_pacf": False
}
```
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from statsmodels.tsa.stattools import acf, pacf

from hdutils import ComponentInputValidationException, plotly_fig_to_json_dict


def create_pacf_plot(
    series: pd.Series,
    lags: int = 20,
    confidence_level: float = 0.05,
    plot_pacf: bool = False,
):
    """Creates a plot for Autocorrelation Function (ACF) or Partial Autocorrelation Function (PACF).

    Inputs:
    series (Pandas Series):
        Time series data. The index must be datetime.
    lags (Integer, optional):
        Number of lags to calculate ACF/PACF. Default is 20.
    confidence_level (Float, optional):
        Significance level for confidence intervals. Default is 0.05.
    plot_pacf (Bool, optional):
        Flag to plot PACF instead of ACF. Default is False (plots ACF).

    Outputs:
    fig (Plotly Figure):
        A plotly figure object containing the ACF/PACF plot.
    """
    # Parameter validations
    if len(series) == 0:
        raise ComponentInputValidationException(
            "The input series must not be empty!",
            error_code="EmptySeries",
            invalid_component_inputs=["series"],
        )

    if pd.api.types.is_datetime64_any_dtype(series.index.dtype) is False:
        raise ComponentInputValidationException(
            "Indices of series must be datetime, but are of type " + str(series.index.dtype),
            error_code=422,
            invalid_component_inputs=["series"],
        )
    if not 0 < confidence_level < 1:
        raise ComponentInputValidationException(
            "`confidence_level` must be between 0 and 1",
            error_code=422,
            invalid_component_inputs=["confidence_level"],
        )
    if not isinstance(lags, int) or lags < 1:
        raise ComponentInputValidationException(
            "`lags` must be a positive integer",
            error_code=422,
            invalid_component_inputs=["lags"],
        )
    if plot_pacf and (lags * 2 + 1) >= len(series):
        raise ComponentInputValidationException(
            (
                "`lags` must be a positive integer of size smaller than half the length "
                f"of the time series minus 1 ({len(series)/2 - 1})"
            ),
            error_code=422,
            invalid_component_inputs=["lags", "series"],
        )

    # Prepare data
    data_sorted = series.sort_index().dropna()
    if plot_pacf:
        array = pacf(data_sorted, nlags=lags, alpha=confidence_level)
        title = "Partial Autocorrelation (PACF) Plot"
    else:
        array = acf(data_sorted, nlags=lags, alpha=confidence_level)
        title = "Autocorrelation (ACF) Plot"

    lower_values = array[1][:, 0] - array[0]
    upper_values = array[1][:, 1] - array[0]

    # Initialize Figure
    fig = go.Figure()

    # Add traces
    for x in range(len(array[0])):
        fig.add_scatter(x=(x, x), y=(0, array[0][x]), mode="lines", line_color="#3f3f3f")
    fig.add_scatter(
        x=np.arange(len(array[0])),
        y=array[0],
        mode="markers",
        marker_color="#1f77b4",
        marker_size=12,
        name="value",
    )
    fig.add_scatter(
        x=np.arange(len(array[0])),
        y=upper_values,
        mode="lines",
        line_color="rgba(255,255,255,0)",
        name="upper boundary",
    )
    fig.add_scatter(
        x=np.arange(len(array[0])),
        y=lower_values,
        mode="lines",
        line_color="rgba(255,255,255,0)",
        fillcolor="rgba(32,146,230,0.3)",
        fill="tonexty",
        name="lower boundary",
    )

    fig.update_traces(showlegend=False)
    fig.update_xaxes(range=[-1, lags])
    fig.update_yaxes(zerolinecolor="#000000")

    fig.update_layout(title=title)

    return fig


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "series": {"data_type": "SERIES"},
        "lags": {"data_type": "INT", "default_value": 20},
        "confidence_level": {"data_type": "FLOAT", "default_value": 0.05},
        "plot_pacf": {"data_type": "BOOLEAN", "default_value": False},
    },
    "outputs": {
        "plot": {"data_type": "PLOTLYJSON"},
    },
    "name": "Partial Autocorrelation Function Plot",
    "category": "Time Series Analysis",
    "description": "Kwiatkowski-Phillips-Schmidt-Shin test to check trend stationarity",
    "version_tag": "1.0.0",
    "id": "7caf5722-1bbb-459a-bfe7-b6ed826ccad3",
    "revision_group_id": "ec53f7cc-8f6c-4ac3-8927-9d1016561659",
    "state": "RELEASED",
}


def main(*, series, lags=20, confidence_level=0.05, plot_pacf=False):
    """entrypoint function for this component"""
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    fig = create_pacf_plot(
        series=series, lags=lags, confidence_level=confidence_level, plot_pacf=plot_pacf
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
}"""
            },
        }
    ]
}

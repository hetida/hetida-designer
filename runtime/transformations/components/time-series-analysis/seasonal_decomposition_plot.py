"""Module Docstring of Time Series Decomposition

# Time Series Decomposition

## Description

This function decomposes a time series into its constituent components: *trend*, *seasonality*, and
*residuals*. It's essential for understanding and modeling time series data, as it helps to identify
underlying patterns and structures. This decomposition is crucial for tasks like forecasting,
anomaly detection, and better understanding the time series behavior.

## Inputs

- **series** (Pandas Series):
  The time series data to be decomposed. The index must be datetimes.
- **model** (String, default value: "additive"):
  The type of decomposition model ('additive' or 'multiplicative').
- **seasonal_periods** (Integer, default value: None):
  The number of observations that constitute a full seasonal cycle. If not provided, it will be
  inferred.

## Outputs

- **plot** (Plotly Figure):
    A Plotly figure containing the original data and the decomposed components.

## Details

This function is used for analyzing time series data. The decomposition allows for a detailed
understanding of the time series by isolating and examining its different components.
It's particularly useful for:
- **Forecasting**: Understanding trends and seasonal patterns can improve forecasting accuracy.
- **Anomaly Detection**: Residuals can help identify unusual data points that don't follow the
  typical pattern.
- **Data Understanding**: It provides insights into the data, like identifying the presence of
  seasonality or trends over time.

## Examples

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
    "model": "additive",
    "seasonal_periods": 7
}
```
"""

import numpy as np
import pandas as pd
import plotly
import plotly.express as px
import plotly.io as pio
from statsmodels.tsa.seasonal import seasonal_decompose

from hdutils import ComponentInputValidationException, plotly_fig_to_json_dict

pio.templates.default = None


def decompose_time_series(
    series: pd.Series, model: str = "additive", seasonal_periods: int = None
) -> pd.DataFrame:
    """Decompose some time series into its trend, seasonality, and residuals components.

    Inputs:
    series (Pandas Series):
        Time series data. The index must be Datetime.
    model (String, optional):
        Type of decomposition model ('additive' or 'multiplicative'). Default is 'additive'.
    seasonal_periods (Integer, optional):
        Frequency of the time series. If not provided, it will be inferred.

    Outputs:
    df (Pandas DataFrame):
        DataFrame containing the original data, trend, seasonal, and residual components.
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
            error_code="422",
            invalid_component_inputs=["series"],
        )
    if model not in ["additive", "multiplicative"]:
        raise ComponentInputValidationException(
            "`model` must be 'additive' or 'multiplicative'",
            error_code=422,
            invalid_component_inputs=["model"],
        )
    if seasonal_periods and (
        not isinstance(seasonal_periods, int) or seasonal_periods * 2 > len(series)
    ):
        raise ComponentInputValidationException(
            "`seasonal_periods` needs to be an integer smaller than half the length of the series",
            error_code=422,
            invalid_component_inputs=["seasonal_periods"],
        )

    # Generate the decomposition of the time series
    series = series.sort_index().dropna()
    decomposition = seasonal_decompose(series, model=model, period=seasonal_periods)

    # Combine the components with the original data
    decomposed_series = pd.DataFrame(
        {
            "value": series,
            "trend": np.round(decomposition.trend, 4),
            "seasonal": np.round(decomposition.seasonal, 4),
            "residual": np.round(decomposition.resid, 4),
        }
    )

    return decomposed_series


def compute_plot_positions(num_y_axes, horizontal_relative_space_per_y_axis=0.06, side="left"):
    """
    returns tuple plot_area_x_ratio, y_positions

    First assumes that a y axis horizontally fits into 5% of the total figure width
    and tries to reserve enough horizontal space to match that exactly up to a limit
    of reserving half the available width.

    If that is not possible it reserves exactly 0.5 times the total width and
    uniformly arranges the y axis positions (now having less than 5% horizontal space
    and therefore maybe overlapping)

    horizontal_relative_space_per_y_axis:
        a value 0f 0.07 for is quite okay for half of a HD screen.
        its too much for a full hd screen but still acceptable
    """

    hor_ratio = horizontal_relative_space_per_y_axis

    if num_y_axes * hor_ratio < 0.5:
        positions = [1 - x * hor_ratio - hor_ratio * (side == "right") for x in range(num_y_axes)]
        plot_area_x_ratio = 1 - num_y_axes * hor_ratio

    else:
        plot_area_x_ratio = 0.5
        positions = [1 - x * 0.5 / num_y_axes for x in range(num_y_axes)]
    return plot_area_x_ratio, positions


def multi_series_with_multi_yaxis(df: pd.DataFrame):
    """One y_axis for each column of input dataframe"""

    plotly_data = []

    colors = px.colors.qualitative.Plotly

    sep_ratio, positions = compute_plot_positions(len(df.columns), side="right")

    # your layout goes here
    layout_kwargs = {
        "xaxis": {"domain": [0, sep_ratio]},
        "height": 200,
    }

    for i, col in enumerate(df.columns):
        # we define our layout keys by string concatenation
        # * (i > 0) is just to get rid of the if i > 0 statement
        axis_name = "yaxis" + str(i + 1) * (i > 0)
        yaxis = "y" + str(i + 1) * (i > 0)
        plotly_data.append(
            plotly.graph_objs.Scatter(
                x=df.index,
                y=df[col],
                name=col,
                line={"color": colors[i % len(colors)]},
            )
        )

        layout_kwargs[axis_name] = {
            "position": positions[i],
            "side": "right",  # which side of the anchor
            "tickfont": {"color": colors[i % len(colors)], "size": 12},
            "showline": True,  # axis line
            "linecolor": colors[i % len(colors)],  # axis line color
            "showgrid": True,
        }

        plotly_data[i]["yaxis"] = yaxis
        if i > 0:
            layout_kwargs[axis_name]["overlaying"] = "y"

    fig = plotly.graph_objs.Figure(
        data=plotly_data, layout=plotly.graph_objs.Layout(**layout_kwargs)
    )
    fig.update_layout(margin={"l": 0, "r": 0, "b": 0, "t": 5, "pad": 0})

    return fig


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "series": {"data_type": "SERIES"},
        "model": {"data_type": "STRING", "default_value": "additive"},
        "seasonal_periods": {"data_type": "INT", "default_value": None},
    },
    "outputs": {
        "plot": {"data_type": "PLOTLYJSON"},
    },
    "name": "Seasonal Decomposition Plot",
    "category": "Time Series Analysis",
    "description": "Decomposition of some time series",
    "version_tag": "1.0.0",
    "id": "a0158411-5f42-425a-8dbb-95e417c452a5",
    "revision_group_id": "3cfdd244-83a2-4a9f-9546-f913e64d0b2c",
    "state": "RELEASED",
}


def main(*, series, model="additive", seasonal_periods=None):
    """entrypoint function for this component"""
    # ***** DO NOT EDIT LINES ABOVE *****
    # generate decomposed time series
    # Step 1: Decompose some time series into its trend, seasonality, and residual components
    decomposed_series = decompose_time_series(
        series=series, model=model, seasonal_periods=seasonal_periods
    )
    # Step 2: Create decomposition plot
    fig = multi_series_with_multi_yaxis(decomposed_series)

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

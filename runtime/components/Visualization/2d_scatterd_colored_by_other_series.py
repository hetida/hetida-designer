from typing import Optional

from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType
from hetdesrun.utils import plotly_fig_to_json_dict


import pandas as pd

from plotly.graph_objects import Figure
import plotly.express as px

import plotly.io as pio

pio.templates.default = None

import plotly.express as px


def color_scatter_plot(
    series1: pd.Series,
    series2: pd.Series,
    color_series: Optional[pd.Series] = None,
    traces_opts: dict = {"line_color": "#1199bb"},
    layout_opts: dict = {
        "xaxis_title": "x",
        "yaxis_title": "y",
        "autosize": True,
        "height": 400,
    },
    line_opts: dict = {},
):
    """Colored 2D Scatter Plot
    
    If no color_series is provided, the index will be used.
    
    Assumes that both series are of same / similar index.
    
    Automatically handles the dtype of the color_series (or index), that
    is datetime will be converted to total_seconds from minimum timestamp,
    and distinguishes between numeric versus categorical values.
    """

    df = pd.DataFrame({"x": series1, "y": series2})

    if color_series is None:
        if pd.api.types.is_datetime64_any_dtype(df.index):
            df["timestamps"] = pd.Series(df.index, index=df.index)
            df["seconds_from_start"] = (
                df.timestamps - df.timestamps.min()
            ).dt.total_seconds()
            fig = px.scatter(
                df,
                x="x",
                y="y",
                color="seconds_from_start",
                color_continuous_scale=px.colors.sequential.Plasma,
            )

        elif pd.api.types.is_numeric_dtype(df.index):
            df["index"] = pd.Series(df.index, index=df.index)
            fig = px.scatter(
                df,
                x="x",
                y="y",
                color="index",
                color_continuous_scale=px.colors.sequential.Plasma,
            )
        else:
            raise ValueError("Index is not of a dtype that allows coloring from it")
    else:
        color_col_name = "color" if color_series.name is None else color_series.name
        df[color_col_name] = color_series

        if pd.api.types.is_datetime64_any_dtype(color_series):
            df[color_col_name] = (
                df[color_col_name] - df[color_col_name].min()
            ).dt.total_seconds()
            fig = px.scatter(
                df,
                x="x",
                y="y",
                color=color_col_name,
                color_continuous_scale=px.colors.sequential.Plasma,
            )

        elif pd.api.types.is_numeric_dtype(color_series):
            fig = px.scatter(
                df,
                x="x",
                y="y",
                color=color_col_name,
                color_continuous_scale=px.colors.sequential.Plasma,
            )

        elif pd.api.types.is_categorical_dtype(
            color_series
        ) or pd.api.types.is_string_dtype(color_series):
            fig = px.scatter(df, x="x", y="y", color=color_col_name)
        else:
            raise ValueError("Index is not of a dtype that allows coloring from it")

    fig.update_layout(**layout_opts)  # see https://plotly.com/python/figure-labels/
    fig.update_traces(traces_opts)  # set line color?

    fig.update_layout(margin=dict(l=0, r=0, b=0, t=5, pad=0))

    fig.update_yaxes(automargin=True)
    fig.update_xaxes(automargin=True)
    return fig


def color_df_scatter_plot(df, x, y, color_col=None):
    """Wrapper for dataframes"""
    return color_scatter_plot(
        df[x], df[y], color_series=df[color_col] if color_col is not None else None
    )


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={"x": DataType.Series, "y": DataType.Series, "color": DataType.Series},
    outputs={"scatter_plot": DataType.PlotlyJson},
)
def main(*, x, y, color):
    """entrypoint function for this component"""
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    return {
        "scatter_plot": plotly_fig_to_json_dict(
            color_scatter_plot(x, y, color_series=color)
        )
    }

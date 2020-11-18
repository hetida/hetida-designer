from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType  # add your own imports here
from hetdesrun.utils import plotly_fig_to_json_dict

import pandas as pd
import numpy as np

from plotly.graph_objects import Figure
import plotly.express as px

import plotly.io as pio

pio.templates.default = None


def timeseries_comparison_plot(
    series_1: pd.Series,
    series_2: pd.Series,
    limit_violation_timestamp: str,
    limit: float,
    traces_opts: dict = {},
    layout_opts: dict = {
        "xaxis_title": "Time",
        "yaxis_title": "Values",
        "autosize": True,
        "height": 200,
    },
    line_opts: dict = {},
) -> Figure:
    """Create a single time series line plot Plotly figure
    
    Returns the plotly figure object.
    """

    fig = Figure()
    # Only thing I figured is - I could do this

    s1 = series_1.sort_index()

    fig.add_scatter(
        x=s1.index, y=s1, mode="lines", name=s1.name if s1.name else "series_1"
    )  # Not what is desired - need a line

    s2 = series_2.sort_index()

    fig.add_scatter(
        x=s2.index, y=s2, mode="lines", name=s2.name if s2.name else "series_2"
    )  # Not what is desired - need a line

    fig.update_layout(**layout_opts)  # see https://plotly.com/python/figure-labels/
    fig.update_traces(traces_opts)  # set line color?

    vline_y_min = np.min([series_1.min(), series_2.min(), limit])
    vline_y_max = np.max([series_1.max(), series_2.max(), limit])

    hline_x_min = np.min([series_1.index.min(), series_2.index.min()])
    hline_x_max = np.max([series_1.index.max(), series_2.index.max()])

    fig.update_layout(
        shapes=(
            [
                dict(
                    type="line",
                    yref="y",
                    y0=vline_y_min,
                    y1=vline_y_max,
                    xref="x",
                    x0=limit_violation_timestamp,
                    x1=limit_violation_timestamp,
                )
            ]
            if limit_violation_timestamp is not None
            else []
        )
        + [
            dict(
                type="line",
                yref="y",
                y0=limit,
                y1=limit,
                xref="x",
                x0=hline_x_min,
                x1=hline_x_max,
                line={"color": "red", "width": 1},
            )
        ]
    )

    fig.update_layout(margin=dict(l=0, r=0, b=0, t=5, pad=0))

    fig.update_yaxes(automargin=True)
    fig.update_xaxes(automargin=True)
    return fig


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={
        "base_series": DataType.Series,
        "predictions": DataType.Series,
        "limit": DataType.Float,
        "limit_violation_prediction_timestamp": DataType.String,
    },
    outputs={"rul_regression_result_plot": DataType.PlotlyJson},
)
def main(*, base_series, predictions, limit, limit_violation_prediction_timestamp):
    """entrypoint function for this component"""
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    return {
        "rul_regression_result_plot": plotly_fig_to_json_dict(
            timeseries_comparison_plot(
                base_series, predictions, limit_violation_prediction_timestamp, limit
            )
        )
    }

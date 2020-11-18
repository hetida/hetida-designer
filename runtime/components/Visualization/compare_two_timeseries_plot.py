from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType  # add your own imports here
from hetdesrun.utils import plotly_fig_to_json_dict

import pandas as pd

from plotly.graph_objects import Figure
import plotly.express as px

import plotly.io as pio

pio.templates.default = None


def timeseries_comparison_plot(
    series_1: pd.Series,
    series_2: pd.Series,
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

    fig.update_layout(margin=dict(l=0, r=0, b=0, t=5, pad=0))

    fig.update_yaxes(automargin=True)
    fig.update_xaxes(automargin=True)
    return fig


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={"series_1": DataType.Series, "series_2": DataType.Series},
    outputs={"comparison_plot": DataType.PlotlyJson},
    is_pure_plot_component=True,
)
def main(*, series_1, series_2):
    """entrypoint function for this component"""
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    return {
        "comparison_plot": plotly_fig_to_json_dict(
            timeseries_comparison_plot(series_1, series_2)
        )
    }

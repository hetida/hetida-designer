from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType
from hetdesrun.utils import plotly_fig_to_json_dict


import pandas as pd

import plotly.graph_objects as go

from plotly.graph_objects import Figure
import plotly.express as px

import plotly.io as pio

pio.templates.default = None


def single_plotly_timeseries_plot(
    series: pd.Series,
    traces_opts: dict = {"line_color": "#1199bb"},
    line_opts: dict = {},
) -> Figure:
    """Create a single time series line plot Plotly figure
    
    Returns the plotly figure object.
    """

    df = pd.DataFrame(
        {"value": series, "timestamp": series.index}, index=series.index
    ).sort_index()
    # fig = px.line(df, x="timestamp", y="value", **line_opts)
    fig = go.Figure([go.Scatter(x=df.index, y=df["value"], mode="lines")])

    layout_opts: dict = {
        "xaxis_title": "Time",
        "yaxis_title": "Values",
        "autosize": True,
        "height": 200,
    }
    if series.name is not None:
        layout_opts["yaxis_title"] = series.name
    fig.update_layout(**layout_opts)  # see https://plotly.com/python/figure-labels/
    fig.update_traces(traces_opts)  # set line color?

    fig.update_layout(margin=dict(l=0, r=0, b=0, t=5, pad=0))

    fig.update_yaxes(automargin=True)
    fig.update_xaxes(automargin=True)

    return fig


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={"series": DataType.Series},
    outputs={"plot": DataType.PlotlyJson},
    is_pure_plot_component=True,
)
def main(*, series):
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    return {"plot": plotly_fig_to_json_dict(single_plotly_timeseries_plot(series))}

from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType
from hetdesrun.utils import plotly_fig_to_json_dict


import pandas as pd

from plotly.graph_objects import Figure
import plotly.express as px

import plotly.io as pio

pio.templates.default = None


def plotly_bar_plot(
    value_series: pd.Series,
    traces_opts: dict = {},
    layout_opts: dict = {"autosize": True, "height": 200},
    bar_opts: dict = {},
) -> Figure:
    """Create a vertical bar plot Plotly figure
    
    Expects a series of values (the bar lengths) and uses the series index
    to denote the bars on the x axis. Works best if the index consists of
    strings.
    
    
    Returns the plotly figure object.
    """

    df = pd.DataFrame(
        {"values": value_series, "x": value_series.index}, index=value_series.index
    )
    fig = px.bar(df, x="x", y="values", **bar_opts)

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
    return {"plot": plotly_fig_to_json_dict(plotly_bar_plot(series))}

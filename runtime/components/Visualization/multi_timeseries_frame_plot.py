from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType
from hetdesrun.utils import plotly_fig_to_json_dict


import pandas as pd

from plotly.graph_objects import Figure
import plotly.express as px

import plotly.io as pio

pio.templates.default = None


def multi_plotly_timeseries_plot(
    dataframe: pd.DataFrame,
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
    columns = list(dataframe.keys())

    to_plot_df = dataframe.sort_index()

    # Only thing I figured is - I could do this
    for key in columns:
        fig.add_scatter(
            x=to_plot_df.index, y=to_plot_df[key], mode="lines", name=key
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
    inputs={"dataframe": DataType.DataFrame},
    outputs={"plot": DataType.PlotlyJson},
    is_pure_plot_component=True,
)
def main(*, dataframe):
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    return {"plot": plotly_fig_to_json_dict(multi_plotly_timeseries_plot(dataframe))}

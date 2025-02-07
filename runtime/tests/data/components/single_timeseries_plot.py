"""Documentation for Single Timeseries Plot

# Single Timeseries Plot
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from plotly.graph_objects import Figure

from hdutils import plotly_fig_to_json_dict

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
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "series": {"data_type": "SERIES"},
    },
    "outputs": {
        "plot": {"data_type": "PLOTLYJSON"},
    },
    "name": "Single Timeseries Plot",
    "category": "Visualization",
    "description": "Plotting a single timeseries",
    "version_tag": "1.0.0",
    "id": "8fba9b51-a0f1-6c6c-a6d4-e224103b819c",
    "revision_group_id": "8fba9b51-a0f1-6c6c-a6d4-e224103b819c",
    "state": "RELEASED",
    "released_timestamp": "2022-02-09T18:33:30.537411+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, series):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    return {"plot": plotly_fig_to_json_dict(single_plotly_timeseries_plot(series))}


TEST_WIRING_FROM_PY_FILE_IMPORT = {}
RELEASE_WIRING = {}

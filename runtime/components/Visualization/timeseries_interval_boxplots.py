from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType
from hetdesrun.utils import plotly_fig_to_json_dict


import pandas as pd

from plotly.graph_objects import Figure
import plotly.express as px

import plotly.io as pio

pio.templates.default = None


def interval_box_plots(
    series: pd.Series,
    interval: str,
    traces_opts: dict = {"line_color": "#1199bb"},
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

    df = series.to_frame().sort_index()
    df_value_col = df.columns[0]

    if interval.lower() in ["day", "d"]:
        interval_col_name = "year--month--day"
        df[interval_col_name] = pd.Series(df.index, index=df.index).apply(
            lambda x: str(x.year) + "--" + f"{x.month:0>2d}" + "--" + f"{x.day:0>2d}"
        )

    elif interval.lower() in ["week", "w"]:
        interval_col_name = "year--week"
        df[interval_col_name] = pd.Series(df.index, index=df.index).apply(
            lambda x: str(x.year) + "--" + f"{x.week:0>2d}"
        )

    elif interval.lower() in ["month", "m"]:
        interval_col_name = "year--month"
        df[interval_col_name] = pd.Series(df.index, index=df.index).apply(
            lambda x: str(x.year) + "--" + f"{x.month:0>2d}"
        )

    elif interval.lower() in ["year", "y"]:
        interval_col_name = "year"
        df[interval_col_name] = pd.Series(df.index, index=df.index).apply(
            lambda x: str(x.year)
        )
    else:
        raise ValueError("Unknown interval string: " + interval)
    fig = px.box(df, x=interval_col_name, y=df_value_col)

    fig.update_layout(
        **{**layout_opts, **{"xaxis_title": interval_col_name}}
    )  # see https://plotly.com/python/figure-labels/
    fig.update_traces(traces_opts)  # set line color?

    fig.update_layout(margin=dict(l=0, r=0, b=0, t=5, pad=0))

    fig.update_yaxes(automargin=True)
    fig.update_xaxes(automargin=True)

    return fig


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={"series": DataType.Series, "interval": DataType.String},
    outputs={"plot": DataType.PlotlyJson},
)
def main(*, series, interval):
    """entrypoint function for this component"""
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    return {"plot": plotly_fig_to_json_dict(interval_box_plots(series, interval))}

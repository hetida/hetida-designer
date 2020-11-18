from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType
from hetdesrun.utils import plotly_fig_to_json_dict


import pandas as pd

import plotly.graph_objects as go

import plotly.io as pio

pio.templates.default = None


def alerts_time_intervals(value_series, alert_indicator_series):

    min_timestamp, max_timestamp = value_series.index.min(), value_series.index.max()
    only_starts_and_ends = alert_indicator_series[
        alert_indicator_series != 0
    ].sort_index()

    # add start to first alert if necessary
    if len(only_starts_and_ends) > 0 and only_starts_and_ends.iloc[0] == -1:
        if min_timestamp < only_starts_and_ends.index.min():
            # add first entry 1
            only_starts_and_ends[min_timestamp] = 1
        else:
            raise ValueError(
                "value_series must have smaller timestamps if first non-zero entry of alert_indicator_series is -1. Otherwise no start for the first alert can be found!"
            )

    only_starts_and_ends = only_starts_and_ends.sort_index()

    # add end to last alert if necessary
    if len(only_starts_and_ends) > 0 and only_starts_and_ends.iloc[-1] == 1:
        if max_timestamp > only_starts_and_ends.index.min():
            # add first entry 1
            only_starts_and_ends[max_timestamp] = -1
        else:
            raise ValueError(
                "value_series must have greater timestamps if last non-zero entry of alert_indicator_series is 1. Otherwise no end for the last alert can be found!"
            )

    return only_starts_and_ends.sort_index()


def plot_series_and_alerts(series, alert_indicator_series):

    series_to_plot = series.sort_index()
    fig = go.Figure(
        [go.Scatter(x=series_to_plot.index, y=series_to_plot, mode="lines")]
    )

    max_val, min_val = series.max(), series.min()

    alert_intervals = alerts_time_intervals(series, alert_indicator_series)

    alerts_df = alert_intervals.to_frame(name="starts")
    alerts_df["start_timestamps"] = alerts_df.index
    alerts_df["ends"] = alerts_df["starts"].shift(-1)
    alerts_df["end_timestamps"] = alerts_df["start_timestamps"].shift(-1)
    alerts_df = alerts_df[alerts_df["starts"] == 1][
        ["start_timestamps", "end_timestamps"]
    ]

    for ind, row in alerts_df.iterrows():
        start, end = row["start_timestamps"], row["end_timestamps"]
        fig.add_shape(
            type="rect",
            x0=start,
            y0=min_val,
            x1=end,
            y1=max_val,
            line={"color": "rgb(251, 40, 0)", "width": 1},
            fillcolor="rgba(251, 40, 0, 0.4)",
        )

    layout_opts: dict = {
        "xaxis_title": "Time",
        "yaxis_title": "Values",
        "autosize": True,
        "height": 200,
    }
    if series.name is not None:
        layout_opts["yaxis_title"] = series.name
    fig.update_layout(**layout_opts)  # see https://plotly.com/python/figure-labels/

    fig.update_layout(margin=dict(l=0, r=0, b=0, t=5, pad=0))

    fig.update_yaxes(automargin=True)
    fig.update_xaxes(automargin=True)

    return fig


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={"series": DataType.Series, "alert_series": DataType.Series},
    outputs={"alert_plot": DataType.PlotlyJson},
    is_pure_plot_component=True,
)
def main(*, series, alert_series):
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    return {
        "alert_plot": plotly_fig_to_json_dict(
            plot_series_and_alerts(series, alert_series)
        )
    }

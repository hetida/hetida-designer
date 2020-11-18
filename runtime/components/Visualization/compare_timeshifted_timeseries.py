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
    freq,
    freq_factor,
    max_shifts_past,
    max_shifts_future,
    traces_opts: dict = {},
    layout_opts: dict = {
        "xaxis_title": "Time",
        "yaxis_title": "Values",
        "autosize": True,
        "height": 480,
    },
    line_opts: dict = {},
) -> Figure:
    """Create a single time series line plot Plotly figure
    
    Returns the plotly figure object.
    """
    if max_shifts_past < 0 or max_shifts_future < 0:
        raise ValueError("Shift maxima values must be greater equal zero.")

    fig = Figure()

    s1 = series_1.sort_index()

    fig.add_scatter(
        x=s1.index,
        y=s1,
        mode="lines",
        name=s1.name if (s1.name and s1.name != "measurement") else "series",
    )

    s2 = series_2.sort_index()

    for step in np.arange(-max_shifts_past, max_shifts_future, 1):
        shifted = s2.copy()
        shifted.index = shifted.index.shift(periods=step * freq_factor, freq=freq)
        fig.add_scatter(
            x=shifted.index,
            y=shifted,
            mode="lines",
            name=shifted.name
            if (shifted.name and shifted.name != "measurement")
            else "series_shiftable",
            visible=False,
        )

    fig.data[max_shifts_past + 1].visible = True  # start somewhere

    steps = []
    for i in range(len(fig.data)):
        step = dict(
            method="update",
            args=[
                {"visible": [False] * (len(fig.data))},
                {
                    "title": f"Shifted by x times frequency {freq_factor}{freq}: "
                    + str(i - max_shifts_past - 1)
                },
            ],  # layout attribute
        )
        step["args"][0]["visible"][i] = True  # Toggle i'th trace to "visible"
        step["args"][0]["visible"][0] = True
        step["label"] = str(i - max_shifts_past - 1)
        steps.append(step)

    sliders = [
        dict(
            active=max_shifts_past,
            currentvalue={
                "prefix": f"Shifted by x times frequency {freq_factor}{freq}: "
            },
            pad={"t": 80, "b": 10},
            steps=steps[1:],
        )
    ]

    fig.update_layout(**layout_opts)  # see https://plotly.com/python/figure-labels/
    fig.update_traces(traces_opts)  # set line color?

    fig.update_layout(margin=dict(l=0, r=0, b=40, t=30, pad=10))

    fig.update_yaxes(automargin=True)
    fig.update_xaxes(automargin=True)

    fig.update_layout(sliders=sliders)

    return fig


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={
        "freq": DataType.String,
        "max_shifts_future": DataType.Integer,
        "max_shifts_past": DataType.Integer,
        "series": DataType.Series,
        "series_shiftable": DataType.Series,
        "freq_factor": DataType.Integer,
    },
    outputs={"comparison_plot": DataType.PlotlyJson},
)
def main(
    *, freq, max_shifts_future, max_shifts_past, series, series_shiftable, freq_factor
):
    """entrypoint function for this component"""
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    return {
        "comparison_plot": plotly_fig_to_json_dict(
            timeseries_comparison_plot(
                series,
                series_shiftable,
                freq,
                freq_factor,
                max_shifts_past,
                max_shifts_future,
            )
        )
    }

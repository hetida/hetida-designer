from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType
from hetdesrun.utils import plotly_fig_to_json_dict


import pandas as pd

from plotly.graph_objects import Figure
import plotly.express as px

import plotly
import plotly.io as pio

pio.templates.default = None


def compute_plot_positions(
    num_y_axes, horizontal_relative_space_per_y_axis=0.06, side="left"
):
    """
    returns tuple plot_area_x_ratio, y_positions

    First assumes that a y axis horizontally fits into 5% of the total figure width
    and tries to reserve enough horizontal space to match that exactly up to a limit
    of reserving half the available width.

    If that is not possible it reserves exactly 0.5 times the total width and
    uniformly arranges the y axis positions (now having less than 5% horizontal space
    and therefore maybe overlapping)

    horizontal_relative_space_per_y_axis:
        a value 0f 0.07 for is quite okay for half of a HD screen.
        its too much for a full hd screen but still acceptable
    """

    hor_ratio = horizontal_relative_space_per_y_axis

    if num_y_axes * hor_ratio < 0.5:
        positions = [
            1 - x * hor_ratio - hor_ratio * (side == "right") for x in range(num_y_axes)
        ]
        plot_area_x_ratio = 1 - num_y_axes * hor_ratio

    else:
        plot_area_x_ratio = 0.5
        positions = [1 - x * 0.5 / num_y_axes for x in range(num_y_axes)]
    return plot_area_x_ratio, positions


def multi_series_with_multi_yaxis(df):
    """One y_axis for each column of input dataframe"""

    plotly_data = []
    plotly_layout = plotly.graph_objs.Layout()

    colors = px.colors.qualitative.Plotly

    sep_ratio, positions = compute_plot_positions(len(df.columns), side="right")

    # your layout goes here
    layout_kwargs = {
        # "title": "y-axes in loop",
        "xaxis": {"domain": [0, sep_ratio]},
        "height": 200,
    }

    for i, col in enumerate(df.columns):
        # we define our layout keys by string concatenation
        # * (i > 0) is just to get rid of the if i > 0 statement
        axis_name = "yaxis" + str(i + 1) * (i > 0)
        yaxis = "y" + str(i + 1) * (i > 0)
        plotly_data.append(
            plotly.graph_objs.Scatter(
                x=df.index,
                y=df[col],
                name=col,
                line=dict(
                    color=colors[i % len(colors)]
                    # , width=4, dash="dash"
                ),
            )
        )

        layout_kwargs[axis_name] = {  #'range': [0, i + 0.1],
            "position": positions[i],
            # "automargin":True,
            # "anchor":"free",
            "side": "right",  # which side of the anchor
            # "title": col,
            # "titlefont": dict(color=colors[i % len(colors)], size=12),
            "tickfont": dict(color=colors[i % len(colors)], size=12),
            # "title_standoff":0.0,
            "showline": True,  # axis line
            "linecolor": colors[i % len(colors)],  # axis line color
            "showgrid": True
            # "gridcolor": colors[i % len(colors)] # color of gridlines for this axis
        }

        plotly_data[i]["yaxis"] = yaxis
        if i > 0:
            layout_kwargs[axis_name]["overlaying"] = "y"

    fig = plotly.graph_objs.Figure(
        data=plotly_data, layout=plotly.graph_objs.Layout(**layout_kwargs)
    )
    fig.update_layout(margin=dict(l=0, r=0, b=0, t=5, pad=0))

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
    return {"plot": plotly_fig_to_json_dict(multi_series_with_multi_yaxis(dataframe))}

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
    num_x_axes,
    num_y_axes,
    horizontal_relative_space_per_y_axis=0.06,
    vertical_relative_space_per_x_axis=0.09,
    y_axes_side="left",
    x_axes_side="bottom",
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
        x_positions = [
            1 - x * hor_ratio - hor_ratio * (y_axes_side == "right")
            for x in range(num_y_axes)
        ]
        plot_area_x_ratio = 1 - num_y_axes * hor_ratio

    else:
        plot_area_x_ratio = 0.5
        x_positions = [1 - x * 0.5 / num_y_axes for x in range(num_y_axes)]

    ver_ratio = vertical_relative_space_per_x_axis

    if num_x_axes * ver_ratio < 0.5:
        y_positions = [
            1 - y * ver_ratio - ver_ratio * (x_axes_side == "bottom")
            for y in range(num_x_axes)
        ]
        plot_area_y_ratio = 1 - num_x_axes * ver_ratio

    else:
        plot_area_y_ratio = 0.5
        y_positions = [1 - y * 0.5 / num_x_axes for y in range(num_x_axes)]

    return plot_area_y_ratio, y_positions, plot_area_x_ratio, x_positions


def multi_series_with_multi_yaxis(df):
    """One y_axis for each column of input dataframe"""

    plotly_data = []
    plotly_layout = plotly.graph_objs.Layout()

    colors = px.colors.qualitative.Plotly

    y_sep_ratio, y_positions, x_sep_ratio, x_positions = compute_plot_positions(
        len(df.columns), len(df.columns), y_axes_side="right", x_axes_side="bottom"
    )

    print(y_sep_ratio, y_positions, x_sep_ratio, x_positions)

    # your layout goes here
    layout_kwargs = {
        # "title": "y-axes in loop",
        # "xaxis": {"domain": [0, x_sep_ratio]},
        "height": 400,
    }

    for i, col in enumerate(df.columns):
        # we define our layout keys by string concatenation
        # * (i > 0) is just to get rid of the if i > 0 statement
        yaxis_name = "yaxis" + str(i + 1) * (i > 0)
        xaxis_name = "xaxis" + str(i + 1) * (i > 0)
        yaxis = "y" + str(i + 1) * (i > 0)
        xaxis = "x" + str(i + 1) * (i > 0)
        plotly_data.append(
            plotly.graph_objs.Scatter(
                x=df.index,
                y=df[col],
                name=col,
                opacity=0.8,
                line=dict(
                    color=colors[i % len(colors)]
                    # , width=4, dash="dash"
                ),
            )
        )

        layout_kwargs[yaxis_name] = {  #'range': [0, i + 0.1],
            "position": x_positions[i],
            # "automargin":True,
            # "anchor":"free",
            "side": "right",  # which side of the anchor
            # "title": col,
            # "titlefont": dict(color=colors[i % len(colors)], size=12),
            "tickfont": dict(color=colors[i % len(colors)], size=12),
            # "title_standoff":0.0,
            "showline": True,  # axis line
            "linecolor": colors[i % len(colors)],  # axis line color
            "showgrid": True,
            # "gridcolor": colors[i % len(colors)] # color of gridlines for this axis
            "domain": [1.0 - y_sep_ratio, 1.0],
        }

        layout_kwargs[xaxis_name] = {  #'range': [0, i + 0.1],
            "position": 1 - y_positions[i],
            # "automargin":True,
            # "anchor":"free",
            "side": "bottom",  # which side of the anchor
            # "title": col,
            # "titlefont": dict(color=colors[i % len(colors)], size=12),
            "tickfont": dict(color=colors[i % len(colors)], size=12),
            # "title_standoff":0.0,
            "showline": True,  # axis line
            "linecolor": colors[i % len(colors)],  # axis line color
            "showgrid": True,
            # "gridcolor": colors[i % len(colors)] # color of gridlines for this axis
            "domain": [0, x_sep_ratio],
        }

        plotly_data[i]["yaxis"] = yaxis
        plotly_data[i]["xaxis"] = xaxis
        if i > 0:
            layout_kwargs[yaxis_name]["overlaying"] = "y"
            layout_kwargs[xaxis_name]["overlaying"] = "x"

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

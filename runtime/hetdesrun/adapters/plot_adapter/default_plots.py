import logging
from typing import Any

import pandas as pd
import plotly
import plotly.express as px
import plotly.graph_objects as go
from pandas.api.types import is_datetime64_any_dtype

from hdutils import DataType, plotly_fig_to_json_dict
from hetdesrun.adapters.exceptions import AdapterHandlingException

logger = logging.getLogger(__name__)


def provide_plotly_fig_json_for_arbitrary_value(value: Any, filtered_sink_type: DataType) -> Any:  # noqa: PLR0911, PLR0912
    """Decide on Python type / DataType and provide corresponding plotly json dict"""
    if isinstance(value, (str, int, float, bool)) and filtered_sink_type in {
        DataType.Boolean,
        DataType.Float,
        DataType.Integer,
        DataType.String,
    }:
        try:
            plotly_json_obj = simple_value_plotly_json(value)
        except Exception as e:
            msg = (
                f"Plot adapter could not generate indicator plotly plot for value"
                f" with type {str(type(value))} "
                f"with FilteredSink.type {str(filtered_sink_type)}. Exception was:\n{str(e)}"
            )
            logger.error(msg)
            raise AdapterHandlingException(msg) from e
        return plotly_json_obj

    if isinstance(value, pd.Series) and (filtered_sink_type in (DataType.Series, DataType.Any)):
        try:
            plotly_json_obj = single_series_plotly_json(value)
        except Exception as e:
            msg = (
                f"Plot adapter could not generate timeseries plot for value"
                f" with type {str(type(value))} "
                f"with FilteredSink.type {str(filtered_sink_type)}. Exception was:\n{str(e)}"
            )
            logger.error(msg)
            raise AdapterHandlingException(msg) from e
        return plotly_json_obj

    if isinstance(value, pd.DataFrame) and filtered_sink_type == DataType.MultiTSFrame:
        try:
            plotly_json_obj = plotly_fig_to_json_dict(multi_series_with_multi_yaxis(value))
        except Exception as e:
            msg = (
                f"Plot adapter could not generate multitsframe plot for value"
                f" with type {str(type(value))} "
                f"with FilteredSink.type {str(filtered_sink_type)}. Exception was:\n{str(e)}"
            )
            logger.error(msg)
            raise AdapterHandlingException(msg) from e
        return plotly_json_obj

    if isinstance(value, pd.DataFrame) and filtered_sink_type == DataType.DataFrame:
        if "timestamp" in value.columns:  # wide format dataframe of timeseries data
            try:
                plotly_json_obj = plotly_fig_to_json_dict(
                    px.line(
                        value,
                        x="timestamp",
                        y=value.columns.drop("timestamp"),
                        template="none",
                        markers=True,
                    )
                )
                return plotly_json_obj
            except Exception:  # noqa: S110, BLE001
                pass

        try:
            plotly_json_obj = plotly_fig_to_json_dict(table_fig_plotly_json(value))
        except Exception as e:
            msg = (
                f"Plot adapter could not generate dataframe table for value"
                f" with type {str(type(value))} "
                f"with FilteredSink.type {str(filtered_sink_type)}. Exception was:\n{str(e)}"
            )
            logger.error(msg)
            raise AdapterHandlingException(msg) from e
        return plotly_json_obj

    if filtered_sink_type == DataType.PlotlyJson:
        return value

    if filtered_sink_type == DataType.Any:
        if isinstance(value, pd.DataFrame):
            try:
                plotly_json_obj = plotly_fig_to_json_dict(table_fig_plotly_json(value))
            except Exception as e:
                msg = (
                    f"Plot adapter could not generate dataframe table for value"
                    f" with type {str(type(value))} "
                    f"with FilteredSink.type {str(filtered_sink_type)}. Exception was:\n{str(e)}"
                )
                logger.error(msg)
                raise AdapterHandlingException(msg) from e

        return simple_value_plotly_json("Unplottable ANY object")

    msg = (
        f"Unfitting type combination for Plot adapter: value type is {str(type(value))}."
        f" DataType from FilteredSink is {str(filtered_sink_type)}"
    )
    raise AdapterHandlingException(msg)


def value_fig(value: Any) -> go.Figure:
    """Simple plotly indicator for float, int, boolean, string values"""
    display = str(value)

    fig = go.Figure(
        go.Indicator(
            mode="number",
            value=0,
            number={"font": {"size": 1, "color": "rgba(0,0,0,0)"}},
            title={"text": f"<b>{display}</b>", "font": {"size": 16, "color": "#1f2937"}},
            domain={"x": [0, 1], "y": [0, 1]},
        )
    )

    fig.update_layout(
        width=100 + 10 * min(max(len(display) - 10, 0), 30),
        height=100,
        margin={"l": 40, "r": 40, "t": 60, "b": 40},
        paper_bgcolor="#f9fafb",
    )
    return fig


def simple_value_plotly_json(value: Any) -> Any:
    plotly_fig_dict = plotly_fig_to_json_dict(value_fig(value))
    plotly_fig_dict["config"]["displayModeBar"] = False
    plotly_fig_dict["config"]["scrollZoom"] = True

    return plotly_fig_dict


def single_plotly_timeseries_plot(
    series: pd.Series,
) -> go.Figure:
    """Create a single series Plotly figure"""

    traces_opts: dict = {"line_color": "#1199bb"}

    df = pd.DataFrame({"value": series, "timestamp": series.index}, index=series.index).sort_index()

    fig = go.Figure([go.Scatter(x=df.index, y=df["value"], mode="lines")])

    layout_opts: dict = {
        "xaxis_title": "",  # TODO
        "yaxis_title": "",  # TODO
        "autosize": True,
        "height": 200,
    }
    if series.name is not None:
        layout_opts["yaxis_title"] = series.name
    fig.update_layout(**layout_opts)  # see https://plotly.com/python/figure-labels/
    fig.update_traces(traces_opts)  # set line color?

    fig.update_layout(margin={"l": 0, "r": 0, "b": 0, "t": 5, "pad": 0})

    fig.update_yaxes(automargin=True)
    fig.update_xaxes(automargin=True)

    return fig


def single_series_plotly_json(series: pd.Series) -> Any:
    return plotly_fig_to_json_dict(single_plotly_timeseries_plot(series))


def compute_plot_positions(
    num_y_axes: int, horizontal_relative_space_per_y_axis: float = 0.06, side: str = "left"
) -> tuple[float, list[float]]:
    """returns tuple plot_area_x_ratio, y_positions

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
        positions = [1 - x * hor_ratio - hor_ratio * (side == "right") for x in range(num_y_axes)]
        plot_area_x_ratio = 1 - num_y_axes * hor_ratio

    else:
        plot_area_x_ratio = 0.5
        positions = [1 - x * 0.5 / num_y_axes for x in range(num_y_axes)]
    return plot_area_x_ratio, positions


def multi_series_with_multi_yaxis(df: pd.DataFrame) -> go.Figure:
    """One y_axis for each metric of input multitsframe"""

    plotly_data = []

    colors = px.colors.qualitative.Plotly
    metrics = df["metric"].unique().tolist()

    sep_ratio, positions = compute_plot_positions(len(metrics), side="right")

    # your layout goes here
    layout_kwargs: dict[str, Any] = {
        "xaxis": {"domain": [0, sep_ratio]},
        "height": 200,
    }

    for i, col in enumerate(metrics):
        selected = df[df.metric == col]
        metric_series = pd.Series(selected["value"].values, index=selected["timestamp"])
        # we define our layout keys by string concatenation
        # * (i > 0) is just to get rid of the if i > 0 statement
        axis_name = "yaxis" + str(i + 1) * (i > 0)
        yaxis = "y" + str(i + 1) * (i > 0)
        plotly_data.append(
            plotly.graph_objs.Scatter(
                x=metric_series.index,
                y=metric_series,
                name=col,
                line={"color": colors[i % len(colors)]},
            )
        )

        layout_kwargs[axis_name] = {  #'range': [0, i + 0.1],
            "position": positions[i],
            "side": "right",  # which side of the anchor
            "tickfont": {"color": colors[i % len(colors)], "size": 12},
            "showline": True,  # axis line
            "linecolor": colors[i % len(colors)],  # axis line color
            "showgrid": True,
        }

        plotly_data[i]["yaxis"] = yaxis
        if i > 0:
            layout_kwargs[axis_name]["overlaying"] = "y"

    fig = plotly.graph_objs.Figure(
        data=plotly_data, layout=plotly.graph_objs.Layout(**layout_kwargs)
    )
    fig.update_layout(
        margin={"l": 0, "r": 0, "b": 0, "t": 5, "pad": 0},
        template="none",
    )

    return fig


def auto_col_with(series: pd.Series) -> int:
    """Try to guess a good column width for the table visualization

    When rendered, plotly tables allow to rearrange columns interactively
    but unfortunately not to resize column width.

    This can lead to unreadable values or column names with no mean
    to make it readable.

    This function tries to guess a good column width based
    on column dtype and the column name (which is used as table header)
    in order to make

    """
    dtype_col_width = 0
    if series.dtype == float:  # noqa: SIM114
        dtype_col_width = 16
    elif series.dtype == int:
        dtype_col_width = 16
    elif series.dtype == bool:
        dtype_col_width = 6
    elif pd.api.types.is_string_dtype(series):
        dtype_col_width = max([min([max(series.str.len()), 200]), 12])
        # maximal len of strings in column but:
        # at least 12
        # at most 200
    elif is_datetime64_any_dtype(series):
        dtype_col_width = 32  # microsends isoformat
    elif series.dtype == object:
        dtype_col_width = 32
    else:
        dtype_col_width = 50
    return max([dtype_col_width, len(series.name) if series.name is not None else 5])


def table_fig_plotly_json(data: pd.DataFrame, auto_col_width: bool = True) -> Any:
    columns = list(data.columns)
    fig = go.Figure(
        data=[
            go.Table(
                columnwidth=(
                    [auto_col_with(data[col]) for col in columns] if auto_col_width else None
                ),
                header=dict(  # noqa: C408
                    values=columns, fill_color="paleturquoise", align="left"
                ),
                cells=dict(  # noqa: C408
                    values=[data[col] for col in columns],
                    fill_color="lavender",
                    align="left",
                ),
            )
        ]
    )

    layout_opts: dict = {
        "xaxis_title": "Time",
        "yaxis_title": "Values",
        "autosize": True,
        "height": 400,
    }
    # scrollbars should be visible:
    fig.update_layout(margin=dict(l=0, r=15.0, b=15.0, t=5, pad=0))  # noqa: C408
    fig.update_layout(**layout_opts)
    fig.update_yaxes(automargin=True)
    fig.update_xaxes(automargin=True)

    return fig

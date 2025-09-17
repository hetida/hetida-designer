import json
import logging
from datetime import datetime
from typing import Any

import pandas as pd
from pandas.tseries.frequencies import to_offset
from plotly.graph_objects import Figure  # type: ignore  # type: ignore

from hdhelpers.exceptions import HelperException, InsufficientPlottingData
from hdhelpers.plot_target_settings import PlotTargetStyle, get_plot_target_settings
from hdhelpers.time_helpers import _get_end_timestamp, _get_start_timestamp, modify_timezone

logger = logging.getLogger(__name__)


def get_colors_from_plot_target_settings() -> PlotTargetStyle:
    """Get thematically coherent colors for customizing plots

    Most color uses are already covered by the default settings of plotly_fig_to_json_dict().
    They are still included here in case coloring other plot elements in the same color is desired.
    Each color is given as a hex code, line_colors is a list of such, as specified in
    PlotTargetStyle.
    """
    plot_target_settings = get_plot_target_settings()

    return plot_target_settings.plot_target_style


def get_locale_from_plot_target_settings() -> str | None:
    """Get language for customizing text elements in plots

    Axis ticks are already covered by the default settings of plotly_fig_to_json_dict().
    The language of custom text elements should be adjusted to the locale.
    """
    plot_target_settings = get_plot_target_settings()

    return plot_target_settings.plot_target_locale


def _get_metric_metadate(series: pd.Series, metadate: str, default_return_value: str = "") -> str:
    """Get metadata from attrs["single_metric_metadata"]["structured_metadata"]["metric"]

    Tries to get the metadate from series.attrs according to the conventions of the hetida platform.
    If such metadata doesn't exist, the default_return_value is returned instead.
    """
    try:
        title = (
            series.attrs.get("single_metric_metadata", {})
            .get("structured_metadata", {})
            .get("metric", {})[metadate]
        )
        if not isinstance(title, str):
            msg = f"""Expected {metadate} to be a string, but it is not!
 Switching to default {metadate}."""
            raise HelperException(msg)
    except KeyError as exc:
        msg = f"""Expected attrs["single_metric_metadata"]["structured_metadata"]["metric"]
            ["{metadate}"] but got incorrect keys! Switching to default {metadate}"""
        logger.info(msg=msg, exc_info=exc)
        title = default_return_value
    except HelperException as exc:
        logger.warning(msg=msg, exc_info=exc)
        title = default_return_value
    return title


def _pad_start(timestamp: pd.Timestamp, padding: str | None) -> pd.Timestamp:
    """Subtracts padding from the timestamp

    That padding has to be formatted to be compatible with pandas.tseries.frequencies.to_offset().
    """
    if padding is None:
        return timestamp
    try:
        return timestamp - to_offset(padding)
    except ValueError as exc:
        raise HelperException(
            f"{padding} as padding value is an invalid duration, i.e. not a 'pandas frequency "
            "string'. Use something compatible with pandas.tseries.frequencies.to_offset()"
        ) from exc


def _pad_end(timestamp: pd.Timestamp, padding: str | None) -> pd.Timestamp:
    """Adds padding to the timestamp

    That padding has to be formatted to be compatible with pandas.tseries.frequencies.to_offset().
    """
    if padding is None:
        return timestamp
    try:
        return timestamp + to_offset(padding)
    except ValueError as exc:
        raise HelperException(
            f"{padding} as padding value is an invalid duration, i.e. not a 'pandas frequency "
            "string'. Use something compatible with pandas.tseries.frequencies.to_offset()"
        ) from exc


def get_and_pad_start_and_end_timestamp(
    series: pd.Series,
    timezone: str | None = None,
    start: datetime | str | None = None,
    start_padding: str | None = None,
    end: datetime | str | None = None,
    end_padding: str | None = None,
) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Get time period displayed on the x-axis

    Retrieves the start and end timestamps, prioritizing the explicit "start" and "end" parameters
    over the metadata of "series" and using the first and last index of the series if neither is
    given. If a padding is given, the respective timestamp is adjusted. That padding has to be
    formatted to be compatible with pandas.tseries.frequencies.to_offset().
    """
    # Get start and end
    start = _get_start_timestamp(series, start)
    end = _get_end_timestamp(series, end)

    if start is None:
        raise InsufficientPlottingData("No start timestamp found!")
    start_timestamp = start
    if end is None:
        raise InsufficientPlottingData("No end timestamp found!")
    end_timestamp = end

    # Convert timezone
    if timezone is not None:
        start_with_timezone = modify_timezone(start_timestamp, timezone)
        end_with_timezone = modify_timezone(end_timestamp, timezone)
    else:
        start_with_timezone = start_timestamp
        end_with_timezone = end_timestamp

    # Optionally add padding
    start_padded = _pad_start(start_with_timezone, start_padding)
    end_padded = _pad_end(end_with_timezone, end_padding)

    return start_padded, end_padded


def get_y_axis_label(series: pd.Series, default_title: str = "", default_unit: str = "") -> str:
    """Get full y-axis label from metadata

    Combines the title and unit provided by _get_display_name and _get_unit.
    """
    title = _get_metric_metadate(series, "short_display_name", default_title)
    unit = _get_metric_metadate(series, "unit", default_unit)
    if len(unit) > 0:
        title = f"{title} [{unit}]"
    return title


def _serialize_plotly_fig(v: dict[str, Any] | Figure) -> Any:
    if isinstance(v, dict):
        return v

    # possibly quite inefficient (multiple serialisation / deserialization) but
    # guarantees that the PlotlyJSONEncoder is used and so the resulting Json
    # should be definitely compatible with the plotly javascript library:

    # Whats the difference using json.loads(json.dumps(fig_dict_obj, cls=PlotlyJSONEncoder))
    # or employing fig.to_plotly_json()
    return json.loads(v.to_json())


def plotly_fig_to_json_dict(  # noqa: PLR0912, PLR0915
    fig: Figure,
    add_config_settings: bool = True,
    hide_legend: bool | None = None,
    hide_x_title: bool | None = None,
    remove_plotly_bar: bool | None = None,
    remove_plotly_icon: bool = True,
    update_x_axes_tickformat: bool | None = None,
    use_default_standoff: bool = False,
    use_minimum_margin: bool = True,
    use_muplot_axes_color: bool | None = None,
    use_muplot_grid: bool | None = None,
    use_muplot_line_and_markers: bool | None = None,
    use_platform_background: bool | None = None,
    use_platform_colorway: bool = True,
    use_platform_defaults: bool = True,
    use_simple_white_template: bool = True,
) -> Any:
    """Turn Plotly figure into a Python dict-like object

    This function can be used in visualization components to obtain the
    correct plotly json-like object from a Plotly Figure object.

    Additionally, this function has a dozen boolean parameters that can be
    set to standardize certain aspects of the plot styling in accordance
    with the hetida platform.

    See visualization components from the accompanying base components for
    examples on usage.
    """
    if use_platform_defaults:
        if hide_legend is None:
            hide_legend = True
        if hide_x_title is None:
            hide_x_title = True
        if remove_plotly_bar is None:
            remove_plotly_bar = True
        if update_x_axes_tickformat is None:
            update_x_axes_tickformat = True
        if use_default_standoff is None:
            use_default_standoff = True
        if use_muplot_axes_color is None:
            use_muplot_axes_color = True
        if use_muplot_grid is None:
            use_muplot_grid = True
        if use_muplot_line_and_markers is None:
            use_muplot_line_and_markers = True
        if use_platform_background is None:
            use_platform_background = True
    else:
        if hide_legend is None:
            hide_legend = False
        if hide_x_title is None:
            hide_x_title = False
        if remove_plotly_bar is None:
            remove_plotly_bar = False
        if update_x_axes_tickformat is None:
            update_x_axes_tickformat = False
        if use_default_standoff is None:
            use_default_standoff = False
        if use_muplot_axes_color is None:
            use_muplot_axes_color = False
        if use_muplot_grid is None:
            use_muplot_grid = False
        if use_muplot_line_and_markers is None:
            use_muplot_line_and_markers = False
        if use_platform_background is None:
            use_platform_background = False

    plot_target_settings = get_plot_target_settings()

    if use_platform_colorway and plot_target_settings.plot_target_style.line_colors is not None:
        fig.update_layout(colorway=plot_target_settings.plot_target_style.line_colors)

    if use_simple_white_template:
        fig.update_layout({"template": "simple_white"})

    if (
        use_platform_background
        and plot_target_settings.plot_target_style.background_color is not None
    ):
        fig.update_layout(
            {
                "paper_bgcolor": plot_target_settings.plot_target_style.background_color,
                "plot_bgcolor": "rgba(0,0,0,0)",
            }
        )

    if hide_legend:
        fig.update_layout(showlegend=False)

    if hide_x_title:
        fig.update_xaxes(title_text="")

    if update_x_axes_tickformat and plot_target_settings.datetime_tick_format is not None:
        fig.update_xaxes(tickformat=plot_target_settings.datetime_tick_format)

    if (
        use_muplot_axes_color
        and plot_target_settings.plot_target_style.axes_label_color is not None
    ):
        fig.update_xaxes(color=plot_target_settings.plot_target_style.axes_label_color)
        fig.update_yaxes(color=plot_target_settings.plot_target_style.axes_label_color)

    if use_default_standoff:
        fig.update_yaxes(title_standoff=5)

    if use_muplot_line_and_markers:
        try:
            fig.update_traces(
                {
                    "marker": {"size": 3},
                    "line": {"width": 1},
                    "mode": "lines+markers",
                    "marker_symbol": "circle",
                }
            )
        except ValueError:
            logger.debug(
                msg="Skipping use_muplot_line_and_markers "
                "because this plot does not have compatible lines and markers"
            )

    if use_minimum_margin:
        fig.update_layout(
            {"margin": {"autoexpand": True, "l": 0, "r": 0, "b": 0, "t": 0, "pad": 0}}
        )

    if use_muplot_grid and plot_target_settings.plot_target_style.grid_color is not None:
        grid_dict = {
            "showgrid": True,
            "gridcolor": plot_target_settings.plot_target_style.grid_color,
            "zeroline": True,
            "zerolinecolor": plot_target_settings.plot_target_style.grid_color,
        }
        fig.update_layout({"xaxis": grid_dict, "yaxis": grid_dict})

    fig_dict_obj = _serialize_plotly_fig(fig)
    if not "config" in fig_dict_obj:
        fig_dict_obj["config"] = {}

    if add_config_settings and plot_target_settings.plot_target_locale is not None:
        fig_dict_obj["config"]["locale"] = plot_target_settings.plot_target_locale

    if remove_plotly_bar:
        fig_dict_obj["config"]["displayModeBar"] = False

    if remove_plotly_icon:
        fig_dict_obj["config"]["displaylogo"] = False

    # possibly quite inefficient (multiple serialisation / deserialization) but
    # guarantees that the PlotlyJSONEncoder is used and so the resulting Json
    # should be definitely compatible with the plotly javascript library:
    return fig_dict_obj

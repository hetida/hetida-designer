import datetime
import json
import logging
from typing import Any

import pandas as pd
from plotly.graph_objects import Figure
from plotly.utils import PlotlyJSONEncoder
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class StatusColor(BaseModel):
    """Collection of status-related colors

    Unlike the other colors in PlotTargetSettings, these colors do not have a predefined use.
    Instead they should be used contextually, e.g. when displaying the sensor status of an asset.
    """

    success_color: str | None = Field(
        None, description="Color of markers that signal success as a hexcode"
    )
    error_color: str | None = Field(
        None, description="Color of markers that signal errors as a hexcode"
    )
    warn_color: str | None = Field(
        None, description="Color of markers that signal warnings as a hexcode"
    )
    info_color: str | None = Field(
        None, description="Color of markers that signal informativeness as a hexcode"
    )


class PlotTargetSettings(BaseModel):
    """Settings that plot components can/should use

    Some Plotly settings like locale or the timezone of timestamps must be set
    by Python and cannot easily be set by plotly.js in a frontend.

    They can be provided to execution endpoints as part of the ExecByIdBase payload,
    are made accessible to components using the execution context.

    hdutils provides helper functions to access them at runtime.
    """

    plot_target_timezone: str | None = Field(
        None,
        description=(
            "The timezone plot components should use for datetime axes etc."
            " Usually via"
            " s.index=pd.to_datetime(s.index, utc=True).tz_convert(plot_target_timezone)"
        ),
        examples=["Europe/Berlin"],
    )
    plot_target_locale: str | None = Field(
        None,
        description=(
            "Locale to set for plots, e.g. to write weekdays in the user's language."
            " This has to be set in the config of the plotly figure dict and the plotly.js "
            "must have the associated plotly local scripts loaded."
        ),
    )
    target_darkmode: bool = Field(
        False, description="Whether plots should be layouted/configured for darkmode"
    )
    datetime_tick_format: str | None = Field(
        None, description="Tickformat to use for datetime axes", examples=["%H:%M<br>%d.%m.%Y"]
    )
    datetime_x_axes_range_start: datetime.datetime | None = Field(
        None, description="datetime range start which plots should set as x axis range"
    )

    datetime_x_axes_range_end: datetime.datetime | None = Field(
        None, description="datetime range end which plots should set as x axis range"
    )


def get_plot_target_settings() -> PlotTargetSettings:
    """Obtain plot settings from runtime execution context.

    If hetdesrun is not importable or this context field is not set,
    return default values.
    """
    try:
        from hdhelpers.context import get_runtime_exec_context

        return get_runtime_exec_context().plot_target_settings
    except ImportError:
        logger.warning("Could not load runtime exec context, import failed! Switch to defaults.")
        # return defaults if hetdesrun is not available as import
        return PlotTargetSettings()


class PlotTargetStyle(BaseModel):
    color_scheme: str | None = Field(  # TODO: Remove this once depencencies are resolved
        None,
        description=(
            "Name of the color scheme for purposes such as whitelabeling."
            "Might eventually absorb target_darkmode."
        ),
    )
    line_colors: list[str] | None = Field(
        None,
        description=(
            "List of colors to be used for plot traces.",
            "Will be set as colorway by plotly_fig_to_json_dict,",
            "so the colors are only applied where no explicit trace color is set",
        ),
    )
    background_color: str | None = Field(
        None, description="Color of the panel background as a hex code"
    )
    axes_label_color: str | None = Field(
        None, description="Color of the tick labels of all axes as a hex code"
    )
    grid_color: str | None = Field(
        None, description="Color of the grid as a hex code that may be drawn into the background"
    )
    status_color: StatusColor | None = Field(
        None, description="Has the properties success_color, error_color, warn_color, info_color"
    )


def get_colors(color_scheme: str | None = None) -> dict[str, str]:
    """Get color_scheme by name for purposes such as whitelabeling

    So far, only the default color_scheme of the fuseki corporate identity is available.
    Further color schemes will be added once the whitelabeling concept is finished.
    """
    # TODO: Get plot_target_settings here

    match color_scheme:
        case "fuseki" | "fuseki_light" | None:
            return {
                "background_color": "white",
                "blue": "#80B0EC",
                "dark_blue": "#2D679E",
                "dark_red": "#A1262A",
                "gray": "#8C8C98",
                "green": "#2FAE53",
                "grid_color": "lightgrey",
                "light_green": "#89CE6E",
                "light_orange": "#FFB058",
                "orange": "#EB7C45",
                "purple": "#BD7ABB",
                "red": "#EB6962",
                "yellow": "#E5CF64",
            }


def _get_display_name(series: pd.Series, default_title: str = "") -> str:
    """Get name for y-axis label

    Tries to get the name from the standard metadata of the hetida .platform.
    If such metadata doesn't exist, the default_title is returned instead.
    """
    try:
        title = (
            series.attrs.get("single_metric_metadata")
            .get("structured_metadata")
            .get("metric")
            .get("short_display_name")
        )
    except AttributeError:
        title = default_title
    return title


def _get_unit(series: pd.Series, default_unit: str = "") -> str:
    """Get unit for y-axis label

    Tries to get the unit from the standard metadata of the hetida .platform.
    If such metadata doesn't exist, the default_unit is returned instead.
    """
    try:
        unit = (
            series.attrs.get("single_metric_metadata")
            .get("structured_metadata")
            .get("metric")
            .get("unit")
        )
    except AttributeError:
        unit = default_unit
    return unit


def get_period(series: pd.Series, timezone: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Get time period displayed on the x-axis

    TODO: The finalized functionality should be described here.
    """
    start = series.attrs.get("single_metric_dataset_metadata").get("ref_interval_start_timestamp")
    end = series.attrs.get("single_metric_dataset_metadata").get("ref_interval_end_timestamp")

    start = pd.to_datetime(start, unit="s", utc=True).tz_convert(timezone)
    end = pd.to_datetime(end, unit="s", utc=True).tz_convert(timezone) + pd.Timedelta("1h")

    return start, end


def set_layout(
    color_scheme: dict | None = None,
    legend_position: dict | str | None = None,
    margins: dict | None = None,
    show_grid: bool = True,
    template: str = "simple_white",
    show_zero_line: bool = True,
) -> dict[str, Any]:
    """Construct the 'update layout' dict for plotly

    Uses the whitelabeling-compatible color scheme. The legend configuration is organized in a match
    statement to allow for additional presets in the future. Margins minimize white space by default
    but can be overwritten via custom dict.
    """
    colors = get_colors(color_scheme)
    # Default lagert man besser vor
    legend = {}
    show_legend = False
    match legend_position:
        case None:
            legend = {}
            show_legend = False
        case "plotly_default":  # Das kommt weg
            legend = {}
            show_legend = True
        case dict():  # Das anders lösen
            legend = legend_position
            show_legend = True
    grid_dict = {
        "showgrid": show_grid,
        "gridcolor": colors["grid_color"],
        "zeroline": show_zero_line,
        "zerolinecolor": colors["grid_color"],
    }
    if margins is None:
        margins = {"autoexpand": True, "l": 0, "r": 0, "b": 0, "t": 0, "pad": 0}
    return {
        "margin": margins,
        "legend": legend,
        "template": template,
        "plot_bgcolor": colors["background_color"],
        "xaxis": grid_dict,
        "yaxis": grid_dict,
        "autosize": True,
        "showlegend": show_legend,
    }


def set_traces(
    line_width: int = 1,
    marker_mode: str = "lines+markers",
    marker_size: int = 3,
    marker_symbol: str = "circle",
) -> dict[str, str | dict[str, int]]:
    """Construct 'update traces' dict for plotly

    The default inputs are the standard settings for the hetida .platform.
    """
    return {
        "marker": {"size": marker_size},
        "line": {"width": line_width},
        "mode": marker_mode,
        "marker_symbol": marker_symbol,
    }


def set_xaxes(
    series: pd.Series, tick_format: str = "%H:%M<br>%d.%m.%Y"
) -> dict[str, bool | str | tuple[pd.Timestamp, pd.Timestamp]]:
    """Construct 'update xaxes' dict for plotly

    TODO: The finalized functionality should be described here.
    """
    return {
        "automargin": True,
        "range": (get_period(series)),
        "tickformat": tick_format,
        "title_text": "",
    }


def set_yaxes(
    series: pd.Series, standoff: int = 5, default_title: str = "", default_unit: str = ""
) -> dict[str, bool | int | str]:
    """Construct 'update yaxes' dict for plotly

    Combines the title and unit provided by get_display_name and get_unit and sets the standoff
    between y-axis and label.
    """
    title = _get_display_name(series, default_title)
    unit = _get_unit(series, default_unit)
    if len(unit) > 0:
        title = f"{title} [{unit}]"
    return {
        "automargin": True,
        "title_standoff": standoff,
        "title_text": title,
    }


def modify_timezone() -> None:
    """Modifies timestamps to a certain timezone

    TODO: modify_timezone is the last function to be overhauled; this is a placeholder
    """


def plotly_fig_to_json_dict(
    fig: Figure,
    add_config_settings: bool = True,
    hide_legend: bool = True,
    update_x_axes_tickformat: bool = True,
    use_default_standoff: bool = True,
    use_minimum_margin: bool = True,
    use_muplot_grid: bool = True,
    use_muplot_line_and_markers: bool = True,
    use_platform_background: bool = True,
    use_simple_white_template: bool = True,
) -> Any:
    """Turn Plotly figure into a Python dict-like object

    This function can be used in visualization components to obtain the
    correct plotly json-like object from a Plotly Figure object.

    See visualization components from the accompanying base components for
    examples on usage.
    """

    plot_target_settings = get_plot_target_settings()

    if plot_target_settings.line_colors is not None:
        fig.update_layout(colorway=plot_target_settings.line_colors)

    if use_simple_white_template:
        fig.update_layout({"template": "simple_white"})

    if use_platform_background and plot_target_settings.background_color is not None:
        fig.update_layout(
            {
                "paper_bgcolor": plot_target_settings.background_color,
                "plot_bgcolor": "rgba(0,0,0,0)",
            }
        )

    if hide_legend:
        fig.update_layout(showlegend=False)

    if update_x_axes_tickformat and plot_target_settings.datetime_tick_format is not None:
        fig.update_xaxes(tickformat=plot_target_settings.datetime_tick_format)

    if use_default_standoff:
        fig.update_yaxes(title_standoff=5)

    if use_muplot_line_and_markers:
        fig.update_traces(
            {
                "marker": {"size": 3},
                "line": {"width": 1},
                "mode": "lines+markers",
                "marker_symbol": "circle",
            }
        )

    if use_minimum_margin:
        fig.update_layout(
            {"marker": {"autoexpand": True, "l": 0, "r": 0, "b": 0, "t": 0, "pad": 0}}
        )

    if use_muplot_grid and plot_target_settings.grid_color is not None:
        grid_dict = {
            "showgrid": True,
            "gridcolor": plot_target_settings.grid_color,
            "zeroline": True,
            "zerolinecolor": plot_target_settings.grid_color,
        }
        fig.update_layout({"xaxis": grid_dict, "yaxis": grid_dict})

    fig_dict_obj = fig.to_plotly_json()
    if not "config" in fig_dict_obj:
        fig_dict_obj["config"] = {}

    if add_config_settings and plot_target_settings.plot_target_locale is not None:
        fig_dict_obj["config"]["locale"] = plot_target_settings.plot_target_locale

    # possibly quite inefficient (multiple serialisation / deserialization) but
    # guarantees that the PlotlyJSONEncoder is used and so the resulting Json
    # should be definitely compatible with the plotly javascript library:
    return json.loads(json.dumps(fig_dict_obj, cls=PlotlyJSONEncoder))

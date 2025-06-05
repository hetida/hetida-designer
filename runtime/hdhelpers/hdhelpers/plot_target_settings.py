import datetime
import json
import logging
from typing import Any

from plotly.graph_objects import Figure
from plotly.utils import PlotlyJSONEncoder
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class StatusColors(BaseModel):
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

    hdhelpers provides helper functions to access them at runtime.
    """

    plot_target_timezone: str | None = Field(
        None,
        description="""The timezone plot components should use for datetime axes etc.
             Usually via
             s.index=pd.to_datetime(s.index, utc=True).tz_convert(plot_target_timezone)""",
        examples=["Europe/Berlin"],
    )
    plot_target_locale: str | None = Field(
        None,
        description="""Locale to set for plots, e.g. to write weekdays in the user's language.
             This has to be set in the config of the plotly figure dict and the plotly.js
             must have the associated plotly local scripts loaded.""",
    )
    line_colors: list[str] | None = Field(
        None,
        description="""List of colors to be used for plot traces.
             Will be set as colorway by plotly_fig_to_json_dict,
             so the colors are only applied where no explicit trace color is set""",
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
    status_colors: StatusColors = Field(
        StatusColors(),
        description="Has the properties success_color, error_color, warn_color, info_color",
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


def plotly_fig_to_json_dict(  # noqa: PLR0912
    fig: Figure,
    add_config_settings: bool = True,
    hide_legend: bool = False,
    hide_x_title: bool = False,
    update_x_axes_tickformat: bool = False,
    use_default_standoff: bool = False,
    use_minimum_margin: bool = True,
    use_muplot_axes_color: bool = False,
    use_muplot_grid: bool = False,
    use_muplot_line_and_markers: bool = False,
    use_platform_background: bool = False,
    use_platform_defaults: bool = False,
    use_simple_white_template: bool = True,
) -> Any:
    """Turn Plotly figure into a Python dict-like object

    This function can be used in visualization components to obtain the
    correct plotly json-like object from a Plotly Figure object.

    See visualization components from the accompanying base components for
    examples on usage.
    """
    if use_platform_defaults:
        hide_legend = True
        hide_x_title = True
        update_x_axes_tickformat = True
        use_default_standoff = True
        use_muplot_axes_color = True
        use_muplot_grid = True
        use_muplot_line_and_markers = True
        use_platform_background = True
        # TODO: Wollen wir grundsätzlich use_simple_white_template = True oder nur hier?

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

    if hide_x_title:
        fig.update_xaxes(title_text="")

    if update_x_axes_tickformat and plot_target_settings.datetime_tick_format is not None:
        fig.update_xaxes(tickformat=plot_target_settings.datetime_tick_format)

    if use_muplot_axes_color and plot_target_settings.axes_label_color is not None:
        fig.update_xaxes(color=plot_target_settings.axes_label_color)
        fig.update_yaxes(color=plot_target_settings.axes_label_color)

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
            {"margin": {"autoexpand": True, "l": 0, "r": 0, "b": 0, "t": 0, "pad": 0}}
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

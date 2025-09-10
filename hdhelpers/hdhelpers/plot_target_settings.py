import datetime
import logging

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


class PlotTargetStyle(BaseModel):
    axes_label_color: str | None = Field(
        None, description="Color of the tick labels of all axes as a hex code"
    )
    background_color: str | None = Field(
        None, description="Color of the panel background as a hex code"
    )
    grid_color: str | None = Field(
        None, description="Color of the grid as a hex code that may be drawn into the background"
    )
    line_colors: list[str] | None = Field(
        None,
        description="""List of colors to be used for plot traces.
            Will be set as colorway by plotly_fig_to_json_dict,
            so the colors are only applied where no explicit trace color is set""",
    )
    status_colors: StatusColors = Field(
        StatusColors(),  # type: ignore
        description="Has the properties success_color, error_color, warn_color, info_color",
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
    plot_target_style: PlotTargetStyle = Field(
        PlotTargetStyle(),  # type: ignore
        description="Colors to use in the plot",
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
        from hetdesrun.runtime.context import (  # type: ignore  # noqa: PLC0415
            get_runtime_exec_context,
        )

        plot_target_settings = get_runtime_exec_context().plot_target_settings
        if not isinstance(plot_target_settings, PlotTargetSettings):
            raise TypeError("plot_target_settings must be instance of PlotTargetSettings")

        return plot_target_settings
    except (ImportError, TypeError):
        logger.warning("Could not load runtime exec context, import failed! Switch to defaults.")
        # return defaults if hetdesrun is not available as import
        return PlotTargetSettings()  # type: ignore

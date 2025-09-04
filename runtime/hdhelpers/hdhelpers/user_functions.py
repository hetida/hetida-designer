import json
import logging
from typing import Any
from warnings import warn

import pandas as pd
import pytz
from plotly.graph_objects import Figure
from plotly.utils import PlotlyJSONEncoder

from hdhelpers.exceptions import HelperException
from hdhelpers.helper_functions import (
    _get_display_name,
    _get_end_timestamp,
    _get_start_timestamp,
    _get_unit,
    _pad_end,
    _pad_start,
)
from hdhelpers.plot_target_settings import PlotTargetStyle, get_plot_target_settings

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


def get_title_with_unit(series: pd.Series, default_title: str = "", default_unit: str = "") -> str:
    """Get full y-axis label from metadata

    Combines the title and unit provided by _get_display_name and _get_unit.
    """
    title = _get_display_name(series, default_title)
    unit = _get_unit(series, default_unit)
    if len(unit) > 0:
        title = f"{title} [{unit}]"
    return title


def get_and_pad_start_and_end_timestamp(
    series: pd.Series,
    timezone: str | None = None,
    start: str | None = None,
    start_padding: str | None = None,
    end: str | None = None,
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
        raise HelperException("No start timestamp found!")
    if end is None:
        raise HelperException("No end timestamp found!")

    # Convert timezone
    start = modify_timezone(start, timezone)
    end = modify_timezone(end, timezone)

    # Optionally add padding
    start = _pad_start(start, start_padding)
    end = _pad_end(end, end_padding)

    return start, end


def modify_timezone(  # noqa: PLR0912
    object_to_convert: pd.Timestamp | pd.Series | pd.DataFrame,
    to_timezone: str,
    column_name: str | None = None,
    column_names: list[str] | None = None,
    convert_index: bool = True,
) -> pd.Timestamp | pd.Series | pd.DataFrame:
    """Modifies timestamps to a certain timezone

    Keyword arguments:
    object_to_convert -- pd.Timestamp, pd.Series or pd.DataFrame where timezone is modified
    to_timezone -- timezone to convert to, e.g. for German time use Europe/Berlin.
    See possible timezone strings in pandas tz_convert method or pytz all_timezones list.
    column_name -- column_name to apply, default is index as pd.Series have timestamps in index
    """
    if not isinstance(object_to_convert, pd.Timestamp | pd.Series | pd.DataFrame):
        raise TypeError(
            f"object_to_convert is {type(object_to_convert)} not pd.Series | pd.DataFrame"
        )
    if column_names is None:
        column_names = []

    try:
        if "plot_target" in to_timezone:
            plot_target_settings = get_plot_target_settings()
            if plot_target_settings.plot_target_timezone is None:
                raise HelperException("Missing timezone in PlotTargetSettings.plot_target_timezone")
            if plot_target_settings.plot_target_timezone is not None:
                to_timezone = plot_target_settings.plot_target_timezone

        if isinstance(object_to_convert, pd.Timestamp):
            return object_to_convert.tz_convert(to_timezone)

        if isinstance(object_to_convert, pd.Series):
            new_object = object_to_convert.to_frame(name=object_to_convert.name)
        else:
            new_object = object_to_convert.copy(deep=True)

        # Both column_name branches exist purely for backwards compatibility,
        # only convert_index should stay.
        if column_name is None and convert_index:
            new_object.index = pd.to_datetime(new_object.index).tz_convert(to_timezone)
        if column_name is not None:
            warn(
                """The parameter 'column_name' will soon be deprecated in favor of
                the more flexible 'columns_names'""",
                DeprecationWarning,
                stacklevel=2,
            )
            new_object[column_name] = pd.to_datetime(new_object[column_name]).dt.tz_convert(
                to_timezone
            )
            column_names.append(column_name)

        if len(column_names) == 0:
            if isinstance(object_to_convert, pd.Series):
                new_object.index = pd.to_datetime(new_object.index).tz_convert(to_timezone)
                msg = f"Converted index to datetime starting with {object_to_convert.index[0]}"
                logger.debug(msg=msg)
            elif isinstance(new_object, pd.DataFrame) and "timestamp" in new_object.columns:
                new_object["timestamp"] = pd.to_datetime(new_object["timestamp"]).dt.tz_convert(
                    to_timezone
                )
                msg = f"""Converted column "timestamp" to datetime starting with
                {object_to_convert["timestamp"][0]}"""
                logger.debug(msg=msg)
        if len(column_names) > 0:
            for column in column_names:
                new_object[column] = pd.to_datetime(new_object[column]).dt.tz_convert(to_timezone)

        if isinstance(object_to_convert, pd.Series):
            new_object = pd.Series(
                new_object[object_to_convert.name],
                index=new_object.index,
                name=object_to_convert.name,
            )

        return new_object

    except pytz.exceptions.UnknownTimeZoneError as exc:
        possible_timezone = pytz.all_timezones
        raise ValueError(f"""Timezone not known, please choose from {possible_timezone}""") from exc
    except (TypeError, AttributeError) as exc:
        raise TypeError("Entries to convert do not contain valid timestamps") from exc
    except KeyError as exc:
        exc.add_note(f"Column name {column_name} not in object_to_convert")
        raise


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

    plot_target_settings = get_plot_target_settings()

    if plot_target_settings.plot_target_style.line_colors is not None:
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

    if use_muplot_grid and plot_target_settings.plot_target_style.grid_color is not None:
        grid_dict = {
            "showgrid": True,
            "gridcolor": plot_target_settings.plot_target_style.grid_color,
            "zeroline": True,
            "zerolinecolor": plot_target_settings.plot_target_style.grid_color,
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

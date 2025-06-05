import logging
from typing import TypedDict

import pandas as pd
import pytz
from pandas.tseries.frequencies import to_offset

from hdhelpers.exceptions import HelperException
from hdhelpers.plot_target_settings import get_plot_target_settings

logger = logging.getLogger(__name__)


class Colors(TypedDict):
    axes_label_color: str | None
    background_color: str | None
    error_color: str | None
    grid_color: str | None
    info_color: str | None
    line_colors: list[str | None]
    success_color: str | None
    warn_color: str | None


def get_colors_from_plot_target_settings() -> Colors:
    """Get thematically coherent colors for customizing plots

    Most color uses are already covered by the default settings of plotly_fig_to_json_dict().
    They are still included here in case coloring other plot elements in the same color is desired.
    Each color is given as a hex code, line_colors is a list of such, as specified in
    PlotTargetSettings.
    """
    plot_target_settings = get_plot_target_settings()

    return {
        "axes_label_color": plot_target_settings.axes_label_color,
        "background_color": plot_target_settings.background_color,
        "error_color": plot_target_settings.status_colors.error_color,
        "grid_color": plot_target_settings.grid_color,
        "info_color": plot_target_settings.status_colors.info_color,
        "line_colors": plot_target_settings.line_colors,
        "success_color": plot_target_settings.status_colors.success_color,
        "warn_color": plot_target_settings.status_colors.warn_color,
    }


def get_locale_from_plot_target_settings() -> str | None:
    """Get language for customizing text elements in plots

    Axis ticks are already covered by the default settings of plotly_fig_to_json_dict().
    Custom text elements might want to adjust their language to the locale.
    """
    plot_target_settings = get_plot_target_settings()

    return plot_target_settings.plot_target_locale


def _get_display_name(series: pd.Series, default_title: str = "") -> str:
    """Get name for y-axis label from metadata

    Tries to get the name from the standard metadata of the hetida .platform.
    If such metadata doesn't exist, the default_title is returned instead.
    """
    try:
        title = series.attrs["single_metric_metadata"]["structured_metadata"]["metric"][
            "short_display_name"
        ]
    except (TypeError, KeyError) as exc:
        msg = (
            'Expected attrs["single_metric_metadata"]["structured_metadata"]["metric"]',
            '["short_display_name"] but got incorrect keys',
        )
        logger.warning(msg=msg, exc_info=exc)
        title = default_title
    return title


def _get_unit(series: pd.Series, default_unit: str = "") -> str:
    """Get unit for y-axis label from metadata

    Tries to get the unit from the standard metadata of the hetida .platform.
    If such metadata doesn't exist, the default_unit is returned instead.
    """
    try:
        unit = series.attrs["single_metric_metadata"]["structured_metadata"]["metric"]["unit"]
    except (TypeError, KeyError) as exc:
        msg = 'Expected attrs["single_metric_metadata"]["structured_metadata"]["metric"]["unit"'
        "] but got incorrect keys"
        logger.warning(msg=msg, exc_info=exc)
        unit = default_unit
    return unit


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
    start = _get_start_or_end_timestamp(series, start)
    end = _get_start_or_end_timestamp(series, end, False)

    # Convert timezone
    start = _convert_timezone(start, timezone)
    end = _convert_timezone(end, timezone)

    # Optionally add padding
    start = _pad_start_or_end(start, start_padding)
    end = _pad_start_or_end(end, end_padding, False)

    return start, end


def _pad_start_or_end(
    timestamp: pd.Timestamp, padding: str | None, is_start: bool = True
) -> pd.Timestamp | None:
    """Adds or subtracts padding from the timestamp

    That padding has to be formatted to be compatible with pandas.tseries.frequencies.to_offset().
    """
    if padding is None:
        return timestamp
    try:
        if is_start:
            return timestamp - to_offset(padding)
        return timestamp + to_offset(padding)
    except ValueError as exc:
        raise HelperException(
            f"{padding} as padding value is an invalid frequency. "
            "Use something compatible with pandas.tseries.frequencies.to_offset()"
        ) from exc


def _get_start_or_end_timestamp(
    series: pd.Series, timestamp: str | None, is_start: bool = True
) -> pd.Timestamp | None:
    """Get the timestamp in question hierarchically

    Will check for an explicit input timestamp first, then check PlotTargetSettings, then the series
     metadata, and if all else fails, will take the first series entry as start and the last as end.
    If the series is also empty, None is returned.
    """
    if timestamp is not None:
        return _to_datetime(timestamp)

    plot_target_settings = get_plot_target_settings()

    if is_start:
        timestamp = plot_target_settings.datetime_x_axes_range_start
        key = "ref_interval_start_timestamp"
        idx = 0
    else:
        timestamp = plot_target_settings.datetime_x_axes_range_end
        key = "ref_interval_end_timestamp"
        idx = -1

    if timestamp is None:
        try:
            timestamp = series.attrs["single_metric_dataset_metadata"][key]
        except (AttributeError, KeyError) as exc:
            msg = f"""Expected key structure not found:
             attrs["single_metric_dataset_metadata"]["{key}"]"""
            logger.warning(msg=msg, exc_info=exc)
            if len(series) > 0:
                timestamp = series.index[idx]

    return _to_datetime(timestamp)


def _convert_timezone(timestamp: int | str, timezone: str | None = None) -> pd.Timestamp | None:
    # TODO: This should probably be absorbed by modify_timezone
    if timezone is None:
        plot_target_settings = get_plot_target_settings()
        timezone = plot_target_settings.plot_target_timezone

    if timezone is None:
        timezone = "utc"
    if timestamp is not None:
        timestamp = _to_datetime(timestamp).tz_convert(timezone)
    return timestamp


def _to_datetime(timestamp: str | int | None) -> pd.Timestamp | None:
    """TODO: Doc-String fehlt noch!"""
    if isinstance(timestamp, int):
        # It's usually "seconds till newyears 1970", but the default unit is ns.
        timestamp = pd.to_datetime(timestamp, unit="s", utc=True)
    else:
        # String Timestamps can be converted with ns precision without issues
        timestamp = pd.to_datetime(timestamp, utc=True)
    return timestamp


def modify_timezone(
    object_to_convert: pd.Series | pd.DataFrame, to_timezone: str, column_name: str | None = None
) -> pd.Series | pd.DataFrame:
    """Modifies timestamps to a certain timezone

    Keyword arguments:
    object_to_convert -- pd.Series or pd.DataFrame where timezone in index or column is modified
    to_timezone -- timezone into convert, e.g. for German time use Europe/Berlin.
    See possible timezone strings in pandas tz_convert method or pytz all_timezones list.
    column_name -- column_name to apply, default is index as pd.Series have timestamps in index
    """
    # TODO: Kein pytz verwenden!
    if not isinstance(object_to_convert, pd.Series | pd.DataFrame):
        raise TypeError(
            f"object_to_convert is {type(object_to_convert)} not pd.Series | pd.DataFrame"
        )

    try:
        if isinstance(object_to_convert, pd.Series):
            new_object = object_to_convert.to_frame(name=object_to_convert.name)
        else:
            new_object = object_to_convert.copy(deep=True)

        if column_name is None:
            new_object.index = new_object.index.tz_convert(to_timezone)
        else:
            new_object[column_name] = new_object[column_name].dt.tz_convert(to_timezone)

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

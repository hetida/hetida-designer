import logging
from typing import TypedDict
from warnings import warn

import pandas as pd
import pytz
from pandas.tseries.frequencies import to_offset

from hdhelpers.exceptions import HelperException
from hdhelpers.plot_target_settings import get_plot_target_settings

logger = logging.getLogger(__name__)


class Colors(TypedDict):
    # TODO: In die PlotTargetSettings verschieben, damit in get_colors_from_plot_target_settings
    # keine string-keys hat (das heißt composition over inheritance)
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
    The language of custom text elements should be adjusted to the locale.
    """
    plot_target_settings = get_plot_target_settings()

    return plot_target_settings.plot_target_locale


def _get_display_name(series: pd.Series, default_title: str = "") -> str:
    """Get name for y-axis label from metadata

    Tries to get the name from series.attrs according to the conventions of thehetida platform.
    If such metadata doesn't exist, the default_title is returned instead.
    """
    try:
        title = (
            series.attrs.get("single_metric_metadata", {})
            .get("structured_metadata", {})
            .get("metric", {})["short_display_name"]
        )
    except KeyError as exc:
        msg = (
            'Expected attrs["single_metric_metadata"]["structured_metadata"]["metric"]',
            '["short_display_name"] but got incorrect keys',
        )
        logger.warning(msg=msg, exc_info=exc)
        title = default_title
    return title


def _get_unit(series: pd.Series, default_unit: str = "") -> str:
    """Get unit for y-axis label from metadata

    Tries to get the unit from series.attrs according to the conventions of thehetida platform.
    If such metadata doesn't exist, the default_unit is returned instead.
    """
    try:
        unit = (
            series.attrs.get("single_metric_metadata", {})
            .get("structured_metadata", {})
            .get("metric", {})["unit"]
        )
    except KeyError as exc:
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
    start = _get_start_timestamp(series, start)
    end = _get_end_timestamp(series, end)

    # Convert timezone
    start = modify_timezone(start, timezone)
    end = modify_timezone(end, timezone)

    # Optionally add padding
    start = _pad_start(start, start_padding)
    end = _pad_end(end, end_padding)

    return start, end


def _pad_start(timestamp: pd.Timestamp, padding: str | None) -> pd.Timestamp | None:
    """Subtracts padding from the timestamp

    That padding has to be formatted to be compatible with pandas.tseries.frequencies.to_offset().
    """
    if padding is None:
        return timestamp
    try:
        return timestamp - to_offset(padding)
    except ValueError as exc:
        raise HelperException(
            f"{padding} as padding value is an invalid frequency. "
            "Use something compatible with pandas.tseries.frequencies.to_offset()"
        ) from exc


def _pad_end(timestamp: pd.Timestamp, padding: str | None) -> pd.Timestamp | None:
    """Adds padding to the timestamp

    That padding has to be formatted to be compatible with pandas.tseries.frequencies.to_offset().
    """
    if padding is None:
        return timestamp
    try:
        return timestamp + to_offset(padding)
    except ValueError as exc:
        raise HelperException(
            f"{padding} as padding value is an invalid frequency. "
            "Use something compatible with pandas.tseries.frequencies.to_offset()"
        ) from exc


def _get_start_timestamp(series: pd.Series, timestamp: str | None) -> pd.Timestamp | None:
    """Get the start timestamp  hierarchically

    Will check for an explicit input timestamp first, then check PlotTargetSettings, then the series
    metadata, and if both are None, will take the first series entry as start timestamp.
    If the series is also empty, None is returned.
    """
    if timestamp is not None:
        return _to_datetime(timestamp)

    plot_target_settings = get_plot_target_settings()

    timestamp = plot_target_settings.datetime_x_axes_range_start
    key = "ref_interval_start_timestamp"  # TODO: DataClass mit Attributen start_timestamp, end_timestamp, noch was?

    if timestamp is None:
        try:
            timestamp = series.attrs.get("single_metric_dataset_metadata", {})[key]
        except KeyError as exc:
            msg = f"""Expected key structure not found:
             attrs["single_metric_dataset_metadata"]["{key}"]"""
            logger.warning(msg=msg, exc_info=exc)
            if len(series) > 0:
                timestamp = series.index[0]

    return _to_datetime(timestamp)


def _get_end_timestamp(series: pd.Series, timestamp: str | None) -> pd.Timestamp | None:
    """Get the end timestamp hierarchically

    Will check for an explicit input timestamp first, then check PlotTargetSettings, then the series
    metadata, and if both are None, will take the last series entry as end timestamp.
    If the series is also empty, None is returned.
    """
    if timestamp is not None:
        return _to_datetime(timestamp)

    plot_target_settings = get_plot_target_settings()

    timestamp = plot_target_settings.datetime_x_axes_range_end
    key = "ref_interval_end_timestamp"

    if timestamp is None:
        try:
            timestamp = series.attrs.get("single_metric_dataset_metadata", {})[key]
        except KeyError as exc:
            msg = f"""Expected key structure not found:
             attrs["single_metric_dataset_metadata"]["{key}"]"""
            logger.warning(msg=msg, exc_info=exc)
            if len(series) > 0:
                timestamp = series.index[-1]

    return _to_datetime(timestamp)


def _to_datetime(timestamp: str | int | None) -> pd.Timestamp | None:
    """Turn datetime string or integer into a pandas timestamp

    Integer values are interpreted as epoch in seconds.
    String values are accepted in any format compatible with pd.to_datetime
    and interpreted in seconds.
    The timezone is set to utc in both cases, other timezones can be set via modify_timezone."""
    if isinstance(timestamp, int):
        timestamp = pd.to_datetime(timestamp, unit="s", utc=True)
    elif isinstance(timestamp, str):
        timestamp = pd.to_datetime(timestamp, utc=True)
    else:
        raise HelperException("Unexpected timestamp type, please use str or int!")
    return timestamp


def modify_timezone(
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
            new_object[column_name] = pd.to_datetime(new_object[column_name]).tz_convert(
                to_timezone
            )
            column_names.append(column_name)

        if column_names is None:
            if isinstance(new_object, pd.Series):
                new_object.index = pd.to_datetime(new_object.index).tz_convert(to_timezone)
                msg = f"Converted index to datetime starting with {object_to_convert.index[0]}"
                logger.debug(msg=msg)
            elif isinstance(new_object, pd.DataFrame) and "timestamp" in new_object.columns:
                new_object["timestamp"] = pd.to_datetime(new_object["timestamp"]).tz_convert(
                    to_timezone
                )
                msg = f"""Converted column "timestamp" to datetime starting with
                {object_to_convert["timestamp"][0]}"""
                logger.debug(msg=msg)
        if column_names is not None and len(column_names) > 0:
            for column in column_names:
                new_object[column] = pd.to_datetime(new_object[column]).tz_convert(to_timezone)

        if isinstance(object_to_convert, pd.Series):
            new_object = pd.Series(
                new_object[object_to_convert.name],
                index=new_object.index,
                name=object_to_convert.name,
            )

        return new_object

    # TODO: Exceptions gründlich unit-testen
    except pytz.exceptions.UnknownTimeZoneError as exc:
        possible_timezone = pytz.all_timezones
        raise ValueError(f"""Timezone not known, please choose from {possible_timezone}""") from exc
    except (TypeError, AttributeError) as exc:
        raise TypeError("Entries to convert do not contain valid timestamps") from exc

    except KeyError as exc:
        exc.add_note(f"Column name {column_name} not in object_to_convert")
        raise

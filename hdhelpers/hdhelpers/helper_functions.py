import logging
from datetime import datetime
from typing import Any

import pandas as pd
from pandas.tseries.frequencies import to_offset

from hdhelpers.exceptions import HelperException
from hdhelpers.plot_target_settings import get_plot_target_settings

logger = logging.getLogger(__name__)


def _convert_to_optional_timezone(object_to_convert: Any, to_timezone: str | None) -> Any:
    """Convert object_to_convert to to_timezone if not None,
    or to its own timezone if aware
    or to UTC otherwise"""
    if to_timezone is None:
        if object_to_convert.tz is None:
            return object_to_convert.tz_localize("UTC")
        return object_to_convert
    if object_to_convert.tz is None:
        return object_to_convert.tz_localize(to_timezone)
    return object_to_convert.tz_convert(to_timezone)


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
        if not isinstance(title, str):
            raise HelperException("Expected short_display_name to be a string, but it is not!")
    except (KeyError, HelperException) as exc:
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
        if not isinstance(unit, str):
            raise HelperException("Expected unit to be a string, but it is not!")
    except (KeyError, HelperException) as exc:
        msg = 'Expected attrs["single_metric_metadata"]["structured_metadata"]["metric"]["unit"'
        "] but got incorrect keys"
        logger.warning(msg=msg, exc_info=exc)
        unit = default_unit
    return unit


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
            f"{padding} as padding value is an invalid frequency. "
            "Use something compatible with pandas.tseries.frequencies.to_offset()"
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
            f"{padding} as padding value is an invalid frequency. "
            "Use something compatible with pandas.tseries.frequencies.to_offset()"
        ) from exc


def _get_start_timestamp(
    series: pd.Series, timestamp: datetime | str | None
) -> pd.Timestamp | None:
    """Get the start timestamp  hierarchically

    Will check for an explicit input timestamp first, then check PlotTargetSettings, then the series
    metadata, and if both are None, will take the first series entry as start timestamp.
    If the series is also empty, None is returned.
    """
    if timestamp is not None:
        return _to_datetime(timestamp)

    plot_target_settings = get_plot_target_settings()

    timestamp = plot_target_settings.datetime_x_axes_range_start

    if timestamp is None:
        key = "ref_interval_start_timestamp"
        try:
            timestamp = series.attrs.get("single_metric_dataset_metadata", {})[key]
        except KeyError as exc:
            msg = f"""Expected key structure not found:
             attrs["single_metric_dataset_metadata"]["{key}"]"""
            logger.warning(msg=msg, exc_info=exc)
            if len(series) > 0:
                timestamp = series.index[0]

    return _to_datetime(timestamp)


def _get_end_timestamp(series: pd.Series, timestamp: datetime | str | None) -> pd.Timestamp | None:
    """Get the end timestamp hierarchically

    Will check for an explicit input timestamp first, then check PlotTargetSettings, then the series
    metadata, and if both are None, will take the last series entry as end timestamp.
    If the series is also empty, None is returned.
    """
    if timestamp is not None:
        return _to_datetime(timestamp)

    plot_target_settings = get_plot_target_settings()

    timestamp = plot_target_settings.datetime_x_axes_range_end

    if timestamp is None:
        key = "ref_interval_end_timestamp"
        try:
            timestamp = series.attrs.get("single_metric_dataset_metadata", {})[key]
        except KeyError as exc:
            msg = f"""Expected key structure not found:
             attrs["single_metric_dataset_metadata"]["{key}"]"""
            logger.warning(msg=msg, exc_info=exc)
            if len(series) > 0:
                timestamp = series.index[-1]

    return _to_datetime(timestamp)


def _to_datetime(timestamp: datetime | str | int | None) -> pd.Timestamp | None:
    """Turn datetime string or integer into a pandas timestamp

    Integer values are interpreted as epoch in seconds.
    String values are accepted in any format compatible with pd.to_datetime
    and interpreted in seconds.
    The timezone is set to utc in both cases, other timezones can be set via modify_timezone."""
    if timestamp is None:
        return None
    if isinstance(timestamp, int):
        timestamp = pd.to_datetime(timestamp, unit="s", utc=True)
    elif isinstance(timestamp, str | datetime):
        timestamp = pd.to_datetime(timestamp, utc=True)
    else:
        raise HelperException("Unexpected timestamp type, please use str or int!")
    return timestamp

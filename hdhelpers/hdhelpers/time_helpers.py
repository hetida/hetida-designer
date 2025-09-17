import logging
from datetime import datetime
from functools import singledispatch
from warnings import warn

import pandas as pd
import pytz

from hdhelpers.exceptions import HelperException
from hdhelpers.plot_target_settings import get_plot_target_settings

logger = logging.getLogger(__name__)


def _to_pd_timestamp(timestamp: datetime | str | int | None) -> pd.Timestamp | None:
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


def _get_start_timestamp(
    series: pd.Series, timestamp: datetime | str | None
) -> pd.Timestamp | None:
    """Get the start timestamp hierarchically

    Will check for an explicit input timestamp first, then check PlotTargetSettings, then the series
     metadata, and if both are None or not present, will take the first series entry as start
     timestamp. If the series is also empty, None is returned.
    """
    if timestamp is not None:
        return _to_pd_timestamp(timestamp)

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
                try:
                    timestamp = _to_pd_timestamp(timestamp)
                    return timestamp
                except HelperException:
                    return None

    return _to_pd_timestamp(timestamp)


def _get_end_timestamp(series: pd.Series, timestamp: datetime | str | None) -> pd.Timestamp | None:
    """Get the end timestamp hierarchically

    Will check for an explicit input timestamp first, then check PlotTargetSettings, then the series
    metadata, and if both are None or not present, will take the last series entry as end timestamp.
    If the series is also empty, None is returned.
    """
    if timestamp is not None:
        return _to_pd_timestamp(timestamp)

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
                try:
                    timestamp = _to_pd_timestamp(timestamp)
                    return timestamp
                except HelperException:
                    return None

    return _to_pd_timestamp(timestamp)


@singledispatch
def _convert_to_optional_timezone(object_to_convert, to_timezone: str | None):
    """Convert object_to_convert to to_timezone if not None,
    or to its own timezone if aware
    or to UTC otherwise"""
    raise NotImplementedError(
        f"Not implemented for object_to_convert of type {type(object_to_convert).__name__}"
    )


@_convert_to_optional_timezone.register(pd.Timestamp | pd.DatetimeIndex)
def _[T: (pd.Timestamp, pd.DatetimeIndex)](object_to_convert: T, to_timezone: str | None) -> T:
    if to_timezone is None:
        if object_to_convert.tz is None:
            return object_to_convert.tz_localize("UTC")
        return object_to_convert
    if object_to_convert.tz is None:
        return object_to_convert.tz_localize(to_timezone)
    return object_to_convert.tz_convert(to_timezone)


@_convert_to_optional_timezone.register
def _(object_to_convert: pd.Series, to_timezone: str | None) -> pd.Series:
    if to_timezone is None:
        if object_to_convert.dt.tz is None:
            return object_to_convert.dt.tz_localize("UTC")
        return object_to_convert
    if object_to_convert.dt.tz is None:
        return object_to_convert.dt.tz_localize(to_timezone)
    return object_to_convert.dt.tz_convert(to_timezone)


def modify_timezone[T: (pd.Timestamp, pd.Series, pd.DataFrame)](  # noqa: PLR0912
    object_to_convert: T,
    to_timezone: str | None = None,
    column_name: str | None = None,
    column_names: list[str] | None = None,
    convert_index: bool = True,
) -> T:
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
        if to_timezone is None:
            plot_target_settings = get_plot_target_settings()
            if plot_target_settings.plot_target_timezone is not None:
                to_timezone = plot_target_settings.plot_target_timezone

        if isinstance(object_to_convert, pd.Timestamp):
            return _convert_to_optional_timezone(object_to_convert, to_timezone)

        if isinstance(object_to_convert, pd.Series):
            new_object = object_to_convert.to_frame(name=object_to_convert.name)
        else:
            new_object = object_to_convert.copy(deep=True)

        # Both column_name branches exist purely for backwards compatibility,
        # only convert_index should stay.
        if column_name is None and convert_index:
            new_object.index = _convert_to_optional_timezone(
                pd.to_datetime(new_object.index), to_timezone
            )
        if column_name is not None:
            warn(
                """The parameter 'column_name' will soon be deprecated in favor of
                the more flexible 'columns_names'""",
                DeprecationWarning,
                stacklevel=2,
            )
            new_object[column_name] = _convert_to_optional_timezone(
                pd.to_datetime(new_object[column_name]), to_timezone
            )
            column_names.append(column_name)

        if len(column_names) == 0:
            if isinstance(object_to_convert, pd.Series):
                new_object.index = _convert_to_optional_timezone(
                    pd.to_datetime(new_object.index), to_timezone
                )
                msg = f"Converted index to datetime starting with {object_to_convert.index[0]}"
                logger.debug(msg=msg)
            elif isinstance(new_object, pd.DataFrame) and "timestamp" in new_object.columns:
                new_object["timestamp"] = _convert_to_optional_timezone(
                    pd.to_datetime(new_object["timestamp"]), to_timezone
                )
                msg = f"""Converted column "timestamp" to datetime starting with
                {object_to_convert["timestamp"][0]}"""
                logger.debug(msg=msg)
        if len(column_names) > 0:
            for column in column_names:
                new_object[column] = _convert_to_optional_timezone(
                    pd.to_datetime(new_object[column]), to_timezone
                )

        if not isinstance(object_to_convert, pd.Series):
            new_object.attrs = object_to_convert.attrs
            return new_object

        series_object = pd.Series(
            new_object[object_to_convert.name],
            index=new_object.index,
            name=object_to_convert.name,
        )
        series_object.attrs = object_to_convert.attrs

        return series_object

    except pytz.exceptions.UnknownTimeZoneError as exc:
        possible_timezone = pytz.all_timezones
        raise ValueError(f"""Timezone not known, please choose from {possible_timezone}""") from exc
    except (AttributeError, pytz.exceptions.NonExistentTimeError) as exc:
        raise TypeError("Entries to convert do not contain valid timestamps") from exc
    except KeyError as exc:
        exc.add_note(f"Column name {column_name} not in object_to_convert")
        raise

import logging

import pandas as pd

from hdhelpers.plot_target_settings import get_plot_target_settings

logger = logging.getLogger(__name__)


def get_colors_from_plot_target_settings() -> dict[str, str | list[str]]:
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


def get_locale_from_plot_target_settings() -> str:
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
    except (AttributeError, KeyError):
        logger.exception(
            'Expected attrs["single_metric_metadata"]["structured_metadata"]["metric"]["unit"] '
            "but got incorrect keys"
        )
        title = default_title
    return title


def _get_unit(series: pd.Series, default_unit: str = "") -> str:
    """Get unit for y-axis label from metadata

    Tries to get the unit from the standard metadata of the hetida .platform.
    If such metadata doesn't exist, the default_unit is returned instead.
    """
    try:
        unit = series.attrs["single_metric_metadata"]["structured_metadata"]["metric"]["unit"]
    except (AttributeError, KeyError):
        logger.exception(
            'Expected attrs["single_metric_metadata"]["structured_metadata"]["metric"]["unit"] '
            "but got incorrect keys"
        )
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


def get_period(
    series: pd.Series,
    timezone: str | None = None,
    start: str | None = None,
    start_padding: str | None = None,
    end: str | None = None,
    end_padding: str | None = None,
) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Get time period displayed on the x-axis

    TODO: The finalized functionality should be described here.
    """
    plot_target_settings = get_plot_target_settings()

    # Get start # TODO: Auslagern in Funktion
    if start is None:
        start = plot_target_settings.datetime_x_axes_range_start

    if start is None:
        try:
            start = series.attrs["single_metric_dataset_metadata"]["ref_interval_start_timestamp"]
        except (AttributeError, KeyError):
            logger.exception(
                'Expected attrs["single_metric_dataset_metadata"]["ref_interval_start_timestamp"] '
                "but got incorrect keys"  # TODO: %s String-Zeugs nachschauen (lazy formatting)
            )
            if len(series) > 0:
                start = series.iloc[0].index

    # Get end
    if end is None:
        end = plot_target_settings.datetime_x_axes_range_end

    if end is None:
        try:
            end = series.attrs["single_metric_dataset_metadata"]["ref_interval_end_timestamp"]
        except (AttributeError, KeyError):
            logger.exception(
                'Expected attrs["single_metric_dataset_metadata"]["ref_interval_end_timestamp"] '
                "but got incorrect keys"
            )
            if len(series) > 0:
                end = series.iloc[0].index

    # Convert timezone
    # TODO: Frequenz aus Metadaten und n ticks statt Zeitintervall padden
    start = convert_timezone(start, timezone)
    end = convert_timezone(end, timezone)

    # Optionally add padding
    # TODO: Timedelta is only <= W, what to do for month, year, ...? Parse for DateOffset?
    start = start - pd.Timedelta(start_padding)
    end = end + pd.Timedelta(end_padding)

    return start, end


def convert_timezone(date: int | str, timezone: str | None = None):
    # TODO: This should probably be absorbed by modify_timezone
    if timezone is None:
        plot_target_settings = get_plot_target_settings()
        # TODO: timezone = None problematisch? Unit Test!
        timezone = plot_target_settings.plot_target_timezone

    if isinstance(date, int):
        # It's usually "seconds till newyears 1970", but the default unit is ns.
        date = pd.to_datetime(date, unit="s", utc=True).tz_convert(timezone)
    else:
        # String Timestamps can be converted with ns precision without issues
        date = pd.to_datetime(date, utc=True).tz_convert(timezone)


def modify_timezone() -> None:
    """Modifies timestamps to a certain timezone

    TODO: modify_timezone is the last function to be overhauled; this is a placeholder
    """
    # TODO: Kein pytz verwenden!

import pandas as pd

from hdhelpers.helper_functions_for_component_code import (
    _get_display_name,
    _get_unit,
    get_colors_from_plot_target_settings,
    get_locale_from_plot_target_settings,
    get_period,
    get_title_with_unit,
    modify_timezone,
)


def test_get_display_name_default():
    series = pd.Series()
    assert _get_display_name(series=series, default_title="default_name") == "default_name"


def test_get_display_name_metadata():
    series = pd.Series()
    series.attrs["single_metric_metadata"]["structured_metadata"]["metric"][
        "short_display_name"
    ] = "name_from_metadata"
    assert _get_display_name(series=series) == "name_from_metadata"


def test_get_unit_default():
    series = pd.Series()
    assert _get_unit(series=series, default_unit="default_unit") == "default_unit"


def test_get_unit_metadata():
    series = pd.Series()
    series.attrs["single_metric_metadata"]["structured_metadata"]["metric"]["unit"] = (
        "unit_from_metadata"
    )
    assert _get_unit(series=series) == "unit_from_metadata"


def test_get_title_with_unit_default():
    series = pd.Series()
    assert (
        get_title_with_unit(
            series=series, default_title="default_name", default_unit="default_unit"
        )
        == "default_name [default_unit]"
    )


def test_get_title_with_unit_metadata():
    series = pd.Series()
    series.attrs["single_metric_metadata"]["structured_metadata"]["metric"][
        "short_display_name"
    ] = "name_from_metadata"
    series.attrs["single_metric_metadata"]["structured_metadata"]["metric"]["unit"] = (
        "unit_from_metadata"
    )
    assert get_title_with_unit(series=series) == "name_from_metadata [unit_from_metadata]"


def test_get_colors_from_plot_target_settings():
    color_dict = get_colors_from_plot_target_settings()
    color_names = [
        "axes_label_color",
        "background_color",
        "error_color",
        "grid_color",
        "info_color",
        "line_colors",
        "success_color",
        "warn_color",
    ]
    assert isinstance(color_dict, dict)
    assert len(color_dict) >= len(color_names)
    assert all(color in color_dict for color in color_names)


def test_get_locale_from_plot_target_settings():
    locale = get_locale_from_plot_target_settings()
    assert isinstance(locale, str)
    assert len(locale) > 0


def test_get_period():
    # TODO: Write proper tests when get_period is done.
    start, end = get_period(pd.Series(), "Europe/Berlin")
    assert isinstance(start, pd.Timestamp)
    assert isinstance(end, pd.Timestamp)
    assert end >= start


def test_modify_timezone():
    # TODO: modify_timezone is the last function to be overhauled; this is a placeholder
    converted_object = modify_timezone()
    assert converted_object is None

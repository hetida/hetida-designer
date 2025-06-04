import sys
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from pytz import UnknownTimeZoneError

from hdhelpers.exceptions import HelperException
from hdhelpers.helper_functions_for_component_code import (
    _convert_timezone,
    _get_display_name,
    _get_start_or_end_timestamp,
    _get_unit,
    _pad_start_or_end,
    _to_datetime,
    get_and_pad_start_and_end_timestamp,
    get_colors_from_plot_target_settings,
    get_locale_from_plot_target_settings,
    get_title_with_unit,
    modify_timezone,
)
from hdhelpers.plot_target_settings import StatusColors


@pytest.fixture
def setup_plot_target_settings():
    from hdhelpers.plot_target_settings import PlotTargetSettings

    # Mock the import of context and get_runtime_exec_context()
    runtime_execution_context_var = MagicMock()

    def insert_kwargs_into_plot_target_settings(**kwargs):
        runtime_execution_context_var.plot_target_settings = PlotTargetSettings(**kwargs)
        return runtime_execution_context_var

    hetdesrun_runtime_context = MagicMock()
    hetdesrun_runtime_context.get_runtime_exec_context = MagicMock(
        return_value=runtime_execution_context_var
    )
    with patch.dict(sys.modules, {"hetdesrun.runtime.context": hetdesrun_runtime_context}):
        yield insert_kwargs_into_plot_target_settings


def test_get_display_name_default():
    series = pd.Series()
    assert _get_display_name(series=series, default_title="default_name") == "default_name"


def test_get_display_name_metadata():
    series = pd.Series()
    series.attrs["single_metric_metadata"] = {
        "structured_metadata": {"metric": {"short_display_name": "name_from_metadata"}}
    }
    assert _get_display_name(series=series) == "name_from_metadata"


def test_get_unit_default():
    series = pd.Series()
    assert _get_unit(series=series, default_unit="default_unit") == "default_unit"


def test_get_unit_metadata():
    series = pd.Series()
    series.attrs["single_metric_metadata"] = {
        "structured_metadata": {"metric": {"unit": "unit_from_metadata"}}
    }
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
    series.attrs["single_metric_metadata"] = {
        "structured_metadata": {"metric": {"short_display_name": "name_from_metadata"}}
    }
    series.attrs["single_metric_metadata"]["structured_metadata"]["metric"]["unit"] = (
        "unit_from_metadata"
    )
    assert get_title_with_unit(series=series) == "name_from_metadata [unit_from_metadata]"


@pytest.mark.parametrize(
    "kwargs",
    [
        ({}),
        ({"axes_label_color": "#000000"}),
        (
            {
                "axes_label_color": "#000000",
                "background_color": "#FFFFFF",
                "grid_color": "#8C8C98",
                "line_colors": ["#2FAE53", "#EB7C45", "#89CE6E", "#FFB058"],
                "status_colors": StatusColors(
                    success_color="#2FAE53",
                    error_color="#EB6962",
                    warn_color="#9CE6E",
                    info_color="#80B0EC",
                ),
            }
        ),
    ],
)
def test_get_colors_from_plot_target_settings(setup_plot_target_settings, kwargs):
    setup_plot_target_settings(**kwargs)
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


@pytest.mark.parametrize(
    "mock_locale",
    [(None), (""), ("de")],
)
def test_get_locale_from_plot_target_settings(setup_plot_target_settings, mock_locale):
    setup_plot_target_settings(plot_target_locale=mock_locale)
    locale = get_locale_from_plot_target_settings()
    assert isinstance(locale, str | None)


@pytest.mark.parametrize(
    ("start", "end", "start_padding", "end_padding"),
    [
        ("2025-05-19T09:00:00+02:00", "2025-05-19T18:00:00+02:00", "1s", "1s"),
        ("2025-05-19T09:00:00+02:00", "2025-05-19T18:00:00+02:00", "1min", "1min"),
        ("2025-05-19T09:00:00+02:00", "2025-05-19T18:00:00+02:00", "1h", "1h"),
        ("2025-05-19T09:00:00+02:00", "2025-05-19T18:00:00+02:00", "1d", "1d"),
        ("2025-05-19T09:00:00+02:00", "2025-05-19T18:00:00+02:00", "1W", "1W"),
        ("2025-05-19T09:00:00+02:00", "2025-05-19T18:00:00+02:00", "1ME", "1ME"),
        ("2025-05-19T09:00:00+02:00", "2025-05-19T18:00:00+02:00", "1YE", "1YE"),
    ],
)
def test_get_and_pad_start_and_end_timestamp(start, end, start_padding, end_padding):
    start, end = get_and_pad_start_and_end_timestamp(
        pd.Series(), "Europe/Berlin", start, start_padding, end, end_padding
    )
    assert isinstance(start, pd.Timestamp)
    assert isinstance(end, pd.Timestamp)
    assert end >= start


def test_get_and_pad_none():
    start, end = get_and_pad_start_and_end_timestamp(pd.Series())
    assert start is None
    assert end is None


@pytest.mark.parametrize(
    ("series", "attrs", "timestamp", "is_start", "kwargs"),
    [
        (pd.Series(), None, "2025-05-28T09:00:00+02:00", True, {}),  # given explicit timestamp
        (
            pd.Series(),
            None,
            None,
            True,
            {"datetime_x_axes_range_start": "2025-05-28T09:00:00+02:00"},
        ),  # start in PlotTargetSettings
        (
            pd.Series(),
            None,
            None,
            False,
            {"datetime_x_axes_range_end": "2025-05-28T18:00:00+02:00"},
        ),  # end in PlotTargetSettings
        (
            pd.Series(),
            {
                "single_metric_dataset_metadata": {
                    "ref_interval_start_timestamp": "2025-05-28T09:00:00+02:00"
                }
            },
            None,
            True,
            {},
        ),  # start in metadata
        (
            pd.Series(),
            {
                "single_metric_dataset_metadata": {
                    "ref_interval_end_timestamp": "2025-05-28T18:00:00+02:00"
                }
            },
            None,
            False,
            {},
        ),  # end in metadata
        (
            pd.Series({"2025-05-28T09:00:00+02:00": 1, "2025-05-28T18:00:00+02:00": 2}),
            None,
            None,
            True,
            {},
        ),  # start is first value
        (
            pd.Series({"2025-05-28T09:00:00+02:00": 1, "2025-05-28T18:00:00+02:00": 2}),
            None,
            None,
            False,
            {},
        ),  # end is last value
    ],
)
def test_get_start_or_end_timestamp(
    setup_plot_target_settings, series, attrs, timestamp, is_start, kwargs
):
    setup_plot_target_settings(**kwargs)
    if attrs is not None:
        series.attrs = attrs
    timestamp = _get_start_or_end_timestamp(series, timestamp, is_start)
    assert isinstance(timestamp, pd.Timestamp | None)


def test_get_start_or_end_none():
    timestamp = _get_start_or_end_timestamp(pd.Series(), None)
    assert timestamp is None


def test_pad_start():
    start = pd.to_datetime("2025-05-28T09:00:00+02:00")
    padded_start = _pad_start_or_end(start, "1h")
    assert isinstance(padded_start, pd.Timestamp)
    assert padded_start < start


def test_pad_end():
    end = pd.to_datetime("2025-05-28T18:00:00+02:00")
    padded_end = _pad_start_or_end(end, "1h", False)
    assert isinstance(padded_end, pd.Timestamp)
    assert padded_end > end


def test_pad_start_or_end_wrong_padding():
    timestamp = pd.to_datetime("2025-05-28T09:00:00+02:00")
    with pytest.raises(HelperException):
        _pad_start_or_end(timestamp, "foo")


@pytest.mark.parametrize(
    ("timezone", "kwargs"),
    [("Europe/Berlin", {}), (None, {}), (None, {"plot_target_timezone": "Europe/Berlin"})],
)
def test_convert_timezone(setup_plot_target_settings, timezone, kwargs):
    setup_plot_target_settings(**kwargs)
    timestamp = _convert_timezone("2025-05-28T09:00:00+02:00", timezone)
    assert isinstance(timestamp, pd.Timestamp)


def test_convert_incorrect_timezone(setup_plot_target_settings):
    setup_plot_target_settings(plot_target_timezone="Eurolin")
    with pytest.raises(UnknownTimeZoneError):
        _convert_timezone("2025-05-28T09:00:00+02:00")


@pytest.mark.parametrize(("timestamp"), [("2025-05-28T09:00:00+02:00"), (1748415600)])
def test_to_datetime(timestamp):
    timestamp = _to_datetime(timestamp)
    assert isinstance(timestamp, pd.Timestamp)


def test_modify_timezone():
    # TODO: modify_timezone is the last function to be overhauled; this is a placeholder
    converted_object = modify_timezone()
    assert converted_object is None

from unittest.mock import MagicMock, patch

import pandas as pd
import plotly.graph_objects as go
import pytest

from hdhelpers.exceptions import HelperException
from hdhelpers.plot_helpers import (
    _get_metric_metadate,
    _pad_end,
    _pad_start,
    get_and_pad_start_and_end_timestamp,
    get_colors_from_plot_target_settings,
    get_locale_from_plot_target_settings,
    get_y_axis_label,
    plotly_fig_to_json_dict,
)
from hdhelpers.plot_target_settings import (
    PlotTargetSettings,
    PlotTargetStyle,
    StatusColors,
)


def test_get_metric_metadate_default():
    series = pd.Series()
    assert _get_metric_metadate(series, "unit", "default") == "default"


def test_get_metric_metadate_metadata():
    series = pd.Series()
    series.attrs["single_metric_metadata"] = {
        "structured_metadata": {"metric": {"unit": "unit_from_metadata"}}
    }
    assert _get_metric_metadate(series, "unit") == "unit_from_metadata"


def test_pad_start():
    start = pd.to_datetime("2025-05-28T09:00:00+02:00")
    padded_start = _pad_start(start, "1h")
    assert isinstance(padded_start, pd.Timestamp)
    assert padded_start < start


def test_pad_end():
    end = pd.to_datetime("2025-05-28T18:00:00+02:00")
    padded_end = _pad_end(end, "1h")
    assert isinstance(padded_end, pd.Timestamp)
    assert padded_end > end


def test_pad_start_wrong_padding():
    timestamp = pd.to_datetime("2025-05-28T09:00:00+02:00")
    with pytest.raises(HelperException):
        _pad_start(timestamp, "foo")


def test_pad_end_wrong_padding():
    timestamp = pd.to_datetime("2025-05-28T09:00:00+02:00")
    with pytest.raises(HelperException):
        _pad_end(timestamp, "foo")


def test_get_y_axis_label_default():
    series = pd.Series()
    assert (
        get_y_axis_label(series=series, default_title="default_name", default_unit="default_unit")
        == "default_name [default_unit]"
    )


def test_get_y_axis_labeltitle_with_unit_metadata():
    series = pd.Series()
    series.attrs["single_metric_metadata"] = {
        "structured_metadata": {"metric": {"short_display_name": "name_from_metadata"}}
    }
    series.attrs["single_metric_metadata"]["structured_metadata"]["metric"]["unit"] = (
        "unit_from_metadata"
    )
    assert get_y_axis_label(series=series) == "name_from_metadata [unit_from_metadata]"


def test_get_no_colors_from_plot_target_settings():
    plot_target_settings_mock = MagicMock(return_value=PlotTargetSettings())
    with patch("hdhelpers.plot_helpers.get_plot_target_settings", plot_target_settings_mock):
        style_object = get_colors_from_plot_target_settings()
        assert isinstance(style_object, PlotTargetStyle)


def test_get_one_color_from_plot_target_settings():
    plot_target_settings_mock = MagicMock(
        return_value=PlotTargetSettings(
            plot_target_style=PlotTargetStyle(
                axes_label_color="#000000",
            )
        )
    )
    with patch("hdhelpers.plot_helpers.get_plot_target_settings", plot_target_settings_mock):
        style_object = get_colors_from_plot_target_settings()
        assert isinstance(style_object, PlotTargetStyle)


def test_get_all_colors_from_plot_target_settings():
    plot_target_settings_mock = MagicMock(
        return_value=PlotTargetSettings(
            plot_target_style=PlotTargetStyle(
                axes_label_color="#000000",
                background_color="#FFFFFF",
                grid_color="#8C8C98",
                line_colors=["#2FAE53", "#EB7C45", "#89CE6E", "#FFB058"],
                status_colors=StatusColors(
                    success_color="#2FAE53",
                    error_color="#EB6962",
                    warn_color="#9CE6E",
                    info_color="#80B0EC",
                ),
            )
        )
    )
    with patch("hdhelpers.plot_helpers.get_plot_target_settings", plot_target_settings_mock):
        style_object = get_colors_from_plot_target_settings()
        assert isinstance(style_object, PlotTargetStyle)


def test_get_no_locale_from_plot_target_settings():
    plot_target_settings_mock = MagicMock(return_value=PlotTargetSettings(plot_target_locale=None))
    with patch("hdhelpers.plot_helpers.get_plot_target_settings", plot_target_settings_mock):
        locale = get_locale_from_plot_target_settings()
        assert isinstance(locale, str | None)


def test_get_empty_locale_from_plot_target_settings():
    plot_target_settings_mock = MagicMock(return_value=PlotTargetSettings(plot_target_locale=""))
    with patch("hdhelpers.plot_helpers.get_plot_target_settings", plot_target_settings_mock):
        locale = get_locale_from_plot_target_settings()
        assert isinstance(locale, str | None)


def test_get_german_locale_from_plot_target_settings():
    plot_target_settings_mock = MagicMock(return_value=PlotTargetSettings(plot_target_locale="de"))
    with patch("hdhelpers.plot_helpers.get_plot_target_settings", plot_target_settings_mock):
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
    with pytest.raises(HelperException):
        start, end = get_and_pad_start_and_end_timestamp(pd.Series())


def test_plotly_fig_to_json_dict_defaults():
    plotly_fig = go.Figure()
    plotly_fig.add_trace(
        go.Scatter(
            x=[1, 2, 3],
            y=[9, 8, 7],
            name="Foo",
        )
    )
    json_dict = plotly_fig_to_json_dict(plotly_fig)
    assert len(json_dict.get("layout", {}).get("template", {}).get("layout", {})["colorway"]) > 0
    assert json_dict.get("layout", {}).get("margin", {})["autoexpand"]
    assert json_dict.get("layout", {}).get("margin", {})["l"] == 0
    assert json_dict.get("layout", {}).get("margin", {})["r"] == 0
    assert json_dict.get("layout", {}).get("margin", {})["b"] == 0
    assert json_dict.get("layout", {}).get("margin", {})["t"] == 0
    assert json_dict.get("layout", {}).get("margin", {})["pad"] == 0
    assert not json_dict.get("config", {})["displaylogo"]
    assert not json_dict.get("config", {})["displayModeBar"]


def test_plotly_fig_to_json_dict_set_everything():
    plotly_fig = go.Figure()
    plotly_fig.add_trace(
        go.Scatter(
            x=[1, 2, 3],
            y=[9, 8, 7],
            name="Foo",
        )
    )
    json_dict = plotly_fig_to_json_dict(
        fig=plotly_fig,
        add_config_settings=False,
        hide_legend=True,
        hide_x_title=True,
        remove_plotly_bar=False,
        remove_plotly_icon=False,
        update_x_axes_tickformat=True,
        use_default_standoff=True,
        use_minimum_margin=False,
        use_muplot_axes_color=True,
        use_muplot_grid=True,
        use_muplot_line_and_markers=True,
        use_platform_background=True,
        use_platform_defaults=True,
        use_simple_white_template=False,
    )
    assert isinstance(json_dict, dict)

    assert len(json_dict.get("layout", {}).get("template", {}).get("layout", {})["colorway"]) > 0
    assert json_dict.get("layout", {}).get("margin", {}) == {}
    assert "displaylogo" not in json_dict.get("config", {})
    assert "displayModeBar" not in json_dict.get("config", {})

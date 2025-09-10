import datetime
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pytest

from hdhelpers.exceptions import HelperException
from hdhelpers.plot_target_settings import (
    PlotTargetSettings,
    PlotTargetStyle,
    StatusColors,
)
from hdhelpers.user_functions import (
    get_and_pad_start_and_end_timestamp,
    get_colors_from_plot_target_settings,
    get_locale_from_plot_target_settings,
    get_y_axis_label,
    modify_timezone,
    plotly_fig_to_json_dict,
)


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
    with patch("hdhelpers.user_functions.get_plot_target_settings", plot_target_settings_mock):
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
    with patch("hdhelpers.user_functions.get_plot_target_settings", plot_target_settings_mock):
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
    with patch("hdhelpers.user_functions.get_plot_target_settings", plot_target_settings_mock):
        style_object = get_colors_from_plot_target_settings()
        assert isinstance(style_object, PlotTargetStyle)


def test_get_no_locale_from_plot_target_settings():
    plot_target_settings_mock = MagicMock(return_value=PlotTargetSettings(plot_target_locale=None))
    with patch("hdhelpers.user_functions.get_plot_target_settings", plot_target_settings_mock):
        locale = get_locale_from_plot_target_settings()
        assert isinstance(locale, str | None)


def test_get_empty_locale_from_plot_target_settings():
    plot_target_settings_mock = MagicMock(return_value=PlotTargetSettings(plot_target_locale=""))
    with patch("hdhelpers.user_functions.get_plot_target_settings", plot_target_settings_mock):
        locale = get_locale_from_plot_target_settings()
        assert isinstance(locale, str | None)


def test_get_german_locale_from_plot_target_settings():
    plot_target_settings_mock = MagicMock(return_value=PlotTargetSettings(plot_target_locale="de"))
    with patch("hdhelpers.user_functions.get_plot_target_settings", plot_target_settings_mock):
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


@pytest.fixture()
def series_winter() -> pd.Series:
    winter = pd.Series(
        [0, 1, 2, 3],
        index=pd.to_datetime(
            ["2023-10-29 00:00", "2023-10-29 01:00", "2023-10-29 02:00", "2023-10-29 03:00"],
            format="%Y-%m-%d %H:%M",
            utc=True,
        ),
    )
    winter.attrs["foo"] = "bar"

    return winter


@pytest.fixture()
def series_summer() -> pd.Series:
    summer = pd.Series(
        [0, 1, 2, 3],
        index=pd.to_datetime(
            ["2023-03-25 23:00", "2023-03-26 00:00", "2023-03-26 01:00", "2023-03-26 02:00"],
            format="%Y-%m-%d %H:%M",
            utc=True,
        ),
    )
    summer.attrs["foo"] = "bar"
    return summer


@pytest.fixture()
def dataframe() -> pd.DataFrame:
    values = [1.0, 1.2, 1.2]
    timestamps = pd.to_datetime(
        [
            "2019-08-01T15:45:36.000Z",
            "2019-08-02T11:33:41.000Z",
            "2019-08-03T11:57:41.000Z",
        ],
        format="%Y-%m-%dT%H:%M:%S.%fZ",
    ).tz_localize("UTC")

    ts_df = pd.DataFrame({"timestamp": timestamps, "value": values})
    ts_df.attrs["foo"] = "bar"

    return ts_df


@pytest.fixture()
def multicolumn_frame() -> pd.DataFrame:
    values = [1.0, 1.2, 1.2]
    index = pd.to_datetime(
        [
            "2021-08-01T15:45:36.000Z",
            "2021-08-02T11:33:41.000Z",
            "2021-08-03T11:57:41.000Z",
        ],
        format="%Y-%m-%dT%H:%M:%S.%fZ",
    ).tz_localize("UTC")
    more_timestamps = pd.to_datetime(
        [
            "2020-08-01T15:45:36.000Z",
            "2020-08-02T11:33:41.000Z",
            "2020-08-03T11:57:41.000Z",
        ],
        format="%Y-%m-%dT%H:%M:%S.%fZ",
    ).tz_localize("UTC")
    timestamps = pd.to_datetime(
        [
            "2019-08-01T15:45:36.000Z",
            "2019-08-02T11:33:41.000Z",
            "2019-08-03T11:57:41.000Z",
        ],
        format="%Y-%m-%dT%H:%M:%S.%fZ",
    ).tz_localize("UTC")

    ts_df = pd.DataFrame(
        {"timestamp": timestamps, "values": values, "more_timestamps": more_timestamps}, index=index
    )
    ts_df.attrs["foo"] = "bar"

    return ts_df


def test_modify_timezone_good_dataframe(dataframe):
    local_summertime = modify_timezone(
        dataframe, to_timezone="Europe/Berlin", column_name="timestamp"
    )

    # German summer time starts in last Sunday in March at 2 am. --> UTC 1am
    timestamp_id = local_summertime.columns.get_loc("timestamp")
    assert local_summertime.iloc[1, timestamp_id].utcoffset() == datetime.timedelta(seconds=7200)
    assert local_summertime.iloc[2, timestamp_id].utcoffset() == datetime.timedelta(seconds=7200)
    assert "foo" in local_summertime.attrs


def test_modify_timezone_good_series(series_summer, series_winter):
    local_summertime = modify_timezone(series_summer, to_timezone="Europe/Berlin")
    local_wintertime = modify_timezone(series_winter, to_timezone="Europe/Berlin")
    cet = modify_timezone(series_winter, to_timezone="CET")
    utc_wintertime = modify_timezone(local_wintertime, to_timezone="UTC")

    # German summer time starts in last Sunday in March at 2 am. --> UTC 1am
    assert local_summertime.index[1].utcoffset() == datetime.timedelta(seconds=3600)
    assert local_summertime.index[2].utcoffset() == datetime.timedelta(seconds=7200)
    assert "foo" in local_summertime.attrs

    # German winter time starts in last Sunday in October at 3 am. --> UTC: 1am
    assert local_wintertime.index[0].utcoffset() == datetime.timedelta(seconds=7200)
    assert local_wintertime.index[1].utcoffset() == datetime.timedelta(seconds=3600)
    assert "foo" in local_wintertime.attrs

    # cet is equal to German winter time
    assert local_wintertime.index[1] == cet.index[1]

    # reversing works
    pd.testing.assert_series_equal(series_winter, utc_wintertime)

    # timedelta not influneced by new timezone
    np.testing.assert_array_equal(
        pd.to_timedelta(local_summertime.index[1:] - local_summertime.index[:-1])
        .total_seconds()
        .values,
        [3600.0, 3600.0, 3600.0],
    )


def test_modify_timezone_wrong_tzname(series_summer):
    with pytest.raises(ValueError, match="Timezone not known*"):
        _ = modify_timezone(series_summer, to_timezone="Europe/Berlin2")


def test_named_series(series_summer):
    data = pd.Series(series_summer.index)
    data.name = "timestamp"
    data.attrs = series_summer.attrs
    modified_data = modify_timezone(data, to_timezone="Europe/Berlin", column_name="timestamp")
    assert modified_data[1].utcoffset() == datetime.timedelta(seconds=3600)
    assert "foo" in modified_data.attrs


def test_named_series_using_index(series_summer):
    data = series_summer
    data.name = "timestamp"
    modified_data = modify_timezone(data, to_timezone="Europe/Berlin", column_name=None)
    assert modified_data.index[0].utcoffset() == datetime.timedelta(seconds=3600)
    assert "foo" in modified_data.attrs


def test_column_not_known(series_summer, dataframe):
    data = pd.Series(series_summer.index)
    data.name = "timestamp"

    with pytest.raises(KeyError, match="Column name*"):
        _ = modify_timezone(data, to_timezone="Europe/Berlin", column_name="timestamp2")

    with pytest.raises(KeyError, match="Column name*"):
        _ = modify_timezone(dataframe, to_timezone="Europe/Berlin", column_name="timestamp2")


def test_modify_timezone_no_tz_known(series_summer):
    series_summer.index = series_summer.index.tz_localize(None)
    with pytest.raises(TypeError, match="Entries to convert do not contain valid timestamps*"):
        _ = modify_timezone(series_summer, to_timezone="Europe/Berlin")


def test_modify_timezone_multicolumn_dataframe(multicolumn_frame):
    local_summertime = modify_timezone(
        multicolumn_frame,
        to_timezone="Europe/Berlin",
        column_names=["timestamp", "more_timestamps"],
    )

    # German summer time starts in last Sunday in March at 2 am. --> UTC 1am
    timestamp_id = local_summertime.columns.get_loc("timestamp")
    timestamp_id_2 = local_summertime.columns.get_loc("more_timestamps")
    assert local_summertime.iloc[1, timestamp_id].utcoffset() == datetime.timedelta(seconds=7200)
    assert local_summertime.iloc[1, timestamp_id_2].utcoffset() == datetime.timedelta(seconds=7200)
    assert local_summertime.index[1].utcoffset() == datetime.timedelta(seconds=7200)
    assert "foo" in local_summertime.attrs


def test_modify_timezone_multicolumn_dataframe_without_index(multicolumn_frame):
    local_summertime = modify_timezone(
        multicolumn_frame,
        to_timezone="Europe/Berlin",
        column_names=["timestamp", "more_timestamps"],
        convert_index=False,
    )

    # German summer time starts in last Sunday in March at 2 am. --> UTC 1am
    timestamp_id = local_summertime.columns.get_loc("timestamp")
    timestamp_id_2 = local_summertime.columns.get_loc("more_timestamps")
    assert local_summertime.iloc[1, timestamp_id].utcoffset() == datetime.timedelta(seconds=7200)
    assert local_summertime.iloc[1, timestamp_id_2].utcoffset() == datetime.timedelta(seconds=7200)
    assert local_summertime.index[1].utcoffset() == datetime.timedelta(seconds=0)
    assert "foo" in local_summertime.attrs


def test_plot_target_timezone(series_summer):
    plot_target_settings_mock = MagicMock(
        return_value=PlotTargetSettings(plot_target_timezone="Europe/Berlin")
    )
    with patch("hdhelpers.user_functions.get_plot_target_settings", plot_target_settings_mock):
        modified_data = modify_timezone(series_summer)
        assert modified_data.index[1].utcoffset() == datetime.timedelta(seconds=3600)


def test_modify_timestamp():
    modified_timestamp = modify_timezone(
        pd.to_datetime("2023-03-25 23:00", utc=True), to_timezone="Europe/Berlin"
    )
    assert modified_timestamp.utcoffset() == datetime.timedelta(seconds=3600)


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

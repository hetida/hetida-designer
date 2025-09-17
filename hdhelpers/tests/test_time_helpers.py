import datetime
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from hdhelpers.exceptions import HelperException
from hdhelpers.plot_target_settings import (
    PlotTargetSettings,
)
from hdhelpers.time_helpers import (
    _convert_to_optional_timezone,
    _get_end_timestamp,
    _get_start_timestamp,
    _to_pd_timestamp,
    modify_timezone,
)


def test_convert_to_optional_timezone_naive_none():
    assert (
        _convert_to_optional_timezone(pd.to_datetime("2025-01-01T01:00:00"), None).tz
        == datetime.timezone.utc
    )


def test_convert_to_optional_timezone_aware_none():
    assert _convert_to_optional_timezone(
        pd.to_datetime("2025-01-01T01:00:00+05:00"), None
    ).tz == datetime.timezone(datetime.timedelta(seconds=18000))


def test_convert_to_optional_timezone_naive_given():
    timestamp = _convert_to_optional_timezone(
        pd.to_datetime("2025-01-01T01:00:00"), "Europe/Berlin"
    )
    assert timestamp.utcoffset() == datetime.timedelta(seconds=3600)


def test_convert_to_optional_timezone_aware_given():
    timestamp = _convert_to_optional_timezone(
        pd.to_datetime("2025-01-01T01:00:00+05:00"), "Europe/Berlin"
    )
    assert timestamp.utcoffset() == datetime.timedelta(seconds=3600)


def test_get_start_timestamp_directly():
    timestamp = _get_start_timestamp(pd.Series(), "2025-05-28T09:00:00+02:00")
    assert isinstance(timestamp, pd.Timestamp)


def test_get_start_timestamp_attrs():
    series = pd.Series()
    series.attrs = {
        "single_metric_dataset_metadata": {
            "ref_interval_start_timestamp": "2025-05-28T09:00:00+02:00"
        }
    }
    timestamp = _get_start_timestamp(series, None)
    assert isinstance(timestamp, pd.Timestamp)


def test_get_start_timestamp_plot_target_settings():
    plot_target_settings_mock = MagicMock(
        return_value=PlotTargetSettings(datetime_x_axes_range_start="2025-05-28T09:00:00+02:00")
    )
    with patch("hdhelpers.time_helpers.get_plot_target_settings", plot_target_settings_mock):
        timestamp = _get_start_timestamp(pd.Series(), None)
        assert isinstance(timestamp, pd.Timestamp)


def test_get_end_timestamp_directly():
    timestamp = _get_end_timestamp(pd.Series(), "2025-05-28T18:00:00+02:00")
    assert isinstance(timestamp, pd.Timestamp)


def test_get_end_timestamp_attrs():
    series = pd.Series()
    series.attrs = {
        "single_metric_dataset_metadata": {
            "ref_interval_end_timestamp": "2025-05-28T18:00:00+02:00"
        }
    }
    timestamp = _get_end_timestamp(series, None)
    assert isinstance(timestamp, pd.Timestamp)


def test_get_end_timestamp_plot_target_settings():
    plot_target_settings_mock = MagicMock(
        return_value=PlotTargetSettings(datetime_x_axes_range_end="2025-05-28T18:00:00+02:00")
    )
    with patch("hdhelpers.time_helpers.get_plot_target_settings", plot_target_settings_mock):
        timestamp = _get_end_timestamp(pd.Series(), None)
        assert isinstance(timestamp, pd.Timestamp)


def test_get_end_none():
    timestamp = _get_end_timestamp(pd.Series(), None)
    assert timestamp is None


def test_get_start_none():
    timestamp = _get_start_timestamp(pd.Series(), None)
    assert timestamp is None


def test_to_pd_timestamp_int():
    timestamp = 1748415600
    timestamp = _to_pd_timestamp(timestamp)
    assert isinstance(timestamp, pd.Timestamp)


def test_to_pd_timestamp_str():
    timestamp = "2025-05-28T09:00:00+02:00"
    timestamp = _to_pd_timestamp(timestamp)
    assert isinstance(timestamp, pd.Timestamp)


def test_to_pd_timestamp_none():
    timestamp = None
    timestamp = _to_pd_timestamp(timestamp)
    assert timestamp is None


def test_to_pd_timestamp_float():
    timestamp = 3.14
    with pytest.raises(HelperException):
        timestamp = _to_pd_timestamp(timestamp)


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
    with patch("hdhelpers.time_helpers.get_plot_target_settings", plot_target_settings_mock):
        modified_data = modify_timezone(series_summer)
        assert modified_data.index[1].utcoffset() == datetime.timedelta(seconds=3600)


def test_modify_timestamp():
    modified_timestamp = modify_timezone(
        pd.to_datetime("2023-03-25 23:00", utc=True), to_timezone="Europe/Berlin"
    )
    assert modified_timestamp.utcoffset() == datetime.timedelta(seconds=3600)

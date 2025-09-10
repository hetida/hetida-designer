import datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from hdhelpers.exceptions import HelperException
from hdhelpers.helper_functions import (
    _convert_to_optional_timezone,
    _get_display_name,
    _get_end_timestamp,
    _get_start_timestamp,
    _get_unit,
    _pad_end,
    _pad_start,
    _to_datetime,
)
from hdhelpers.plot_target_settings import PlotTargetSettings


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
    with patch("hdhelpers.helper_functions.get_plot_target_settings", plot_target_settings_mock):
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
    with patch("hdhelpers.helper_functions.get_plot_target_settings", plot_target_settings_mock):
        timestamp = _get_end_timestamp(pd.Series(), None)
        assert isinstance(timestamp, pd.Timestamp)


def test_get_end_none():
    timestamp = _get_end_timestamp(pd.Series(), None)
    assert timestamp is None


def test_get_start_none():
    timestamp = _get_start_timestamp(pd.Series(), None)
    assert timestamp is None


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


def test_to_datetime_int():
    timestamp = 1748415600
    timestamp = _to_datetime(timestamp)
    assert isinstance(timestamp, pd.Timestamp)


def test_to_datetime_str():
    timestamp = "2025-05-28T09:00:00+02:00"
    timestamp = _to_datetime(timestamp)
    assert isinstance(timestamp, pd.Timestamp)


def test_to_datetime_none():
    timestamp = None
    timestamp = _to_datetime(timestamp)
    assert timestamp is None


def test_to_datetime_float():
    timestamp = 3.14
    with pytest.raises(HelperException):
        timestamp = _to_datetime(timestamp)

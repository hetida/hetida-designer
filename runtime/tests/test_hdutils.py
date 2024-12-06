import datetime

import numpy as np
import pandas as pd
import pytest

from hdutils import modify_timezone


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

    return ts_df


def test_modify_timezone_good_dataframe(dataframe):
    local_summertime = modify_timezone(
        dataframe, to_timezone="Europe/Berlin", column_name="timestamp"
    )

    # German summer time starts in last Sunday in March at 2 am. --> UTC 1am
    timestamp_id = local_summertime.columns.get_loc("timestamp")
    assert local_summertime.iloc[1, timestamp_id].utcoffset() == datetime.timedelta(seconds=7200)
    assert local_summertime.iloc[2, timestamp_id].utcoffset() == datetime.timedelta(seconds=7200)


def test_modify_timezone_good_series(series_summer, series_winter):
    local_summertime = modify_timezone(series_summer, to_timezone="Europe/Berlin")
    local_wintertime = modify_timezone(series_winter, to_timezone="Europe/Berlin")
    cet = modify_timezone(series_winter, to_timezone="CET")
    utc_wintertime = modify_timezone(local_wintertime, to_timezone="UTC")

    # German summer time starts in last Sunday in March at 2 am. --> UTC 1am
    assert local_summertime.index[1].utcoffset() == datetime.timedelta(seconds=3600)
    assert local_summertime.index[2].utcoffset() == datetime.timedelta(seconds=7200)

    # German winter time starts in last Sunday in October at 3 am. --> UTC: 1am
    assert local_wintertime.index[0].utcoffset() == datetime.timedelta(seconds=7200)
    assert local_wintertime.index[1].utcoffset() == datetime.timedelta(seconds=3600)

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
    modified_data = modify_timezone(data, to_timezone="Europe/Berlin", column_name="timestamp")
    assert modified_data[1].utcoffset() == datetime.timedelta(seconds=3600)


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


def test_modify_timezone_no_tz_in_index(series_summer):
    series_summer.index = series_summer.reset_index(drop=True)
    with pytest.raises(TypeError, match="Entries to convert do not contain valid timestamps*"):
        _ = modify_timezone(series_summer, to_timezone="Europe/Berlin")

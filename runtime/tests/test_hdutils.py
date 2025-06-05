
import pandas as pd
import pytest


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

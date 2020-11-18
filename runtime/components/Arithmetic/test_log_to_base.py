import pandas as pd
from .log_to_base import main


def test_numeric():
    assert main(base=2, data=16)["log"] == 4


def test_series_numeric():
    assert main(
        base=pd.Series(
            {
                "2019-08-01T15:20:12": 4,
                "2019-08-01T15:44:12": None,
                "2019-08-03T16:20:15": 2,
                "2019-08-05T12:00:34": 8,
            }
        ),
        data=64,
    )["log"].equals(
        pd.Series(
            {
                "2019-08-01T15:20:12": 3,
                "2019-08-01T15:44:12": None,
                "2019-08-03T16:20:15": 6,
                "2019-08-05T12:00:34": 2,
            }
        )
    )


def test_series_series():
    assert main(
        base=pd.Series(
            {
                "2019-08-01T15:20:12": 2,
                "2019-08-01T15:44:12": None,
                "2019-08-03T16:20:15": 0.5,
                "2019-08-05T12:00:34": 4,
            }
        ),
        data=pd.Series(
            {
                "2019-08-01T15:20:12": 4,
                "2019-08-01T15:44:12": 4,
                "2019-08-03T16:20:15": 0.25,
                "2019-08-05T12:00:34": 2,
            }
        ),
    )["log"].equals(
        pd.Series(
            {
                "2019-08-01T15:20:12": 2,
                "2019-08-01T15:44:12": None,
                "2019-08-03T16:20:15": 2,
                "2019-08-05T12:00:34": 0.5,
            }
        )
    )


def test_df_df():
    assert main(
        base=pd.DataFrame(
            {
                "a": {
                    "2019-08-01T15:20:12": 3,
                    "2019-08-01T15:44:12": 7,
                    "2019-08-03T16:20:15": 2,
                },
                "b": {
                    "2019-08-01T15:20:12": 7,
                    "2019-08-01T15:44:12": 4,
                    "2019-08-03T16:20:15": 5,
                },
            }
        ),
        data=pd.DataFrame(
            {
                "a": {
                    "2019-08-01T15:20:12": 1,
                    "2019-08-01T15:44:12": 49,
                    "2019-08-03T16:20:15": 0.25,
                },
                "b": {
                    "2019-08-01T15:20:12": 1,
                    "2019-08-01T15:44:12": 0.25,
                    "2019-08-03T16:20:15": 25,
                },
            }
        ),
    )["log"].equals(
        pd.DataFrame(
            {
                "a": {
                    "2019-08-01T15:20:12": 0.0,
                    "2019-08-01T15:44:12": 2.0,
                    "2019-08-03T16:20:15": -2.0,
                },
                "b": {
                    "2019-08-01T15:20:12": 0.0,
                    "2019-08-01T15:44:12": -1.0,
                    "2019-08-03T16:20:15": 2.0,
                },
            }
        )
    )


def test_series_empty_base():
    assert main(data=pd.Series(dtype=float), base=2)["log"].empty


def test_series_base_empty():
    assert main(base=pd.Series(dtype=float), data=2)["log"].empty


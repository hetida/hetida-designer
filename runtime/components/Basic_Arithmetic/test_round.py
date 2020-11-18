import pandas as pd
import math
from .round import main


def test_float():
    assert main(data=2.4854, decimals=3)["rounded"] == 2.485


def test_series():
    assert main(
        data=pd.Series(
            {
                "2019-08-01T15:20:12": 4.4554,
                "2019-08-01T15:44:12": None,
                "2019-08-03T16:20:15": 2.1212,
                "2019-08-05T12:00:34": 8.999,
            }
        ),
        decimals=0,
    )["rounded"].equals(
        pd.Series(
            {
                "2019-08-01T15:20:12": 4,
                "2019-08-01T15:44:12": None,
                "2019-08-03T16:20:15": 2,
                "2019-08-05T12:00:34": 9,
            }
        )
    )


def test_df():
    assert main(
        data=pd.DataFrame(
            {
                "a": {
                    "2019-08-01T15:20:12": 3.154,
                    "2019-08-01T15:44:12": 7.5415,
                    "2019-08-03T16:20:15": 0.7812,
                    "2019-08-05T12:00:34": 2.8979,
                },
                "b": {
                    "2019-08-01T15:20:12": 0.585746,
                    "2019-08-01T15:44:12": 4.123,
                    "2019-08-03T16:20:15": 5.7898,
                    "2019-08-05T12:00:34": 7.321,
                },
            }
        ),
        decimals=1,
    )["rounded"].equals(
        pd.DataFrame(
            {
                "a": {
                    "2019-08-01T15:20:12": 3.2,
                    "2019-08-01T15:44:12": 7.5,
                    "2019-08-03T16:20:15": 0.8,
                    "2019-08-05T12:00:34": 2.9,
                },
                "b": {
                    "2019-08-01T15:20:12": 0.6,
                    "2019-08-01T15:44:12": 4.1,
                    "2019-08-03T16:20:15": 5.8,
                    "2019-08-05T12:00:34": 7.3,
                },
            }
        )
    )


def test_empty_series_series():
    assert main(data=pd.Series(dtype=float), decimals=5)["rounded"].empty


import pandas as pd
import pytest
import math
from .average import main


def test_series():
    assert (
        main(
            data=pd.Series(
                {
                    "2019-08-01T15:20:25": 0.3,
                    "2019-08-01T15:20:10": 1.7,
                    "2019-08-01T15:20:20": None,
                    "2019-08-01T15:20:30": 1.0,
                }
            )
        )["average"]
        == 1.0
    )


def test_df():
    assert main(
        data=pd.DataFrame(
            {
                "a": {
                    "2019-08-01T15:20:12": -4,
                    "2019-08-01T15:44:12": 9,
                    "2019-08-03T16:20:15": 0,
                    "2019-08-05T12:00:34": -1,
                },
                "b": {
                    "2019-08-01T15:20:12": 10,
                    "2019-08-01T15:44:12": -1,
                    "2019-08-03T16:20:15": None,
                    "2019-08-05T12:00:34": 12,
                },
            }
        )
    )["average"].equals(pd.Series({"a": 1.0, "b": 7.0}))


def test_df_2():
    assert main(
        data=pd.DataFrame(
            {
                "a": {
                    "2019-08-01T15:20:12": -4,
                    "2019-08-01T15:44:12": 9,
                    "2019-08-03T16:20:15": 0,
                    "2019-08-05T12:00:34": -1,
                },
                "b": {
                    "2019-08-01T15:20:12": "Hello",
                    "2019-08-01T15:44:12": -1,
                    "2019-08-03T16:20:15": None,
                    "2019-08-05T12:00:34": 12,
                },
            }
        )
    )["average"].equals(pd.Series({"a": 1.0}))


def test_series_empty():
    assert math.isnan(main(data=pd.Series(dtype=float))["average"])


def test_empty_df():
    assert main(data=pd.DataFrame(dtype=float))["average"].empty

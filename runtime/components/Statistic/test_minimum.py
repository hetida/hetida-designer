import pandas as pd
import pytest
import math
from .minimum import main


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
        )["min"]
        == 0.3
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
    )["min"].equals(pd.Series({"a": -4.0, "b": -1.0}))


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
    )["min"].equals(pd.Series({"a": -4}))


def test_series_empty():
    assert math.isnan(main(data=pd.Series(dtype=float))["min"])


def test_empty_df():
    assert main(data=pd.DataFrame(dtype=float))["min"].empty

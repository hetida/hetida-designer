import pandas as pd
import pytest
from .consecutive_differences import main


def test_date_seconds():
    assert main(
        data=pd.Series(
            {
                "2019-08-01T15:20:10": 0.0,
                "2019-08-01T15:20:11": 27.0,
                "2019-08-01T15:20:14": 18.0,
                "2019-08-01T15:20:16": 22.0,
            }
        )
    )["diff"].equals(
        pd.Series(
            {
                "2019-08-01T15:20:11": 27.0,
                "2019-08-01T15:20:14": -9.0,
                "2019-08-01T15:20:16": 4.0,
            }
        )
    )


def test_date_unsorted():
    assert main(
        data=pd.Series(
            {
                "2019-08-01T15:20:14": 18.0,
                "2019-08-01T15:20:10": 0.0,
                "2019-08-01T15:20:11": 27.0,
                "2019-08-01T15:20:16": 22.0,
            }
        )
    )["diff"].equals(
        pd.Series(
            {
                "2019-08-01T15:20:11": 27.0,
                "2019-08-01T15:20:14": -9.0,
                "2019-08-01T15:20:16": 4.0,
            }
        )
    )


def test_date_milliseconds():
    assert main(
        data=pd.Series(
            {
                "2019-08-01T15:20:25.000Z": 0.0,
                "2019-08-01T15:20:25.001Z": 20.0,
                "2019-08-01T15:20:25.002Z": 10.0,
                "2019-08-01T15:20:25.100Z": 10.0,
            }
        )
    )["diff"].equals(
        pd.Series(
            {
                "2019-08-01T15:20:25.001Z": 20.0,
                "2019-08-01T15:20:25.002Z": -10.0,
                "2019-08-01T15:20:25.100Z": 0.0,
            }
        )
    )


def test_numeric_index():
    assert main(data=pd.Series({0: 1.0, 1: 4.0, 3: 5.0, 4: 8.0}))["diff"].equals(
        pd.Series({1: 3.0, 3: 1.0, 4: 3.0})
    )


def test_numeric_unsorted():
    assert main(data=pd.Series({1: 4.0, 3: 5.0, 0: 1.0, 4: 8.0}))["diff"].equals(
        pd.Series({1: 3.0, 3: 1.0, 4: 3.0})
    )


def test_series_empty():
    assert main(data=pd.Series(dtype=float))["diff"].empty


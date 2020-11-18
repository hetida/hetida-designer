import pandas as pd
import pytest
from .derivate import main


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
    )["diff_quo"].equals(
        pd.Series(
            {
                "2019-08-01T15:20:11": 27.0,
                "2019-08-01T15:20:14": -3.0,
                "2019-08-01T15:20:16": 2.0,
            }
        )
    )

    def test_date_unsorted():
        assert main(
            data=pd.Series(
                {
                    "2019-08-01T15:20:10": 0.0,
                    "2019-08-01T15:20:14": 18.0,
                    "2019-08-01T15:20:16": 22.0,
                    "2019-08-01T15:20:11": 27.0,
                }
            )
        )["diff_quo"].equals(
            pd.Series(
                {
                    "2019-08-01T15:20:11": 27.0,
                    "2019-08-01T15:20:14": -3.0,
                    "2019-08-01T15:20:16": 2.0,
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
    )["diff_quo"].equals(
        pd.Series(
            {
                "2019-08-01T15:20:25.001Z": 20000.0,
                "2019-08-01T15:20:25.002Z": -10000.0,
                "2019-08-01T15:20:25.100Z": 0.0,
            }
        )
    )


def test_numeric_index():
    assert main(data=pd.Series({0: 1.0, 1: 4.0, 3: 5.0, 4: 8.0}))["diff_quo"].equals(
        pd.Series({1: 3.0, 3: 0.5, 4: 3.0})
    )


def test_numeric_unsorted():
    assert main(data=pd.Series({3: 5.0, 0: 1.0, 1: 4.0, 4: 8.0}))["diff_quo"].equals(
        pd.Series({1: 3.0, 3: 0.5, 4: 3.0})
    )


def test_series_empty():
    with pytest.raises(ValueError, match="size of data must be at least 2"):
        assert main(data=pd.Series(dtype=float))


def test_index_string():
    with pytest.raises(TypeError, match="indices of data must be numeric or datetime"):
        assert main(
            data=pd.Series(
                {"test": 0.3, "hello": 1.7, "2019-08-01T15:20:25.113Z": -0.3}
            )
        )

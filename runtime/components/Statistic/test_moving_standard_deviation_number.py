import pandas as pd
import numpy as np
import pytest
from .moving_standard_deviation_number import main


def test_date():
    pd.testing.assert_series_equal(
        main(
            data=pd.Series(
                {
                    "2019-08-01T15:20:10": 0.0,
                    "2019-08-01T15:20:11": 1.0,
                    "2019-08-01T15:20:14": 18.0,
                    "2019-08-01T15:20:16": 2.0,
                }
            ),
            n=2,
        )["movstd"],
        pd.Series(
            [np.nan, 0.707, 12.020, 11.313],
            index=pd.to_datetime(
                [
                    "2019-08-01T15:20:10",
                    "2019-08-01T15:20:11",
                    "2019-08-01T15:20:14",
                    "2019-08-01T15:20:16",
                ]
            ),
        ),
        atol=1e-3,
    )


def test_date_unsorted():
    pd.testing.assert_series_equal(
        main(
            data=pd.Series(
                {
                    "2019-08-01T15:20:10": 0.0,
                    "2019-08-01T15:20:14": 18.0,
                    "2019-08-01T15:20:16": 2.0,
                    "2019-08-01T15:20:11": 1.0,
                }
            ),
            n=2,
        )["movstd"],
        pd.Series(
            [np.nan, 0.707, 12.020, 11.313],
            index=pd.to_datetime(
                [
                    "2019-08-01T15:20:10",
                    "2019-08-01T15:20:11",
                    "2019-08-01T15:20:14",
                    "2019-08-01T15:20:16",
                ]
            ),
        ),
        atol=1e-3,
    )


def test_numeric_index():
    pd.testing.assert_series_equal(
        main(data=pd.Series({0: 1.0, 1: 4.0, 3: 4.0, 4: 7.0}), n=3)["movstd"],
        pd.Series({0: np.nan, 1: np.nan, 3: 1.732, 4: 1.732}),
        atol=1e-3,
    )


def test_numeric_unsorted():
    pd.testing.assert_series_equal(
        main(data=pd.Series({3: 4.0, 0: 1.0, 1: 4.0, 4: 7.0}), n=3)["movstd"],
        pd.Series({0: np.nan, 1: np.nan, 3: 1.732, 4: 1.732}),
        atol=1e-3,
    )


def test_series_empty():
    assert main(data=pd.Series(dtype=float), n=4)["movstd"].empty


def test_index_string():
    with pytest.raises(TypeError, match="indices of data must be numeric or datetime"):
        assert main(
            data=pd.Series(
                {"test": 0.3, "hello": 1.7, "2019-08-01T15:20:25.113Z": -0.3}
            ),
            n=5,
        )

import pandas as pd
import numpy as np
import pytest
from .moving_median_number import main


def test_date():
    assert main(
        data=pd.Series(
            {
                "2019-08-01T15:20:10": 0.0,
                "2019-08-01T15:20:11": 22.0,
                "2019-08-01T15:20:14": 18.0,
                "2019-08-01T15:20:16": 2.0,
            }
        ),
        n=3,
    )["movmedian"].equals(
        pd.Series(
            {
                "2019-08-01T15:20:10": np.nan,
                "2019-08-01T15:20:11": np.nan,
                "2019-08-01T15:20:14": 18.0,
                "2019-08-01T15:20:16": 18.0,
            }
        )
    )


def test_none():
    assert main(
        data=pd.Series(
            {
                "2019-08-01T15:20:10": 0.0,
                "2019-08-01T15:20:11": None,
                "2019-08-01T15:20:14": 18.0,
                "2019-08-01T15:20:16": 2.0,
            }
        ),
        n=3,
    )["movmedian"].equals(
        pd.Series(
            {
                "2019-08-01T15:20:10": np.nan,
                "2019-08-01T15:20:14": np.nan,
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
                "2019-08-01T15:20:16": 2.0,
                "2019-08-01T15:20:11": 22.0,
            }
        ),
        n=3,
    )["movmedian"].equals(
        pd.Series(
            {
                "2019-08-01T15:20:10": np.nan,
                "2019-08-01T15:20:11": np.nan,
                "2019-08-01T15:20:14": 18.0,
                "2019-08-01T15:20:16": 18.0,
            }
        )
    )


def test_numeric_index():
    assert main(data=pd.Series({0: 1.0, 1: 4.0, 3: 4.0, 4: 7.0}), n=3)[
        "movmedian"
    ].equals(pd.Series({0: np.nan, 1: np.nan, 3: 4.0, 4: 4.0}))


def test_numeric_unsorted():
    assert main(data=pd.Series({3: 4.0, 0: 1.0, 1: 4.0, 4: 7.0}), n=3)[
        "movmedian"
    ].equals(pd.Series({0: np.nan, 1: np.nan, 3: 4.0, 4: 4.0}))


def test_series_empty():
    assert main(data=pd.Series(dtype=float), n=4)["movmedian"].empty


def test_index_string():
    with pytest.raises(TypeError, match="indices of data must be numeric or datetime"):
        assert main(
            data=pd.Series(
                {"test": 0.3, "hello": 1.7, "2019-08-01T15:20:25.113Z": -0.3}
            ),
            n=5,
        )

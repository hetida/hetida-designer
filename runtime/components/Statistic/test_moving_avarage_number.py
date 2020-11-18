import pandas as pd
import numpy as np
import pytest
from .moving_average_number import main


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
        n=2,
    )["mavg"].equals(
        pd.Series(
            {
                "2019-08-01T15:20:10": np.nan,
                "2019-08-01T15:20:11": 11.0,
                "2019-08-01T15:20:14": 20.0,
                "2019-08-01T15:20:16": 10.0,
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
        n=2,
    )["mavg"].equals(
        pd.Series(
            {
                "2019-08-01T15:20:10": np.nan,
                "2019-08-01T15:20:11": 11.0,
                "2019-08-01T15:20:14": 20.0,
                "2019-08-01T15:20:16": 10.0,
            }
        )
    )


def test_numeric_index():
    assert main(data=pd.Series({0: 1.0, 1: 4.0, 3: 4.0, 4: 7.0}), n=3)["mavg"].equals(
        pd.Series({0: np.nan, 1: np.nan, 3: 3.0, 4: 5.0})
    )


def test_numeric_unsorted():
    assert main(data=pd.Series({3: 4.0, 0: 1.0, 1: 4.0, 4: 7.0}), n=3)["mavg"].equals(
        pd.Series({0: np.nan, 1: np.nan, 3: 3.0, 4: 5.0})
    )


def test_series_empty():
    assert main(data=pd.Series(dtype=float), n=4)["mavg"].empty


def test_index_string():
    with pytest.raises(TypeError, match="indices of data must be numeric or datetime"):
        assert main(
            data=pd.Series(
                {"test": 0.3, "hello": 1.7, "2019-08-01T15:20:25.113Z": -0.3}
            ),
            n=5,
        )

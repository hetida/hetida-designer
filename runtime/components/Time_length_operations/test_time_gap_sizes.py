import pandas as pd
import numpy as np
import pytest
from .time_gap_sizes import main


def test_basic():
    pd.testing.assert_series_equal(
        main(
            data=pd.Series(
                [10.0, 22.0, 18.0, 2.0],
                index=pd.to_datetime(
                    [
                        "2019-08-01 15:20:10",
                        "2019-08-01 15:20:11",
                        "2019-08-01 15:20:14",
                        "2019-08-01 15:20:16",
                    ]
                ),
            )
        )["gap_sizes"],
        pd.Series(
            [1, 3, 2],
            index=pd.to_datetime(
                ["2019-08-01 15:20:11", "2019-08-01 15:20:14", "2019-08-01 15:20:16"]
            ),
        ),
        check_dtype=False,
    )


def test_():
    with pytest.raises(
        ValueError, match="length of data must be greater than 1, it is 1"
    ):
        main(data=pd.Series({1: 0}))


def test_empty():
    with pytest.raises(
        ValueError, match="length of data must be greater than 1, it is 0"
    ):
        main(data=pd.Series(dtype=float))


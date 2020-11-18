import pandas as pd
import pytest
from .integrate import main


def test_basic_int():
    assert main(data=pd.Series({0: 2, 4: 6, 8: 2, 10: 0}))["integral"] == 34.0


def test_date_unsorted():
    assert (
        main(
            data=pd.Series(
                {
                    "2019-08-01T15:20:25": 0.3,
                    "2019-08-01T15:20:10": 1.7,
                    "2019-08-01T15:20:20": None,
                    "2019-08-01T15:20:30": 0.5,
                }
            )
        )["integral"]
        == 17.0
    )


def test_date_milliseconds():
    assert main(
        data=pd.Series(
            {
                "2019-08-01T15:20:25.000Z": 0.3,
                "2019-08-01T15:20:25.012Z": 1.7,
                "2019-08-01T15:20:25.112Z": 2.3,
                "2019-08-01T15:20:25.113Z": -0.3,
            }
        )
    )["integral"] == pytest.approx(0.213)


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


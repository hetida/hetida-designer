import pandas as pd
import numpy as np
import pytest
from .moving_median_time import main


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
        t="3s",
    )["movmedian"].equals(
        pd.Series(
            {
                "2019-08-01T15:20:10": 0.0,
                "2019-08-01T15:20:11": 11.0,
                "2019-08-01T15:20:14": 18.0,
                "2019-08-01T15:20:16": 10.0,
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
        t="3s",
    )["movmedian"].equals(
        pd.Series(
            {
                "2019-08-01T15:20:10": 0.0,
                "2019-08-01T15:20:14": 18.0,
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
        t="3s",
    )["movmedian"].equals(
        pd.Series(
            {
                "2019-08-01T15:20:10": 0.0,
                "2019-08-01T15:20:11": 11.0,
                "2019-08-01T15:20:14": 18.0,
                "2019-08-01T15:20:16": 10.0,
            }
        )
    )


def test_series_empty():
    assert main(data=pd.Series(dtype=float), t="4h")["movmedian"].empty


def test_index_string():
    with pytest.raises(TypeError, match="indices of data must be datetime"):
        assert main(
            data=pd.Series(
                {"test": 0.3, "hello": 1.7, "2019-08-01T15:20:25.113Z": -0.3}
            ),
            t="5ms",
        )


def test_wrong_t():
    with pytest.raises(ValueError, match="t could not be parsed as frequency: hello"):
        assert main(
            data=pd.Series(
                {
                    "2019-08-01T15:20:00": 0.3,
                    "2019-08-01T15:20:11": 1.7,
                    "2019-08-01T15:20:25": -0.3,
                }
            ),
            t="hello",
        )

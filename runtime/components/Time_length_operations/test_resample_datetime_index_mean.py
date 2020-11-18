import pandas as pd
import numpy as np
import pytest
from .resample_datetime_index_mean import main


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
            t="s",
        )["resampled"],
        pd.Series(
            [0.000, 1.000, np.nan, np.nan, 18.000, np.nan, 2.000],
            index=pd.to_datetime(
                [
                    "2019-08-01T15:20:10",
                    "2019-08-01T15:20:11",
                    "2019-08-01T15:20:12",
                    "2019-08-01T15:20:13",
                    "2019-08-01T15:20:14",
                    "2019-08-01T15:20:15",
                    "2019-08-01T15:20:16",
                ]
            ),
        ).asfreq("s"),
    )


def test_date_unsorted():
    with pytest.raises(ValueError, match="data must be sorted by its index"):
        main(
            data=pd.Series(
                {
                    "2019-08-01T15:20:10": 0.0,
                    "2019-08-01T15:20:14": 18.0,
                    "2019-08-01T15:20:16": 2.0,
                    "2019-08-01T15:20:11": 1.0,
                }
            ),
            t="s",
        )


def test_series_empty():
    assert main(data=pd.Series(dtype=float), t="h")["resampled"].empty


def test_index_string():
    with pytest.raises(TypeError, match="indices of data must be datetime"):
        assert main(
            data=pd.Series(
                {"test": 0.3, "hello": 1.7, "2019-08-01T15:20:25.113Z": -0.3}
            ),
            t="d",
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

import pandas as pd
import numpy as np
import pytest
from .shift_values import main


def test_series():
    pd.testing.assert_series_equal(
        main(
            data=pd.Series(
                [10.0, 22.0, 18.0],
                index=pd.to_datetime(
                    [
                        "2019-08-01 15:20:10",
                        "2019-08-01 15:20:11",
                        "2019-08-01 15:20:14",
                    ]
                ),
            ),
            periods=1,
        )["shifted"],
        pd.Series(
            [np.nan, 10.0, 22.0],
            index=pd.to_datetime(
                ["2019-08-01 15:20:10", "2019-08-01 15:20:11", "2019-08-01 15:20:14"]
            ),
        ),
        check_dtype=False,
    )


def test_df():
    pd.testing.assert_frame_equal(
        main(
            data=pd.DataFrame(
                {
                    "a": {
                        "2019-08-01T15:20:12": 1.2,
                        "2019-08-01T15:44:12": 7.2,
                        "2019-08-03T16:20:15": 0.3,
                        "2019-08-05T12:00:34": 0.5,
                    },
                    "b": {
                        "2019-08-01T15:20:12": 7.2,
                        "2019-08-01T15:44:12": 7.0,
                        "2019-08-03T16:20:15": 7.3,
                        "2019-08-05T12:00:34": 7.5,
                    },
                }
            ),
            periods=-2,
        )["shifted"],
        pd.DataFrame(
            {
                "a": {
                    "2019-08-01T15:20:12": 0.3,
                    "2019-08-01T15:44:12": 0.5,
                    "2019-08-03T16:20:15": np.nan,
                    "2019-08-05T12:00:34": np.nan,
                },
                "b": {
                    "2019-08-01T15:20:12": 7.3,
                    "2019-08-01T15:44:12": 7.5,
                    "2019-08-03T16:20:15": np.nan,
                    "2019-08-05T12:00:34": np.nan,
                },
            }
        ),
    )


def test_empty():
    assert main(data=pd.DataFrame(dtype=float), periods=10)["shifted"].empty


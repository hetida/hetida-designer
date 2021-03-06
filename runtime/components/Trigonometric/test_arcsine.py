import pandas as pd
import numpy as np
import pytest
from .arcsine import main


def test_numeric():
    assert main(data=0.0)["result"] == pytest.approx(0.0, rel=1e-5)


def test_series():
    pd.testing.assert_series_equal(
        main(
            data=pd.Series(
                {
                    "2019-08-01T15:20:12": 0.0,
                    "2019-08-01T15:44:12": 1.0,
                    "2019-08-03T16:20:15": 0.0,
                    "2019-08-05T12:00:34": -1.0,
                    "2019-08-05T12:00:55": 0.0,
                }
            )
        )["result"],
        pd.Series(
            {
                "2019-08-01T15:20:12": 0.0,
                "2019-08-01T15:44:12": np.pi / 2,
                "2019-08-03T16:20:15": 0.0,
                "2019-08-05T12:00:34": -np.pi / 2,
                "2019-08-05T12:00:55": 0.0,
            }
        ),
    )


def test_none():
    pd.testing.assert_series_equal(
        main(
            data=pd.Series(
                {
                    "2019-08-01T15:20:12": 0.0,
                    "2019-08-01T15:44:12": None,
                    "2019-08-03T16:20:15": np.nan,
                }
            )
        )["result"],
        pd.Series(
            {
                "2019-08-01T15:20:12": 0.0,
                "2019-08-01T15:44:12": np.nan,
                "2019-08-03T16:20:15": np.nan,
            }
        ),
    )


def test_df():
    pd.testing.assert_frame_equal(
        main(
            data=pd.DataFrame(
                {"a": [0.0, 1.0, 0.0, -1.0], "b": [0.0, 0.5, 0.0, -0.5]},
                index=[
                    "2019-08-01T15:20:12",
                    "2019-08-01T15:44:12",
                    "2019-08-03T16:20:15",
                    "2019-08-05T12:00:34",
                ],
            )
        )["result"],
        pd.DataFrame(
            {
                "a": [0.0, np.pi / 2, 0.0, -np.pi / 2],
                "b": [0.0, np.pi / 6, 0.0, -np.pi / 6],
            },
            index=[
                "2019-08-01T15:20:12",
                "2019-08-01T15:44:12",
                "2019-08-03T16:20:15",
                "2019-08-05T12:00:34",
            ],
        ),
    )


def test_empty_series():
    assert main(data=pd.Series(dtype=float))["result"].empty


def test_empty_df():
    assert main(data=pd.DataFrame(dtype=float))["result"].empty


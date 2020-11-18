import pandas as pd
import numpy as np
import pytest
from .tangent import main


def test_numeric():
    assert main(data=np.pi)["result"] == pytest.approx(0.0, rel=1e-1)


def test_series():
    pd.testing.assert_series_equal(
        main(
            data=pd.Series(
                {
                    "2019-08-01T15:20:12": 0.0,
                    "2019-08-01T15:44:12": np.pi / 6,
                    "2019-08-03T16:20:15": np.pi / 4,
                    "2019-08-05T12:00:34": np.pi / 3,
                    "2019-08-05T12:00:55": 10 * np.pi,
                }
            )
        )["result"],
        pd.Series(
            {
                "2019-08-01T15:20:12": 0.0,
                "2019-08-01T15:44:12": (3 ** 0.5) / 3,
                "2019-08-03T16:20:15": 1.0,
                "2019-08-05T12:00:34": (3 ** 0.5),
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
                    "2019-08-05T12:00:34": np.pi / 3,
                    "2019-08-05T12:00:55": 10 * np.pi,
                }
            )
        )["result"],
        pd.Series(
            {
                "2019-08-01T15:20:12": 0.0,
                "2019-08-01T15:44:12": np.nan,
                "2019-08-03T16:20:15": np.nan,
                "2019-08-05T12:00:34": (3 ** 0.5),
                "2019-08-05T12:00:55": 0.0,
            }
        ),
    )


def test_df():
    pd.testing.assert_frame_equal(
        main(
            data=pd.DataFrame(
                {
                    "a": [0.0, np.pi / 6, np.pi, np.pi / 4],
                    "b": [np.pi, np.pi / 3, 0.0, -np.pi / 3],
                },
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
                "a": [0.0, (3 ** 0.5) / 3, 0.0, 1.0],
                "b": [0.0, 3 ** 0.5, 0.0, -(3 ** 0.5)],
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


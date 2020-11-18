import pandas as pd
import numpy as np
import pytest
from .shift_datetime_index import main


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
            frequency="s",
            periods=-1,
        )["shifted"],
        pd.Series(
            [10.0, 22.0, 18.0],
            index=pd.to_datetime(
                ["2019-08-01 15:20:09", "2019-08-01 15:20:10", "2019-08-01 15:20:13"]
            ),
        ),
        check_dtype=False,
    )


def test_df():
    pd.testing.assert_frame_equal(
        main(
            data=pd.DataFrame(
                {"a": [1.2, 7.2, 0.3, 0.5], "b": [7.2, 7.0, 7.3, 7.5]},
                index=pd.to_datetime(
                    [
                        "2019-08-01T15:20:12",
                        "2019-08-01T15:44:12",
                        "2019-08-03T16:20:15",
                        "2019-08-05T12:00:34",
                    ]
                ),
            ),
            frequency="min",
            periods=2,
        )["shifted"],
        pd.DataFrame(
            {"a": [1.2, 7.2, 0.3, 0.5], "b": [7.2, 7.0, 7.3, 7.5]},
            index=pd.to_datetime(
                [
                    "2019-08-01T15:22:12",
                    "2019-08-01T15:46:12",
                    "2019-08-03T16:22:15",
                    "2019-08-05T12:02:34",
                ]
            ),
        ),
    )


def test_empty():
    assert main(
        data=pd.DataFrame(dtype=float, index=pd.to_datetime([])),
        frequency="d",
        periods=10,
    )["shifted"].empty


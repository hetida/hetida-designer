import pandas as pd
import numpy as np
import pytest
from .count_level_crossings import main


def test_all_edges():
    pd.testing.assert_series_equal(
        main(
            data=pd.Series(
                [10.0, 22.0, 18.0, 2.0, 12.0, 10.0, 18.0, 2.0],
                index=pd.to_datetime(
                    [
                        "2019-08-01 15:20:10",
                        "2019-08-01 15:20:11",
                        "2019-08-01 15:20:14",
                        "2019-08-01 15:20:16",
                        "2019-08-01 15:20:18",
                        "2019-08-01 15:20:20",
                        "2019-08-01 15:20:21",
                        "2019-08-01 15:20:24",
                    ]
                ),
            ),
            level=10,
            hysteresis=1,
            edge_type=0,
        )["result"],
        pd.Series(
            [0, 0, 0, 1, 2, 2, 2, 3],
            index=pd.to_datetime(
                [
                    "2019-08-01 15:20:10",
                    "2019-08-01 15:20:11",
                    "2019-08-01 15:20:14",
                    "2019-08-01 15:20:16",
                    "2019-08-01 15:20:18",
                    "2019-08-01 15:20:20",
                    "2019-08-01 15:20:21",
                    "2019-08-01 15:20:24",
                ]
            ),
        ),
        check_dtype=False,
    )


def test_falling_edges():
    pd.testing.assert_series_equal(
        main(
            data=pd.Series(
                [10.0, 22.0, 18.0, 2.0, 12.0, 10.0, 18.0, 2.0],
                index=pd.to_datetime(
                    [
                        "2019-08-01 15:20:10",
                        "2019-08-01 15:20:11",
                        "2019-08-01 15:20:14",
                        "2019-08-01 15:20:16",
                        "2019-08-01 15:20:18",
                        "2019-08-01 15:20:20",
                        "2019-08-01 15:20:21",
                        "2019-08-01 15:20:24",
                    ]
                ),
            ),
            level=10,
            hysteresis=1,
            edge_type=-1,
        )["result"],
        pd.Series(
            [0, 0, 0, 1, 1, 1, 1, 2],
            index=pd.to_datetime(
                [
                    "2019-08-01T15:20:10",
                    "2019-08-01T15:20:11",
                    "2019-08-01T15:20:14",
                    "2019-08-01T15:20:16",
                    "2019-08-01T15:20:18",
                    "2019-08-01T15:20:20",
                    "2019-08-01T15:20:21",
                    "2019-08-01T15:20:24",
                ]
            ),
        ),
        check_dtype=False,
    )


def test_rising_edges():
    pd.testing.assert_series_equal(
        main(
            data=pd.Series(
                [10.0, 22.0, 18.0, 2.0, 12.0, 10.0, 18.0, 2.0],
                index=pd.to_datetime(
                    [
                        "2019-08-01 15:20:10",
                        "2019-08-01 15:20:11",
                        "2019-08-01 15:20:14",
                        "2019-08-01 15:20:16",
                        "2019-08-01 15:20:18",
                        "2019-08-01 15:20:20",
                        "2019-08-01 15:20:21",
                        "2019-08-01 15:20:24",
                    ]
                ),
            ),
            level=10,
            hysteresis=1,
            edge_type=1,
        )["result"],
        pd.Series(
            [0, 0, 0, 0, 1, 1, 1, 1],
            index=pd.to_datetime(
                [
                    "2019-08-01T15:20:10",
                    "2019-08-01T15:20:11",
                    "2019-08-01T15:20:14",
                    "2019-08-01T15:20:16",
                    "2019-08-01T15:20:18",
                    "2019-08-01T15:20:20",
                    "2019-08-01T15:20:21",
                    "2019-08-01T15:20:24",
                ]
            ),
        ),
        check_dtype=False,
    )


def test_none():
    pd.testing.assert_series_equal(
        main(
            data=pd.Series(
                [10.0, 22.0, 18.0, None, 12.0, 10.0, np.nan, 2.0],
                index=pd.to_datetime(
                    [
                        "2019-08-01 15:20:10",
                        "2019-08-01 15:20:11",
                        "2019-08-01 15:20:14",
                        "2019-08-01 15:20:16",
                        "2019-08-01 15:20:18",
                        "2019-08-01 15:20:20",
                        "2019-08-01 15:20:21",
                        "2019-08-01 15:20:24",
                    ]
                ),
            ),
            level=10,
            hysteresis=1,
            edge_type=0,
        )["result"],
        pd.Series(
            [0, 0, 0, 0, 0, 0, 0, 1],
            index=pd.to_datetime(
                [
                    "2019-08-01T15:20:10",
                    "2019-08-01T15:20:11",
                    "2019-08-01T15:20:14",
                    "2019-08-01T15:20:16",
                    "2019-08-01T15:20:18",
                    "2019-08-01T15:20:20",
                    "2019-08-01T15:20:21",
                    "2019-08-01T15:20:24",
                ]
            ),
        ),
        check_dtype=False,
    )


def test_date_unsorted():
    with pytest.raises(ValueError, match="data must be sorted by its index"):
        main(
            data=pd.Series(
                {
                    "2019-08-01T15:20:20": 10.0,
                    "2019-08-01T15:20:10": 10.0,
                    "2019-08-01T15:20:11": 22.0,
                    "2019-08-01T15:20:14": 18.0,
                    "2019-08-01T15:20:21": 18.0,
                    "2019-08-01T15:20:24": 2.0,
                    "2019-08-01T15:20:16": 2.0,
                    "2019-08-01T15:20:18": 12.0,
                }
            ),
            level=10,
            hysteresis=1,
            edge_type=0,
        )


def test_numeric_index():
    pd.testing.assert_series_equal(
        main(
            data=pd.Series({0: 1.0, 1: 4.0, 3: 4.0, 4: 7.0}),
            level=5,
            hysteresis=2,
            edge_type=0,
        )["result"],
        pd.Series({0: 0, 1: 0, 3: 0, 4: 1}),
        check_dtype=False,
    )


def test_numeric_unsorted():
    with pytest.raises(ValueError, match="data must be sorted by its index"):
        main(
            data=pd.Series({3: 4.0, 0: 1.0, 1: 4.0, 4: 7.0}),
            level=5,
            hysteresis=2,
            edge_type=0,
        )["result"],
        pd.Series({0: 0, 1: 0, 3: 0, 4: 1})


def test_negative_hysteresis():
    with pytest.raises(ValueError, match="hysteresis must be non-negative, it is -5"):
        main(
            data=pd.Series({0: 1.0, 1: 4.0, 3: 4.0, 4: 7.0}),
            level=7,
            hysteresis=-5,
            edge_type=-1,
        )


def test_series_empty():
    with pytest.raises(
        ValueError, match="length of data must be greater than 1, it is 0"
    ):
        main(data=pd.Series(dtype=float), level=7, hysteresis=100, edge_type=-1)


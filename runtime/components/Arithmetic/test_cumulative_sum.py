import pandas as pd
from .cumulative_sum import main


def test_series():
    assert main(
        data=pd.Series(
            {
                "2019-08-01T15:20:10": 0.0,
                "2019-08-01T15:20:11": 27.0,
                "2019-08-01T15:20:14": 18.0,
                "2019-08-01T15:20:16": 22.0,
            }
        )
    )["cum_sum"].equals(
        pd.Series(
            {
                "2019-08-01T15:20:10": 0.0,
                "2019-08-01T15:20:11": 27.0,
                "2019-08-01T15:20:14": 45.0,
                "2019-08-01T15:20:16": 67.0,
            }
        )
    )


def test_date_unsorted():
    assert main(
        data=pd.Series(
            {
                "2019-08-01T15:20:14": 18.0,
                "2019-08-01T15:20:10": 0.0,
                "2019-08-01T15:20:11": 27.0,
                "2019-08-01T15:20:16": 22.0,
            }
        )
    )["cum_sum"].equals(
        pd.Series(
            {
                "2019-08-01T15:20:10": 0.0,
                "2019-08-01T15:20:11": 27.0,
                "2019-08-01T15:20:14": 45.0,
                "2019-08-01T15:20:16": 67.0,
            }
        )
    )


def test_numeric_index():
    assert main(data=pd.Series({0: 1.0, 1: 4.0, 3: 5.0, 4: 8.0}))["cum_sum"].equals(
        pd.Series({0: 1.0, 1: 5.0, 3: 10.0, 4: 18.0})
    )


def test_numeric_unsorted():
    assert main(data=pd.Series({1: 4.0, 3: 5.0, 0: 1.0, 4: 8.0}))["cum_sum"].equals(
        pd.Series({0: 1.0, 1: 5.0, 3: 10.0, 4: 18.0})
    )


def test_series_empty():
    assert main(data=pd.Series(dtype=float))["cum_sum"].empty


def test_df():
    assert main(
        data=pd.DataFrame(
            {
                "a": {
                    "2019-08-01T15:20:12": -4,
                    "2019-08-01T15:44:12": 9,
                    "2019-08-03T16:20:15": 0,
                    "2019-08-05T12:00:34": -1,
                },
                "b": {
                    "2019-08-01T15:20:12": -625,
                    "2019-08-01T15:44:12": -1,
                    "2019-08-03T16:20:15": 0,
                    "2019-08-05T12:00:34": 4,
                },
            }
        )
    )["cum_sum"].equals(
        pd.DataFrame(
            {
                "a": {
                    "2019-08-01T15:20:12": -4,
                    "2019-08-01T15:44:12": 5,
                    "2019-08-03T16:20:15": 5,
                    "2019-08-05T12:00:34": 4,
                },
                "b": {
                    "2019-08-01T15:20:12": -625,
                    "2019-08-01T15:44:12": -626,
                    "2019-08-03T16:20:15": -626,
                    "2019-08-05T12:00:34": -622,
                },
            }
        )
    )

    def test_empty_df():
        assert main(data=pd.DataFrame())["cum_sum"].empty

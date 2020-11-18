import pandas as pd
from .filter import main


def test_series_series():
    assert main(
        data=pd.Series(
            {
                "2019-08-01T15:20:12": 1.2,
                "2019-08-01T15:44:12": None,
                "2019-08-03T16:20:15": 0.3,
                "2019-08-05T12:00:34": 0.5,
            }
        ),
        filter_series=pd.Series(
            {
                "2019-08-01T15:20:12": True,
                "2019-08-01T15:44:12": True,
                "2019-08-03T16:20:15": False,
                "2020-08-05T12:00:34": True,
                "2021-08-05T12:00:34": False,
            }
        ),
    )["filtered"].equals(
        pd.Series({"2019-08-01T15:20:12": 1.2, "2019-08-01T15:44:12": None})
    )


def test_empty_series_series():
    assert main(
        data=pd.Series(dtype=float),
        filter_series=pd.Series(
            {
                "2019-08-01T15:20:12": True,
                "2019-08-01T15:44:12": True,
                "2019-08-03T16:20:15": False,
                "2020-08-05T12:00:34": True,
                "2021-08-05T12:00:34": False,
            }
        ),
    )["filtered"].empty


def test_series_empty_series():
    assert main(
        data=pd.Series(
            {
                "2019-08-01T15:20:12": 1.2,
                "2019-08-01T15:44:12": None,
                "2019-08-03T16:20:15": 0.3,
                "2019-08-05T12:00:34": 0.5,
            }
        ),
        filter_series=pd.Series(dtype=float),
    )["filtered"].empty


def test_df_series():
    assert main(
        data=pd.DataFrame(
            {"a": [None, 3, 14, 15], "b": [2, 71, 82, 81]},
            index=[
                "2019-08-01T15:20:12",
                "2019-08-01T15:44:12",
                "2019-08-03T16:20:15",
                "2019-08-05T12:00:34",
            ],
        ),
        filter_series=pd.Series(
            {
                "2019-08-01T15:20:12": True,
                "2019-08-01T15:44:12": True,
                "2019-08-03T16:20:15": False,
                "2020-08-05T12:00:34": True,
                "2021-08-05T12:00:34": False,
            }
        ),
    )["filtered"].equals(
        pd.DataFrame(
            {"a": [None, 3], "b": [2, 71]},
            index=["2019-08-01T15:20:12", "2019-08-01T15:44:12"],
        )
    )


def test_empty_series_series():
    assert main(
        data=pd.DataFrame(dtype=float),
        filter_series=pd.Series(
            {
                "2019-08-01T15:20:12": True,
                "2019-08-01T15:44:12": True,
                "2019-08-03T16:20:15": False,
                "2020-08-05T12:00:34": True,
                "2020-08-05T12:00:34": False,
            }
        ),
    )["filtered"].empty


def test_df_empty_series():
    assert main(
        data=pd.DataFrame(
            {"a": [None, 3, 14, 15], "b": [2, 71, 82, 81]},
            index=[
                "2019-08-01T15:20:12",
                "2019-08-01T15:44:12",
                "2019-08-03T16:20:15",
                "2019-08-05T12:00:34",
            ],
        ),
        filter_series=pd.Series(dtype=float),
    )["filtered"].empty


def test_df_series():
    assert main(
        data=pd.DataFrame(
            {"a": [None, 3, 14, 15], "b": [2, 71, 82, 81]},
            index=[
                "2019-08-01T15:20:12",
                "2019-08-01T15:44:12",
                "2019-08-03T16:20:15",
                "2019-08-05T12:00:34",
            ],
        ),
        filter_series=pd.Series(
            {
                "2019-08-01T15:20:12": 1,
                "2019-08-01T15:44:12": 0,
                "2019-08-03T16:20:15": 1,
                "2019-08-05T12:00:34": None,
            }
        ),
    )["filtered"].equals(
        pd.DataFrame(
            {"a": [None, 14, 15], "b": [2, 82, 81]},
            index=["2019-08-01T15:20:12", "2019-08-03T16:20:15", "2019-08-05T12:00:34"],
        )
    )


def test_df_series_with_string():
    assert main(
        data=pd.DataFrame(
            {"a": [None, 3, 14, 15], "b": [2, 71, 82, 81]},
            index=[
                "2019-08-01T15:20:12",
                "2019-08-01T15:44:12",
                "2019-08-03T16:20:15",
                "2019-08-05T12:00:34",
            ],
        ),
        filter_series=pd.Series(
            {
                "2019-08-01T15:20:12": 1,
                "2019-08-01T15:44:12": "test1234",
                "2019-08-03T16:20:15": None,
                "2019-08-05T12:00:34": 0,
            }
        ),
    )["filtered"].equals(
        pd.DataFrame(
            {"a": [None, 3], "b": [2, 71]},
            index=["2019-08-01T15:20:12", "2019-08-01T15:44:12"],
        )
    )

import pandas as pd
import pytest
from .restrict_to_time_interval import main


def test_series_without_timezone():
    assert main(
        data=pd.Series(
            {
                "2019-08-01T15:20:25": 0.3,
                "2019-08-01T15:20:10": 1.7,
                "2019-08-01T15:20:20": None,
                "2019-08-01T15:20:30": 0.5,
            }
        ),
        start="2019-08-01T15:20:10",
        stop="2019-08-01T15:20:26",
    )["interval"].equals(
        pd.Series(
            {
                "2019-08-01T15:20:10": 1.7,
                "2019-08-01T15:20:20": None,
                "2019-08-01T15:20:25": 0.3,
            }
        )
    )


def test_series_with_utc():
    assert main(
        data=pd.Series(
            {
                "2019-08-01T15:20:10+01:00": 1.7,
                "2019-08-01T15:20:20+01:00": None,
                "2019-08-01T15:20:30+01:00": 0.5,
            }
        ),
        start="2019-08-01T15:20:10+01:00",
        stop="today",
    )["interval"].equals(
        pd.Series(
            {
                "2019-08-01T15:20:10+01:00": 1.7,
                "2019-08-01T15:20:20+01:00": None,
                "2019-08-01T15:20:30+01:00": 0.5,
            }
        )
    )


def test_inverted_borders():
    with pytest.raises(
        ValueError, match="start timestamp cannot be after stop timestamp"
    ):
        main(
            data=pd.Series(
                {
                    "2019-08-01T15:20:10": 1.7,
                    "2019-08-01T15:20:20": None,
                    "2019-08-01T15:20:30": 0.5,
                }
            ),
            start="today",
            stop="2019-08-01T15:20:12",
        )


def test_wrong_borders():
    with pytest.raises(ValueError, match="start timestamp could not be parsed"):
        res = main(
            data=pd.Series(
                {
                    "2019-08-01T15:20:10": 1.7,
                    "2019-08-01T15:20:20": None,
                    "2019-08-01T15:20:30": 0.5,
                }
            ),
            start="hello",
            stop=None,
        )

    with pytest.raises(ValueError, match="start timestamp could not be parsed"):
        res = main(
            data=pd.Series(
                {
                    "2019-08-01T15:20:10": 1.7,
                    "2019-08-01T15:20:20": None,
                    "2019-08-01T15:20:30": 0.5,
                }
            ),
            start=None,
            stop="hello",
        )


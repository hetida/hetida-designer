import pandas as pd
import numpy as np
import math
from .ln import main


def test_numeric():
    assert main(data=math.e ** 2)["ln"] == 2


def test_series():
    assert main(
        data=pd.Series(
            {
                "2019-08-01T15:20:12": None,
                "2019-08-01T15:44:12": 1,
                "2019-08-03T16:20:15": math.e ** 3,
            }
        )
    )["ln"].equals(
        pd.Series(
            {
                "2019-08-01T15:20:12": None,
                "2019-08-01T15:44:12": 0.0,
                "2019-08-03T16:20:15": 3,
            }
        )
    )


def test_series_empty():
    assert main(data=pd.Series(dtype=float))["ln"].empty


def test_df_basic():
    assert main(
        data=pd.DataFrame(
            {
                "a": {
                    "2019-08-01T15:20:12": math.e ** 3,
                    "2019-08-01T15:44:12": 1.0,
                    "2019-08-03T16:20:15": math.e ** 2,
                },
                "b": {
                    "2019-08-01T15:20:12": math.e,
                    "2019-08-01T15:44:12": None,
                    "2019-08-03T16:20:15": math.e ** 4,
                },
            }
        )
    )["ln"].equals(
        pd.DataFrame(
            {
                "a": {
                    "2019-08-01T15:20:12": 3,
                    "2019-08-01T15:44:12": 0.0,
                    "2019-08-03T16:20:15": 2,
                },
                "b": {
                    "2019-08-01T15:20:12": 1,
                    "2019-08-01T15:44:12": None,
                    "2019-08-03T16:20:15": 4,
                },
            }
        )
    )

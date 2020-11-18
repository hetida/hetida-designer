import pandas as pd
import math
from .exp import main


def test_int():
    assert main(data=0)["exp"] == 1


def test_series():
    assert main(
        data=pd.Series(
            {
                "2019-08-01T15:20:12": 0,
                "2019-08-01T15:44:12": None,
                "2019-08-01T15:44:16": 2,
            }
        )
    )["exp"].equals(
        pd.Series(
            {
                "2019-08-01T15:20:12": 1,
                "2019-08-01T15:44:12": None,
                "2019-08-01T15:44:16": math.e ** 2,
            }
        )
    )


def test_empty_series():
    assert main(data=pd.Series(dtype=float))["exp"].equals(pd.Series(dtype=float))


from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType

import pandas as pd
import numpy as np

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={"data": DataType.Any, "t": DataType.String},
    outputs={"interpolation": DataType.Any},
)
def main(*, data, t):
    """entrypoint function for this component

    Usage example:
    >>> main(
    ...     data = pd.Series(
    ...        {
    ...             "2019-08-01T15:20:12": 1.2,
    ...             "2019-08-01T15:20:14": 7.2,
    ...             "2019-08-01T15:20:15": 0.3,
    ...             "2019-08-01T15:20:20": 0.5,
    ...        }
    ...     ),
    ...     t = "s"
    ... )["interpolation"]
    2019-08-01 15:20:12    1.20
    2019-08-01 15:20:13    4.20
    2019-08-01 15:20:14    7.20
    2019-08-01 15:20:15    0.30
    2019-08-01 15:20:16    0.34
    2019-08-01 15:20:17    0.38
    2019-08-01 15:20:18    0.42
    2019-08-01 15:20:19    0.46
    2019-08-01 15:20:20    0.50
    Freq: S, dtype: float64
    """
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your code here.

    data_date = data.copy()
    try:
        data_date.index = pd.to_datetime(data_date.index)
    except (ValueError, TypeError):
        raise TypeError("indices of data must be datetime")

    try:
        return {"interpolation": data_date.resample(t).interpolate()}
    except (ValueError):
        raise ValueError(f"t could not be parsed as frequency: {t}")

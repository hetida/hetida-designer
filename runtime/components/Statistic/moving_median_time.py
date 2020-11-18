from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType

import pandas as pd
import numpy as np

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={"data": DataType.Any, "t": DataType.String},
    outputs={"movmedian": DataType.Any},
)
def main(*, data, t):
    """entrypoint function for this component

    Usage example:
    >>> main(
    ...     data = pd.Series(
    ...        {
    ...            "2019-08-01T15:20:00": 4.0,
    ...            "2019-08-01T15:20:01": 5.0,
    ...            "2019-08-01T15:20:05": 1.0,
    ...            "2019-08-01T15:20:09": 9.0,
    ...        }
    ...     ),
    ...     t = "6s"
    ... )["movmedian"]
    2019-08-01 15:20:00    4.0
    2019-08-01 15:20:01    4.5
    2019-08-01 15:20:05    4.0
    2019-08-01 15:20:09    5.0
    dtype: float64
    """
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your code here.

    try:
        data.index = pd.to_datetime(data.index)
    except (ValueError, TypeError):
        raise TypeError("indices of data must be datetime")

    data_sort = data.sort_index().dropna()
    try:
        return {"movmedian": data_sort.rolling(t).median()}
    except (ValueError):
        raise ValueError(f"t could not be parsed as frequency: {t}")

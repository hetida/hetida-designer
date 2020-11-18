from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType

import pandas as pd
import numpy as np

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={"data": DataType.Any, "t": DataType.String},
    outputs={"resampled": DataType.Any},
)
def main(*, data, t):
    """entrypoint function for this component

    Usage example:
    >>> main(
    ...     data = pd.Series(
    ...        [0, 10, 20, 30],
    ...        index = pd.to_datetime(
    ...            [
    ...                "2019-08-01T00:00:00",
    ...                "2019-08-01T00:00:15",
    ...                "2019-08-01T00:02:00",
    ...                "2019-08-01T00:03:33"
    ...            ]
    ...        )),
    ...     t = "min"
    ... )["resampled"]
    2019-08-01 00:00:00     5.0
    2019-08-01 00:01:00     NaN
    2019-08-01 00:02:00    20.0
    2019-08-01 00:03:00    30.0
    Freq: T, dtype: float64
    """
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your code here.

    data_date = data.copy()
    try:
        data_date.index = pd.to_datetime(data_date.index)
    except (ValueError, TypeError):
        raise TypeError("indices of data must be datetime")

    if not data.index.is_monotonic:
        raise ValueError("data must be sorted by its index")

    try:
        return {"resampled": data_date.resample(t).mean()}
    except (ValueError):
        raise ValueError(f"t could not be parsed as frequency: {t}")

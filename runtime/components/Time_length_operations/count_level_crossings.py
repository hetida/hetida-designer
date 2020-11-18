from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType

import pandas as pd
import numpy as np

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={
        "data": DataType.Series,
        "level": DataType.Float,
        "hysteresis": DataType.Float,
        "edge_type": DataType.Float,
    },
    outputs={"result": DataType.Series},
)
def main(*, data, level, hysteresis, edge_type):
    """entrypoint function for this component

    Usage example:
    >>> main(data = pd.Series([1,4,11,8,3,45,1,21,5,6]), level = 8, hysteresis = 4, edge_type = 0)["result"]
    0    0
    1    0
    2    1
    3    1
    4    2
    5    3
    6    4
    7    5
    8    6
    9    6
    dtype: int64
    >>> main(
    ...     data=pd.Series(
    ...         {
    ...             "2019-08-01 15:20:10": 10.0,
    ...             "2019-08-01 15:20:11": 22.0,
    ...             "2019-08-01 15:20:14": 18.0,
    ...             "2019-08-01 15:20:16": 2.0,
    ...             "2019-08-01 15:20:18": 11.0,
    ...             "2019-08-01 15:20:20": 10.0,
    ...             "2019-08-01 15:20:21": 18.0,
    ...             "2019-08-01 15:20:24": 2.0,
    ...         }
    ...     ),
    ...     level = 10,
    ...     hysteresis = 1,
    ...     edge_type = -1,
    ... )["result"]
    2019-08-01 15:20:10    0
    2019-08-01 15:20:11    0
    2019-08-01 15:20:14    0
    2019-08-01 15:20:16    1
    2019-08-01 15:20:18    1
    2019-08-01 15:20:20    1
    2019-08-01 15:20:21    1
    2019-08-01 15:20:24    2
    dtype: int64
    """
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.

    if data.size < 2:
        raise ValueError(f"length of data must be greater than 1, it is {data.size}")

    if hysteresis < 0:
        raise ValueError(f"hysteresis must be non-negative, it is {hysteresis}")

    if not data.index.is_monotonic:
        raise ValueError("data must be sorted by its index")

    tolerance = hysteresis / 2

    crossings = (data > (level + tolerance)).astype("int64") - (
        data < (level - tolerance)
    ).astype("int64")
    crossings = crossings[crossings != 0]

    crossings.values[1:] = np.diff(crossings) / 2
    crossings = crossings[1:]

    if edge_type > 0:
        crossings = crossings[crossings == 1]
    elif edge_type < 0:
        crossings = crossings[crossings == -1] / (-1)
    else:
        crossings = np.abs(crossings).fillna(0)
        crossings = crossings[crossings != 0]

    crossings = crossings.cumsum()
    crossings = crossings.reindex(data.index)
    crossings[0] = 0

    return {"result": crossings.fillna(method="pad").astype("int64")}

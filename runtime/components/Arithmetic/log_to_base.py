from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType

import pandas as pd
import numpy as np

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={"base": DataType.Any, "data": DataType.Any}, outputs={"log": DataType.Any}
)
def main(*, base, data):
    """entrypoint function for this component

    Usage example:
    >>> main(
    ...     base = 2,
    ...     data = pd.Series(
    ...        {
    ...            "2019-08-01T15:20:12": 8.0,
    ...            "2019-08-01T15:44:12": None,
    ...            "2019-08-03T16:20:15": 1,
    ...            "2019-08-05T12:00:34": 0.5
    ...        }
    ...     )
    ... )["log"]
    2019-08-01T15:20:12    3.0
    2019-08-01T15:44:12    NaN
    2019-08-03T16:20:15    0.0
    2019-08-05T12:00:34   -1.0
    dtype: float64
    >>> main(
    ...     data = pd.Series(
    ...         {
    ...             "2019-08-01T15:20:12": 16,
    ...             "2019-08-01T15:44:12": 4,
    ...             "2019-08-03T16:20:15": 27,
    ...             "2019-08-05T12:00:34": 1,
    ...         }
    ...     ),
    ...     base = pd.Series(
    ...         {
    ...             "2019-08-01T15:20:12": 2,
    ...             "2019-08-01T15:44:12": 2,
    ...             "2019-08-03T16:20:15": 3,
    ...             "2019-08-05T12:00:34": 22,
    ...         }
    ...     ),
    ... )["log"]
    2019-08-01T15:20:12    4.0
    2019-08-01T15:44:12    2.0
    2019-08-03T16:20:15    3.0
    2019-08-05T12:00:34    0.0
    dtype: float64
    """
    
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    return {"log": np.log(data) / np.log(base)}

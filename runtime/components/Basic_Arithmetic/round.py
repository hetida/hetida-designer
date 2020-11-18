from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType

import pandas as pd
import numpy as np

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={"data": DataType.Any, "decimals": DataType.Integer},
    outputs={"rounded": DataType.Any},
)
def main(*, data, decimals):
    """entrypoint function for this component

    Usage example:
    >>> main(
    ...     data = pd.Series(
    ...        {
    ...            "2019-08-01T15:20:12": -25.054,
    ...            "2019-08-01T15:44:12": None,
    ...            "2019-08-03T16:20:15": -0.2514,
    ...            "2019-08-05T12:00:34": 9.3764
    ...        }
    ...     ),
    ...     decimals = 2 
    ... )["rounded"]
    2019-08-01T15:20:12   -25.05
    2019-08-01T15:44:12      NaN
    2019-08-03T16:20:15    -0.25
    2019-08-05T12:00:34     9.38
    dtype: float64
    """
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.

    return {"rounded": round(data, decimals)}

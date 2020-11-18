from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType

import pandas as pd
import numpy as np

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={"data": DataType.Any, "n": DataType.Any}, outputs={"root": DataType.Any}
)
def main(*, data, n):
    """entrypoint function for this component

    Usage example:
    >>> main(
    ...     data = pd.Series(
    ...        {
    ...            "2019-08-01T15:20:12": 125.0,
    ...            "2019-08-01T15:44:12": None,
    ...            "2019-08-03T16:20:15": 0.125,
    ...            "2019-08-05T12:00:34": 27.0
    ...        }
    ...     ),
    ...     n = 3
    ... )["root"]
    2019-08-01T15:20:12    5.0
    2019-08-01T15:44:12    NaN
    2019-08-03T16:20:15    0.5
    2019-08-05T12:00:34    3.0
    dtype: float64
    """
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.

    return {"root": data ** (1 / n)}

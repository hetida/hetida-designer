from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType

import pandas as pd
import numpy as np

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={"a": DataType.Any, "b": DataType.Integer}, outputs={"modulo": DataType.Any}
)
def main(*, a, b):
    """entrypoint function for this component

    Usage example:
    >>> main(
    ...     a = pd.Series(
    ...        {
    ...            "2019-08-01T15:20:12": 25,
    ...            "2019-08-01T15:44:12": None,
    ...            "2019-08-03T16:20:15": -10,
    ...            "2019-08-05T12:00:34": 4
    ...        }
    ...     ),
    ...     b = 4 
    ... )["modulo"]
    2019-08-01T15:20:12    1.0
    2019-08-01T15:44:12    NaN
    2019-08-03T16:20:15    2.0
    2019-08-05T12:00:34    0.0
    dtype: float64
    """
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.

    return {"modulo": a % b}

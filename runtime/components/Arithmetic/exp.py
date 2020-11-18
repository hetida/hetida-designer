from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType

import math
import pandas as pd

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(inputs={"data": DataType.Any}, outputs={"exp": DataType.Any})
def main(*, data):
    """entrypoint function for this component

    Usage example:
    >>> main(
    ...     data = pd.Series(
    ...        {
    ...            "2019-08-01T15:20:12": 0.0,
    ...            "2019-08-01T15:44:12": None
    ...        }
    ...     )
    ... )["exp"]
    2019-08-01T15:20:12    1.0
    2019-08-01T15:44:12    NaN
    dtype: float64
    """
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    return {"exp": math.e ** data}

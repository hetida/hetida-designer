from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType

import pandas as pd
import numpy as np
import math

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(inputs={"data": DataType.Any}, outputs={"ln": DataType.Any})
def main(*, data):
    """entrypoint function for this component

    Usage example:
    >>> main(
    ...     data = pd.Series(
    ...        {
    ...             "2019-08-01T15:20:12": None,
    ...             "2019-08-01T15:44:12": 1,
    ...             "2019-08-03T16:20:15": 2.718281828459045
    ...        }
    ...     )
    ... )["ln"]
    2019-08-01T15:20:12    NaN
    2019-08-01T15:44:12    0.0
    2019-08-03T16:20:15    1.0
    dtype: float64
    >>> main(data = (math.e ** 2))["ln"]
    2.0
    """
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    return {"ln": np.log(data)}

from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType

import pandas as pd
import numpy as np

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={"data": DataType.Any, "periods": DataType.Integer},
    outputs={"shifted": DataType.Any},
)
def main(*, data, periods):
    """entrypoint function for this component

    Usage example:
    >>> main(data = pd.Series([1,4,11,8]), periods = 2)["shifted"]
    0    NaN
    1    NaN
    2    1.0
    3    4.0
    dtype: float64
    >>> main(
    ...     data=pd.Series(
    ...             [10.0, 22.0, 18.0, 2.0],   
    ...             index=pd.to_datetime(["2019-08-01T15:20:10", "2019-08-01T15:20:11", "2019-08-01T15:20:14", "2019-08-01T15:20:16"])
    ...     ),
    ...     periods = -1
    ... )["shifted"]
    2019-08-01 15:20:10    22.0
    2019-08-01 15:20:11    18.0
    2019-08-01 15:20:14     2.0
    2019-08-01 15:20:16     NaN
    dtype: float64
    """
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.

    return {"shifted": data.shift(periods)}


from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType

import pandas as pd
import numpy as np

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={
        "data": DataType.Any,
        "frequency": DataType.String,
        "periods": DataType.Integer,
    },
    outputs={"shifted": DataType.Any},
)
def main(*, data, frequency, periods):
    """entrypoint function for this component

    Usage example:
    >>> main(
    ...     data=pd.Series(
    ...             [10.0, 22.0, 18.0, 2.0],   
    ...             index=pd.to_datetime(["2019-08-01T15:20:10", "2019-08-01T15:20:11", "2019-08-01T15:20:14", "2019-08-01T15:20:16"])
    ...     ),
    ...     frequency = "s",
    ...     periods = -4
    ... )["shifted"]
    2019-08-01 15:20:06    10.0
    2019-08-01 15:20:07    22.0
    2019-08-01 15:20:10    18.0
    2019-08-01 15:20:12     2.0
    dtype: float64
    """
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    shifted = data.copy()
    shifted.index = shifted.index.shift(periods=periods, freq=frequency)
    return {"shifted": shifted}

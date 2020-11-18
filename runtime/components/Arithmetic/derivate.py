from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType

import pandas as pd
import numpy as np

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(inputs={"data": DataType.Series}, outputs={"diff_quo": DataType.Series})
def main(*, data):
    """entrypoint function for this component

    Usage example:
    >>> main(
    ...     data = pd.Series(
    ...        {
    ...            "2019-08-01T15:20:00": 0.0,
    ...            "2019-08-01T15:20:01": 5.0,
    ...            "2019-08-01T15:20:05": 1.0,
    ...            "2019-08-01T15:20:09": 9.0,
    ...        }
    ...     )
    ... )["diff_quo"]
    2019-08-01 15:20:01    5.0
    2019-08-01 15:20:05   -1.0
    2019-08-01 15:20:09    2.0
    dtype: float64

    """
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your code here.

    if (data.size) < 2:
        raise ValueError("size of data must be at least 2")

    data_dropna = data.dropna()

    if pd.api.types.is_numeric_dtype(data_dropna.index.dtype):
        data_dropna = data_dropna.sort_index()
        x = data_dropna.index

    else:
        try:
            data_dropna.index = pd.to_datetime(data_dropna.index)
        except (ValueError, TypeError):
            raise TypeError("indices of data must be numeric or datetime")
        data_dropna = data_dropna.sort_index()
        x = (data_dropna.index - data_dropna.index[0]).total_seconds()

    y = data_dropna.values

    x_diff = np.ediff1d(x)
    y_diff = np.ediff1d(y)
    
    return {"diff_quo": pd.Series(y_diff / x_diff, index=data_dropna.index[1:])}


from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType

import pandas as pd
import numpy as np

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(inputs={"data": DataType.Series}, outputs={"diff": DataType.Series})
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
    ... )["diff"]
    2019-08-01 15:20:01    5.0
    2019-08-01 15:20:05   -4.0
    2019-08-01 15:20:09    8.0
    dtype: float64

    """
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your code here.

    data_dropna = data.dropna()

    if pd.api.types.is_numeric_dtype(data_dropna.index.dtype):
        data_dropna = data_dropna.sort_index()

    else:
        try:
            data_dropna.index = pd.to_datetime(data_dropna.index)

        except TypeError:
            raise TypeError("indices of data must be numeric or datetime")
        data_dropna = data_dropna.sort_index()
    data_diff = np.ediff1d(data_dropna.values)

    return {"diff": pd.Series(data_diff, index=data_dropna.index[1:])}


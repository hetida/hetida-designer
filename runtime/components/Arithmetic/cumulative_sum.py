from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType

import pandas as pd
import numpy as np

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(inputs={"data": DataType.Series}, outputs={"cum_sum": DataType.Series})
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
    ... )["cum_sum"]
    2019-08-01 15:20:00     0.0
    2019-08-01 15:20:01     5.0
    2019-08-01 15:20:05     6.0
    2019-08-01 15:20:09    15.0
    dtype: float64
    """
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your code here.

    if pd.api.types.is_numeric_dtype(data.index.dtype):
        data_sort = data.sort_index()

    else:
        try:
            data.index = pd.to_datetime(data.index)

        except (ValueError, TypeError):
            raise TypeError("indices of data must be numeric or datetime")
        data_sort = data.sort_index()
    return {"cum_sum": data_sort.cumsum()}

from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType

import pandas as pd
import numpy as np

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={"data": DataType.Any, "d": DataType.Integer},
    outputs={"interpolation": DataType.Any},
)
def main(*, data, d):
    """entrypoint function for this component

    Usage example:
    >>> main(
    ...     data = pd.Series(
    ...         [1.2, 7.2, 2.8, 4.8, 10.8],
    ...         index = [2, 3, 5, 6, 9]
    ...     ),
    ...     d = 2
    ... )["interpolation"]
    2    1.2
    4    5.0
    6    4.8
    8    8.8
    dtype: float64
    """
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your code here.

    if data.empty:
        return {"interpolation": data}
    data_reindex = data.reindex(
        pd.RangeIndex(data.index[0], data.index[-1], d).union(data.index)
    )
    data_reindex = data_reindex.interpolate(method="index")
    return {
        "interpolation": data_reindex.reindex(
            pd.RangeIndex(data.index[0], data.index[-1] + 1, d)
        )
    }

from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType

import pandas as pd
import numpy as np

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={"data": DataType.Any, "d": DataType.Integer},
    outputs={"resampled": DataType.Any},
)
def main(*, data, d):
    """entrypoint function for this component

    Usage example:
    >>> main(
    ...     data = pd.Series(
    ...         [0.75, 7.25, 2.75, 5.0, 10.0],
    ...         index = [2, 4, 5, 6, 9]
    ...     ),
    ...     d = 3
    ... )["resampled"]
    2    4.0
    5    5.0
    8    7.5
    dtype: float64
    """
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your code here.
    if data.empty:
        return {"resampled": data}
    if not data.index.is_monotonic:
        raise ValueError("data must be sorted by its index")

    data_reindex = data.copy()
    data_reindex = data.reindex(
        pd.RangeIndex(data.index[0], data.index[-1], d).union(data.index)
    )
    data_reindex = data_reindex.rolling(d, min_periods=1, center=True).mean()
    return {
        "resampled": data_reindex.reindex(
            pd.RangeIndex(data.index[0], data.index[-1] + 1, d)
        )
    }

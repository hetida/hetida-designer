import pandas as pd
import numpy as np
from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType  # add your own imports here

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(inputs={"data": DataType.Series}, outputs={"gap_sizes": DataType.Series})
def main(*, data):
    """entrypoint function for this component

    Usage example:
    >>> main(
    ...     data = pd.Series(
    ...             [1,2,3], 
    ...             index = pd.to_datetime([
    ...                 "2019-08-01T00:00:00",
    ...                 "2019-08-01T00:00:20",
    ...                 "2019-08-01T00:00:50"
    ...             ])
    ...     )
    ... )["gap_sizes"]
    2019-08-01 00:00:20    20.0
    2019-08-01 00:00:50    30.0
    dtype: float64
    """
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    if not len(data) >= 2:
        raise ValueError(f"length of data must be greater than 1, it is {len(data)}")
    return {
        "gap_sizes": pd.Series(
            (data.index.values[1:] - data.index.values[:-1]) / np.timedelta64(1, "s"),
            index=data.index.values[1:],
        )
    }


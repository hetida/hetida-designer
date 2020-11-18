from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType

import pandas as pd
import datetime
from scipy import integrate

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(inputs={"data": DataType.Series}, outputs={"integral": DataType.Float})
def main(*, data):
    """entrypoint function for this component

    Usage example:
    >>> main(data = pd.Series(
    ...        {
    ...            "2019-08-01T15:20:10": 1.7,
    ...            "2019-08-01T15:20:20": None,
    ...            "2019-08-01T15:20:25": 0.3,
    ...            "2019-08-01T15:20:30": 0.5,
    ...        }
    ...    ))["integral"]
    17.0
    """
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.

    if (data.size) < 2:
        raise ValueError("size of data must be at least 2")

    data_dropna = data.dropna()

    if pd.api.types.is_numeric_dtype(data_dropna.index.dtype):
        data_dropna = data_dropna.sort_index()
        x = data_dropna.index

    else:
        try:
            data_dropna.index = pd.to_datetime(data_dropna.index)
        except (TypeError, ValueError):
            raise TypeError("indices of data must be numeric or datetime")
        data_dropna = data_dropna.sort_index()
        x = (data_dropna.index - data_dropna.index[0]).total_seconds()

    y = data_dropna.values

    return {"integral": integrate.trapz(y, x)}

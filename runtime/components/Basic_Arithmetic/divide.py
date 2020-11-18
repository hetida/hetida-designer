from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType

import pandas as pd

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={"a": DataType.Any, "b": DataType.Any}, outputs={"quotient": DataType.Any}
)
def main(*, a, b):
    """entrypoint function for this component

    Usage example:
    >>> main(
    ...     a = pd.Series(
    ...        {
    ...            "2019-08-01T15:20:12": 1.5,
    ...            "2019-08-01T15:44:12": None,
    ...            "2019-08-03T16:20:15": 3.0,
    ...            "2019-08-05T12:00:34": 0.5
    ...        }
    ...     ),
    ...    b = 2
    ... )["quotient"]
    2019-08-01T15:20:12    0.75
    2019-08-01T15:44:12     NaN
    2019-08-03T16:20:15    1.50
    2019-08-05T12:00:34    0.25
    dtype: float64
    >>> main(a = pd.Series(
    ...        {
    ...            "2019-08-01T15:20:12": 1.2,
    ...            "2019-08-01T15:44:12": 7.0,
    ...            "2019-08-03T16:20:15": 0.3,
    ...            "2019-08-05T12:00:34": 5.5,
    ...        }
    ...    ),
    ...    b = pd.Series(
    ...        {
    ...            "2019-08-01T15:20:12": 1.2,
    ...            "2019-08-01T15:44:12": 3.5,
    ...            "2019-08-03T16:20:15": 3.0,
    ...            "2019-08-05T12:00:34": 0.5,
    ...        }
    ...    ),
    ... )["quotient"]
    2019-08-01T15:20:12     1.0
    2019-08-01T15:44:12     2.0
    2019-08-03T16:20:15     0.1
    2019-08-05T12:00:34    11.0
    dtype: float64
    """
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    return {"quotient": a / b}

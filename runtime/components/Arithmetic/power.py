from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType

import pandas as pd

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={"base": DataType.Any, "exponent": DataType.Any},
    outputs={"power": DataType.Any},
)
def main(*, base, exponent):
    """entrypoint function for this component

    Usage example:
    >>> main(
    ...     base = pd.Series(
    ...        {
    ...            "2019-08-01T15:20:12": 3.0,
    ...            "2019-08-01T15:44:12": None,
    ...            "2019-08-03T16:20:15": 0.3,
    ...            "2019-08-05T12:00:34": 0.5
    ...        }
    ...     ),
    ...    exponent = 2
    ... )["power"]
    2019-08-01T15:20:12    9.00
    2019-08-01T15:44:12     NaN
    2019-08-03T16:20:15    0.09
    2019-08-05T12:00:34    0.25
    dtype: float64
    >>> main(base = pd.Series(
    ...        {
    ...            "2019-08-01T15:20:12": 3,
    ...            "2019-08-01T15:44:12": 4,
    ...            "2019-08-03T16:20:15": 9,
    ...            "2019-08-05T12:00:34": 1,
    ...        }
    ...    ),
    ...    exponent = pd.Series(
    ...        {
    ...            "2019-08-01T15:20:12": 2,
    ...            "2019-08-01T15:44:12": 4,
    ...            "2019-08-03T16:20:15": 0.5,
    ...            "2019-08-05T12:00:34": 100000,
    ...        }
    ...    ),
    ... )["power"]
    2019-08-01T15:20:12      9.0
    2019-08-01T15:44:12    256.0
    2019-08-03T16:20:15      3.0
    2019-08-05T12:00:34      1.0
    dtype: float64
    """
    
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    return {"power": base ** exponent}

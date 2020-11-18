from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType

import pandas as pd

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(inputs={"data": DataType.Any}, outputs={"std": DataType.Any})
def main(*, data):
    """entrypoint function for this component

    Usage example:
    >>> main(data = pd.Series(
    ...        {
    ...            "2019-08-01T15:20:10": 1.7,
    ...            "2019-08-01T15:20:20": None,
    ...            "2019-08-01T15:20:25": 0.3,
    ...            "2019-08-01T15:20:30": 1.0,
    ...        }
    ...    ))["std"]
    0.7
    """
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.

    return {"std": data.std()}

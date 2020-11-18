from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType

import pandas as pd
import numpy as np

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(inputs={"data": DataType.Any}, outputs={"result": DataType.Any})
def main(*, data):
    """entrypoint function for this component

    Usage example:
    >>> main(data = pd.Series(
    ...        {
    ...	    	    "2019-08-01T15:20:12": 0.0,
    ...		        "2019-08-01T15:44:12": 1.0,
    ...	    	    "2019-08-03T16:20:15": -1.0,
    ...		        "2019-08-05T12:00:34": 0.5
    ...		    }
    ...    )
    ... )["result"].round(4)
    2019-08-01T15:20:12    1.57...
    2019-08-01T15:44:12    0.0...
    2019-08-03T16:20:15    3.14...
    2019-08-05T12:00:34    1.04...
    dtype: float64
    >>> main(data = 1
    ... )["result"]
    0.0
    """
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.

    return {"result": np.arccos(data)}

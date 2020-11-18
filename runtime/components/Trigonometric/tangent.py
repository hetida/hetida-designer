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
    ...		        "2019-08-01T15:44:12": np.pi/4,
    ...	    	    "2019-08-03T16:20:15": np.pi/3,
    ...             "2019-08-05T12:00:50": 10*np.pi,
    ...		    }
    ...    )
    ... )["result"].round(4)
    2019-08-01T15:20:12    0.0...
    2019-08-01T15:44:12    1.0...
    2019-08-03T16:20:15    1.7...
    2019-08-05T12:00:50   -0.0...
    dtype: float64
    """
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.

    return {"result": np.tan(data)}

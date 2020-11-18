from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType

import pandas as pd

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={"left": DataType.Any, "right": DataType.Any},
    outputs={"result": DataType.Any},
)
def main(*, left, right):
    """entrypoint function for this component

    Usage example:
    >>> main(left = pd.Series(
    ...        {
    ...	    	    "2019-08-01T15:20:12": 1.2,
    ...		        "2019-08-01T15:44:12": None,
    ...	    	    "2019-08-03T16:20:15": 0.3,
    ...		        "2019-08-05T12:00:34": 0.5,
    ...		    }
    ...    ),
    ...    right = pd.Series(
    ...        {
    ...		        "2019-08-01T15:20:12": 1.2,
    ...	   	        "2019-08-01T15:44:12": 27,
    ...		        "2019-08-03T16:20:15": 3.6,
    ...	            "2020-08-05T12:00:34": 17,
    ...		        "2021-08-05T12:00:34": None,      
    ...	        }
    ...    ),
    ... )["result"]
    2019-08-01T15:20:12     True
    2019-08-01T15:44:12    False
    2019-08-03T16:20:15     True
    2019-08-05T12:00:34    False
    2020-08-05T12:00:34    False
    2021-08-05T12:00:34    False
    dtype: bool
    """
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.

    try:
        return {"result": left <= right}
    except ValueError:
        return {"result": left.le(right)}

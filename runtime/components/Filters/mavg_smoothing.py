from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType

import pandas as pd
from scipy.signal import butter
from scipy.signal import lfilter

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={"data": DataType.Any, "window_size": DataType.String}, outputs={"data": DataType.Any})
def main(*, data, window_size):
    """entrypoint function for this component"""
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your code here
    return {"data": data.rolling(window_size).mean()}

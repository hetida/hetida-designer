from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType

import pandas as pd
from scipy.signal import butter
from scipy.signal import lfilter

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={"allowed_deviation_factor": DataType.Float, "window_size": DataType.String, "ts": DataType.Any}, outputs={"ts": DataType.Any})
def main(*, window_size="5d", allowed_deviation_factor=3.0, ts):
    """entrypoint function for this component"""
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your code here
    means = ts.rolling(window_size).mean()
    stds = ts.rolling(window_size).std()

    return {
        "ts": ts[
            (ts < means + allowed_deviation_factor * stds)
            | ((ts > means - allowed_deviation_factor * stds))
        ]
    }

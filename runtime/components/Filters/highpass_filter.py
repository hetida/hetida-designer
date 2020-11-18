from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType

import pandas as pd
from scipy.signal import butter
from scipy.signal import lfilter

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(inputs={"data": DataType.Series, "frequency": DataType.Float},outputs={"filtered": DataType.Series})
def main(*, data, frequency):
    """entrypoint function for this component"""
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your code here.
    nyq = 0.5 * data.size / ((data.index[-1] - data.index[0]).total_seconds())
    normal_frequency = frequency / nyq
    b, a = butter(1, normal_frequency, btype="high", analog=False)
    filtered = lfilter(b, a, data)
    return {"filtered": pd.Series(filtered, index=data.index)}


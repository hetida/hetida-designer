from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType

import pandas as pd

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(inputs={"ts_or_frame": DataType.Any, "limit": DataType.Float}, outputs={"ts_or_frame": DataType.Any})
def main(*, ts_or_frame, limit):
    """entrypoint function for this component"""
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    return {"ts_or_frame": ts_or_frame[ts_or_frame >= limit]}

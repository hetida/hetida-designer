from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType

import pandas as pd

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={"dataframe": DataType.DataFrame, "result_series_name": DataType.String},
    outputs={"sum_values": DataType.Series},
)
def main(*, dataframe, result_series_name):

    # ***** DO NOT EDIT LINES ABOVE *****
    s = dataframe.sum(axis=1)
    s.name = result_series_name
    return {"sum_values": s}

from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType  # add your own imports here

import pandas as pd
import logging

logger = logging.getLogger(__name__)
# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={"series_or_dataframe": DataType.Any, "series": DataType.Series},
    outputs={"dataframe": DataType.DataFrame},
)
def main(*, series_or_dataframe, series):
    """entrypoint function for this component"""
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    if isinstance(series_or_dataframe, pd.Series):
        df = series_or_dataframe.to_frame()
    elif isinstance(series_or_dataframe, pd.DataFrame):
        df = series_or_dataframe
    else:
        raise TypeError(
            "series_or_dataframe must be a pandas Series or pandas DataFrame."
        )

    if series.name is None:
        i = 0
        while str(i) in df.columns or (i in df.columns):
            i += 1
        df[str(i)] = series
    elif series.name in df.columns:
        i = 1
        while series.name + "_" + str(i) in df.columns:
            i += 1
        df[series.name + "_" + str(i)] = series
    else:
        df[series.name] = series

    return {"dataframe": df}


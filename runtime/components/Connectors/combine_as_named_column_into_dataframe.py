from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType  # add your own imports here

import pandas as pd

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={
        "series_or_dataframe": DataType.Any,
        "series": DataType.Series,
        "column_name": DataType.String,
    },
    outputs={"dataframe": DataType.DataFrame},
)
def main(*, series_or_dataframe, series, column_name):
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

    df[column_name] = series

    return {"dataframe": df}


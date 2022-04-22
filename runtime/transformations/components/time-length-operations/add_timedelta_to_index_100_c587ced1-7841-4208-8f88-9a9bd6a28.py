from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType

import pandas as pd
import numpy as np

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
@register(
    inputs={"df_or_series": DataType.Any, "timedelta": DataType.String},
    outputs={"df_or_series": DataType.Any},
    name="Add Timedelta to Index",
    description="Add a timedelta to the index of a frame or series",
    category="Time length operations",
    id="c587ced1-7841-4208-8f88-9a9bd6a28f20",
    revision_group_id="3b838621-8d8e-493a-a91a-5a7680385ed9",
    version_tag="1.0.0"
)
def main(*, df_or_series, timedelta):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    """ Usage example:
    >>> main(
    ...     df_or_series=pd.Series(
    ...             [10.0, 22.0, 18.0, 2.0],   
    ...             index=pd.to_datetime(["2019-08-01T15:20:10", "2019-08-01T15:20:11", "2019-08-01T15:20:14", "2019-08-01T15:20:16"])
    ...     ),
    ...     timedelta = "-4s",
    ... )["df_or_series"]
    2019-08-01 15:20:06    10.0
    2019-08-01 15:20:07    22.0
    2019-08-01 15:20:10    18.0
    2019-08-01 15:20:12     2.0
    dtype: float64
    """
    # write your function code here.
    df_or_series = pd.DataFrame.from_dict(df_or_series, orient="index")
    df_or_series.index = pd.to_datetime(df_or_series.index)
    if df_or_series.columns.size < 2:
        df_or_series = df_or_series.squeeze("columns")
    new_index = df_or_series.index + pd.Timedelta(timedelta)
    df_or_series.index = new_index
    return {"df_or_series": df_or_series}

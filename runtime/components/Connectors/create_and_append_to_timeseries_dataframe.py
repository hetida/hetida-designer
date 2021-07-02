"""Timeseries Dataframe

Creates (or appends to) a multi-timeseries dataframe. The result is a dataframe with 3 columns of the form:

```
{
    "value": [
        1.0,
        1.2,
        0.5,
        1.9,
        1.3,
        0.2,
        1.5,
        1.7,
        0.1
    ],
    "metric": [
        "a",
        "b",
        "c",
        "a",
        "b",
        "c",
        "a",
        "b",
        "c"
    ],
    "timestamp": [
        "2019-08-01T15:45:36.000Z",
        "2019-08-01T15:45:36.000Z",
        "2019-08-01T15:45:36.000Z",
        "2019-08-02T15:45:36.000Z",
        "2019-08-02T15:45:36.000Z",
        "2019-08-02T15:45:36.000Z",
        "2019-08-03T15:45:36.000Z",
        "2019-08-03T15:45:36.000Z",
        "2019-08-03T15:45:36.000Z"
    ]
}
```

Input to **df_or_series** can be either such a dataframe or a series (with datetime index).
"""


from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType

# add your own imports here, e.g.
import pandas as pd

#     import numpy as np


def generate_next_metric_name(df):
    i = 0
    existing_metrics = set(df["metric"].unique().tolist())
    while True:
        name = "metric_" + str(i)
        if not name in existing_metrics:
            break
        i = i + 1

    return name


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
@register(
    inputs={"df_or_series": DataType.Any, "series_to_add": DataType.Series},
    outputs={"timeseries_df": DataType.DataFrame},
    component_name="Timeseries Dataframe",
    description="Create and/or append to a multi-timeseries dataframe",
    category="Connectors",
)
def main(*, df_or_series, series_to_add):
    """entrypoint function for this component"""
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.

    if series_to_add.name is None or series_to_add.name is None:
        name = generate_next_metric_name(df_or_series)
    else:
        name = series_to_add.name

    if isinstance(df_or_series, pd.DataFrame):
        return {
            "timeseries_df": pd.concat(
                [
                    df_or_series,
                    pd.DataFrame(
                        {
                            "timestamp": series_to_add.index,
                            "value": series_to_add.values,
                            "metric": name,
                        }
                    ),
                ],
                ignore_index=True,
            )
        }
    else:
        return {
            "timeseries_df": pd.concat(
                [
                    pd.DataFrame(
                        {
                            "timestamp": df_or_series.index,
                            "value": df_or_series.values,
                            "metric": df_or_series.name
                            if df_or_series.name is not None
                            else "metric_0",
                        }
                    ),
                    pd.DataFrame(
                        {
                            "timestamp": series_to_add.index,
                            "value": series_to_add.values,
                            "metric": name,
                        }
                    ),
                ],
                ignore_index=True,
            )
        }

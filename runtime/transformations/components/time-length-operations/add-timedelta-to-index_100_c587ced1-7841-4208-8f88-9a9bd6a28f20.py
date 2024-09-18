"""Module Docsting: Documentation for "Add Timedelta to Index"

# Add Timedelta to Index

## Description
This component adds the provided timedelta to each of the indices of the provided dataframe or
series.

## Inputs
* **df_or_series** (Any): Both dataframe and series are accepted, the indices must be datetimes.
* **timedelta** (String): Timedelta to be added (may be negative) to each of the indices, e.g. '3s',
'-1min', or '2days'.

## Outputs
* **df_or_series** (Any): Dataframe or series same as the input just with the provided timedelta
added to each of the indices.

## Details
This component adds the provided timedelta to each of the indices of the provided dataframe or
series.

## Examples
The json input of a typical call of this component, adding a timedelta of 2 days to each of the
indices is
```
{
        "df_or_series": {
                "2019-08-01T15:20:00": 1.0,
                "2019-08-02T15:20:15": 7.0,
                "2019-08-04T15:19:20": 5.0
        },
        "timedelta": "2days"
}
```
The expected output is
```
        "df_or_series": {
                "2019-08-03T15:20:00": 1.0,
                "2019-08-04T15:20:15": 7.0,
                "2019-08-06T15:19:20": 5.0
        }
```

The json input of a call of this component with the same series, adding a timedelta of -1 minute
```
{
        "df_or_series": {
                "2019-08-03T15:20:00": 1.0,
                "2019-08-04T15:20:15": 7.0,
                "2019-08-06T15:19:20": 5.0
        },
        "timedelta": "-1min"
}
```
The expected output is
```
        "df_or_series": {
                "2019-08-03T15:19:00": 1.0,
                "2019-08-04T15:19:15": 7.0,
                "2019-08-06T15:18:20": 5.0
        }
```

"""

import pandas as pd

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "df_or_series": {"data_type": "ANY"},
        "timedelta": {"data_type": "STRING"},
    },
    "outputs": {
        "df_or_series": {"data_type": "ANY"},
    },
    "name": "Add Timedelta to Index",
    "category": "Time length operations",
    "description": "Add a timedelta to the index of a frame or series",
    "version_tag": "1.0.0",
    "id": "c587ced1-7841-4208-8f88-9a9bd6a28f20",
    "revision_group_id": "3b838621-8d8e-493a-a91a-5a7680385ed9",
    "state": "RELEASED",
    "released_timestamp": "2023-09-25T09:57:52.577013+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, df_or_series, timedelta):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    """Usage example:
    >>> main(
    ...     df_or_series=pd.Series(
    ...         [10.0, 22.0, 18.0, 2.0],
    ...         index=pd.to_datetime(
    ...             [
    ...                 "2019-08-01T15:20:10",
    ...                 "2019-08-01T15:20:11",
    ...                 "2019-08-01T15:20:14",
    ...                 "2019-08-01T15:20:16"
    ...             ]
                ),
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


TEST_WIRING_FROM_PY_FILE_IMPORT = {}
RELEASE_WIRING = {}

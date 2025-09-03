"""Documentation for Resample Numeric Index using Mean

# Resample Numeric Index

## Description
The component resamples data with given distances using mean.

## Inputs
* **data** (Pandas Series or Pandas DataFrame): Indices must be Integer, entries numeric.
* **d** (Integer): The distance between the new indices.

## Outputs
* **resampled** (Pandas Series or Pandas DataFrame): The resampled **data**.

## Details
The component resamples **data** using means on windows. It creates a Pandas Series or Pandas DataFrame with indices in the range of the indices of data with distance **d**.

It equips each index with the average of the numerical observations in a window of size **d** around.

## Examples
The json input of a typical call of this component with a Pandas Series is
```
{
        "data": {
                2: 1.2,
                3: 7.2,
                5: 2.8,
                6: 8.0,
                                9: 10.8
        },
        "d": 3
}
```
The expected output is
```
        "resampled": {
                                2: 4.2,
                5: 6.0,
                8: 9.4
        }
```
"""

import pandas as pd

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "data": {"data_type": "ANY"},
        "d": {"data_type": "INT"},
    },
    "outputs": {
        "resampled": {"data_type": "ANY"},
    },
    "name": "Resample Numeric Index using Mean",
    "category": "Time length operations",
    "description": "Resamples data with given distances using mean",
    "version_tag": "1.0.1",
    "id": "20ac2fca-0819-4816-a33e-4f1a8002e070",
    "revision_group_id": "015d7a72-f9c3-8a14-dde8-3aa59b2e9f10",
    "state": "RELEASED",
    "released_timestamp": "2025-06-25T08:45:58.947237+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, data, d):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your code here.
    if data.empty:
        return {"resampled": data}
    if not data.index.is_monotonic_increasing:
        raise ValueError("data must be sorted by its index")

    data_reindex = data.copy()
    data_reindex = data.reindex(pd.RangeIndex(data.index[0], data.index[-1], d).union(data.index))
    data_reindex = data_reindex.rolling(d, min_periods=1, center=True).mean()
    return {"resampled": data_reindex.reindex(pd.RangeIndex(data.index[0], data.index[-1] + 1, d))}


TEST_WIRING_FROM_PY_FILE_IMPORT = {}
RELEASE_WIRING = {}

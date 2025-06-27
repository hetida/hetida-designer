"""Documentation for Resample Datetime Index using Mean

# Resample Datetime Index using Mean

## Description
The component resamples data for some time frequency by taking mean values.

## Inputs
* **data** (Pandas Series or Pandas DataFrame): Indices must be datetime.
* **t** (String): The distance between the new indices. For example, 'ms', '15s', 'min', '2h' or 'd'.

## Outputs
* **resampled** (Pandas Series or Pandas DataFrame): The resampled **data**.

## Details
The component resamples **data**. It creates a Pandas Series or Pandas DataFrame with indices in the range of the indices of **data** with the distance t.

It equippes each index with the average numerical observations in a window of size **t**.

## Examples
The json input of a typical call of this component with a Pandas Series is
```
{
        "data": {
                "2019-08-01T00:00:00": 1.2,
                "2019-08-01T15:20:14": 7.2,
                "2019-08-03T00:00:00": 0.3,
                "2019-08-04T15:20:20": 0.5,
        },
        "t": "d"
}
```
The expected output is
```
        "resampled": {
                                "2019-08-01T00:00:00": 4.2,
                "2019-08-02T00:00:00": null,
                                "2019-08-03T00:00:00": 0.3,
                "2019-08-04T00:00:00": 0.5
        }
```
"""

import pandas as pd

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "data": {"data_type": "ANY"},
        "t": {"data_type": "STRING"},
    },
    "outputs": {
        "resampled": {"data_type": "ANY"},
    },
    "name": "Resample Datetime Index using Mean",
    "category": "Time length operations",
    "description": "Resamples data for some time frequency by taking means",
    "version_tag": "1.0.1",
    "id": "0de3f794-2bbe-453c-92c9-c35a61c961e3",
    "revision_group_id": "d48ce6ad-05ab-8bc1-fb79-c1960966f595",
    "state": "RELEASED",
    "released_timestamp": "2025-06-25T08:09:35.657398+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, data, t):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your code here.

    data_date = data.copy()
    try:
        data_date.index = pd.to_datetime(data_date.index)
    except (ValueError, TypeError):
        raise TypeError("indices of data must be datetime") from None

    if not data.index.is_monotonic_increasing:
        raise ValueError("data must be sorted by its index")

    try:
        return {"resampled": data_date.resample(t).mean()}
    except ValueError as exc:
        raise ValueError(f"t could not be parsed as frequency: {t}") from exc


TEST_WIRING_FROM_PY_FILE_IMPORT = {}
RELEASE_WIRING = {}

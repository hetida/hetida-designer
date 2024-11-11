"""Documentation for Series Difference Quotients

# Series Difference Quotients
## Description
Compute difference quotiens of a series

## Inputs
* **series** (SERIES): Series of values (typically float) with a numerical or
  datetime index. Consecutive index entries should differ in order to avoid
  division by zero.
* **dropna** (BOOLEAN, default: true): Whether dropna is called at the end.

## Outputs
* **difference_quotients** (SERIES): Series of difference quotients

## Details
Takes differences of values and divides by differences of indices. This component
expects that computing differences for both makes sense and that differences of
indices will not be zero.

## Examples
Inputting
**series**:
```
{
    "2020-01-01T01:15:27.000Z": 42.2,
    "2020-01-03T08:20:03.000Z": 18.7,
    "2020-01-03T08:20:04.000Z": 25.9
}
```
gives a result series with two entries.
"""

import pandas as pd

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "series": {"data_type": "SERIES"},
        "dropna": {"data_type": "BOOLEAN", "default_value": True},
    },
    "outputs": {
        "difference_quotients": {"data_type": "SERIES"},
    },
    "name": "Series Difference Quotients",
    "category": "Basic",
    "description": "Compute difference quotiens of a series",
    "version_tag": "1.0.0",
    "id": "3de190af-3103-4462-b5ba-2f431494abe8",
    "revision_group_id": "6c7665d7-8f4e-4ec9-892b-e3a89b213a11",
    "state": "RELEASED",
    "released_timestamp": "2024-02-27T15:47:17.076850+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, series, dropna=True):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****

    # write your function code here.

    index_series = pd.Series(series.index, index=series.index)

    if isinstance(series.index, pd.DatetimeIndex):
        h = index_series.diff().dt.total_seconds()
    else:
        h = index_series.diff()

    difference_quotients = series.diff() / h

    if dropna:
        return {"difference_quotients": difference_quotients.dropna()}

    return {"difference_quotients": difference_quotients}


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "series",
            "filters": {
                "value": '{\n    "2020-01-01T01:15:27.000Z": 42.2,\n    "2020-01-03T08:20:03.000Z": 18.7,\n    "2020-01-03T08:20:04.000Z": 25.9\n}'
            },
        },
        {
            "workflow_input_name": "dropna",
            "use_default_value": True,
            "filters": {"value": "True"},
        },
    ]
}
RELEASE_WIRING = {
    "input_wirings": [
        {
            "workflow_input_name": "series",
            "filters": {
                "value": '{\n    "2020-01-01T01:15:27.000Z": 42.2,\n    "2020-01-03T08:20:03.000Z": 18.7,\n    "2020-01-03T08:20:04.000Z": 25.9\n}'
            },
        },
        {
            "workflow_input_name": "dropna",
            "use_default_value": True,
            "filters": {"value": "True"},
        },
    ]
}

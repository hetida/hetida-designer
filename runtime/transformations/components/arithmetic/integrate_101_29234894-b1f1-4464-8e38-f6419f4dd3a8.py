"""Documentation for Integrate

# Integrate

## Description
This component integrates a Pandas Series.

## Inputs
* **data** (Pandas Series): The indices must be numeric or datetimes, the values must be numeric.

## Outputs
* **integral** (Float): The integral of data.

## Details
This component calculates the integral according to the trapezoidal rule. Therefore, the component ignores NaN values and uses a version of data, sorted by its index.
If the indices are datetimes, their distances are expressed in seconds.

## Examples
The json input of a typical call of this component with a Pandas Series is
```
{
        "data": {
                                "2019-08-01T15:20:10": 1.7,
                                "2019-08-01T15:20:20": null,
                                "2019-08-01T15:20:25": 0.3,
                                "2019-08-01T15:20:30": 0.5
        }
}
```
The expected output is
```
        "integral": 17
```
"""

import pandas as pd
import datetime
from scipy import integrate

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "data": {"data_type": "SERIES"},
    },
    "outputs": {
        "integral": {"data_type": "FLOAT"},
    },
    "name": "Integrate",
    "category": "Arithmetic",
    "description": "Calculates the integral of a Series",
    "version_tag": "1.0.1",
    "id": "29234894-b1f1-4464-8e38-f6419f4dd3a8",
    "revision_group_id": "dd73bac2-cd9d-61c5-0aec-9dec6f337516",
    "state": "RELEASED",
    "released_timestamp": "2025-06-25T09:25:36.593346+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, data):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.

    if (data.size) < 2:
        raise ValueError("size of data must be at least 2")

    data_dropna = data.dropna()

    if pd.api.types.is_numeric_dtype(data_dropna.index.dtype):
        data_dropna = data_dropna.sort_index()
        x = data_dropna.index

    else:
        try:
            data_dropna.index = pd.to_datetime(data_dropna.index)
        except (TypeError, ValueError):
            raise TypeError("indices of data must be numeric or datetime")
        data_dropna = data_dropna.sort_index()
        x = (data_dropna.index - data_dropna.index[0]).total_seconds()

    y = data_dropna.values

    return {"integral": integrate.trapezoid(y, x)}


TEST_WIRING_FROM_PY_FILE_IMPORT = {}
RELEASE_WIRING = {}

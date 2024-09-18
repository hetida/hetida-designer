"""Documentation for Eval Expression On Series

# Eval Expression On Series
## Description
Evaluates a string expression on a pandas Series which can be referred as `x`.


## Inputs

* **series** (SERIES): A pandas Series object.
* **expression** (STRING): A Python expression

## Outputs
* **result_series (SERIES)**: The resulting Pandas Series object.

## Details
* Evaluates an expression provided as string according to https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.eval.html. The series object is available as variable `x`.

## Examples

On a series `pd.Series([1,2,3,4])` the expression `x>2` results in a `pd.Series([False, False, True, True])`.
"""  # noqa: E501

# add your own imports here, e.g.
import pandas as pd

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "series": {"data_type": "SERIES"},
        "expression": {"data_type": "STRING"},
    },
    "outputs": {
        "result_series": {"data_type": "SERIES"},
    },
    "name": "Eval Expression On Series",
    "category": "Filters",
    "description": "Evaluates a string expression on a series",
    "version_tag": "1.0.0",
    "id": "f70f53c2-645e-4bfa-91e1-a3ecbd56465a",
    "revision_group_id": "fae04080-abff-46e4-a964-a118640e95f7",
    "state": "RELEASED",
    "released_timestamp": "2024-02-22T13:09:42.771466+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, series, expression):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    x = series  # noqa: F841
    return {"result_series": pd.eval(expression)}


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "series",
            "filters": {
                "value": '{\n    "2020-01-01T01:15:27.000Z": 42.2,\n    "2020-01-03T08:20:03.000Z": 18.7,\n    "2020-01-03T08:20:04.000Z": 25.9\n}'
            },
        },
        {"workflow_input_name": "expression", "filters": {"value": "x > 42"}},
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
        {"workflow_input_name": "expression", "filters": {"value": "x > 42"}},
    ]
}

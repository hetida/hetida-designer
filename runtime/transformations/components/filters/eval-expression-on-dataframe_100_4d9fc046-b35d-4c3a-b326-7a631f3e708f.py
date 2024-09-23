"""Documentation for Eval Expression On DataFrame

# Eval Expression On DataFrame
## Description
Evaluates a string expression on a pandas DataFrame.


## Inputs

* **series** (DATAFRAME): A pandas DataFrame object.
* **expression** (STRING): A Python expression

## Outputs
* **result_series (SERIES)**: The resulting Pandas Series object.

## Details
* Evaluates an expression provided as string according to https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.eval.html.

## Examples

On a DataFrame `pd.DataFrame({"A": [1,2,3,4], "B": [2,2,2,2]})` the expression `A + B` results in a `pd.Series([3,4,5,6])`.
"""  # noqa: E501

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "dataframe": {"data_type": "DATAFRAME"},
        "expression": {"data_type": "STRING"},
    },
    "outputs": {
        "result_series": {"data_type": "SERIES"},
    },
    "name": "Eval Expression On DataFrame",
    "category": "Filters",
    "description": "Evaluates a string expression on a DataFrame",
    "version_tag": "1.0.0",
    "id": "4d9fc046-b35d-4c3a-b326-7a631f3e708f",
    "revision_group_id": "87db5d56-9f24-436f-ae8e-4d0a52607004",
    "state": "RELEASED",
    "released_timestamp": "2024-02-22T13:22:50.060356+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, dataframe, expression):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    return {"result_series": dataframe.eval(expression)}


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "dataframe",
            "filters": {
                "value": '{\n    "A": {\n        "2019-08-01T15:45:36.000Z": 1,\n        "2019-08-02T11:33:41.000Z": 2\n    },\n    "B": {\n        "2019-08-01T15:45:36.000Z": 1.3,\n        "2019-08-02T11:33:41.000Z": 2.8\n    }\n}'
            },
        },
        {
            "workflow_input_name": "expression",
            "filters": {"value": "A > 1.8 and B > 2.5"},
        },
    ]
}
RELEASE_WIRING = {
    "input_wirings": [
        {
            "workflow_input_name": "dataframe",
            "filters": {
                "value": '{\n    "A": {\n        "2019-08-01T15:45:36.000Z": 1,\n        "2019-08-02T11:33:41.000Z": 2\n    },\n    "B": {\n        "2019-08-01T15:45:36.000Z": 1.3,\n        "2019-08-02T11:33:41.000Z": 2.8\n    }\n}'
            },
        },
        {
            "workflow_input_name": "expression",
            "filters": {"value": "A > 1.8 and B > 2.5"},
        },
    ]
}

"""Documentation for Convert SingleTSFrame to DataFrame

# Convert SingleTSFrame to DataFrame

## Description
Convert a SingleTSFrame into a DataFrame with the timestamps as index.

## Inputs
* **singletsframe** (SingleTSFrame): The input SingleTSFrame.

## Outputs
* **dataframe** (Pandas DataFrame): The output DataFrame with the timestamps as index and one column per value dimension.

## Details
A SINGLETSFRAME already is in "wide" format with respect to its value dimensions: every column besides "timestamp" is a value dimension. Converting it to a DataFrame therefore just moves the "timestamp" column into the index.

The attributes (`.attrs`) are carried over unchanged.

## Examples
The json input of a typical call of this component is
```
{
    "singletsframe": {
        "value": [1.0, 1.2],
        "state": ["ok", "suspicious"],
        "timestamp": [
            "2019-08-01T15:42:36.000Z",
            "2019-08-01T15:45:36.000Z"
        ]
    }
}
```
"""

import copy

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "singletsframe": {"data_type": "SINGLETSFRAME"},
    },
    "outputs": {
        "dataframe": {"data_type": "DATAFRAME"},
    },
    "name": "Convert SingleTSFrame to DataFrame",
    "category": "Connectors",
    "description": "Convert a SingleTSFrame into a DataFrame with the timestamps as index",
    "version_tag": "1.0.0",
    "id": "7b95ac28-1df1-4611-afcf-599b2a0d8725",
    "revision_group_id": "30982eb7-a66b-404f-8737-c509949ef027",
    "state": "RELEASED",
    "released_timestamp": "2026-08-05T10:00:00+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, singletsframe):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    dataframe = singletsframe.set_index("timestamp").sort_index()
    dataframe.attrs = copy.deepcopy(singletsframe.attrs) if singletsframe.attrs else {}

    return {"dataframe": dataframe}


# Testing
try:
    import pandas as pd
    import pytest
except ImportError:
    pass
else:

    @pytest.fixture
    def singletsframe():
        singletsframe = pd.DataFrame(
            {
                "timestamp": pd.to_datetime(
                    ["2019-08-01T15:45:36.000Z", "2019-08-01T15:42:36.000Z"], utc=True
                ),
                "value": [1.2, 1.0],
                "state": ["ok", "suspicious"],
            }
        )
        singletsframe.attrs = {"dataset_metadata": {"single_metric": "abc.temp"}}
        return singletsframe

    def test_timestamp_becomes_index(singletsframe):
        dataframe = main(singletsframe=singletsframe)["dataframe"]

        assert dataframe.index.name == "timestamp"  # noqa: S101
        assert list(dataframe.columns) == ["value", "state"]  # noqa: S101
        assert list(dataframe["value"]) == [1.0, 1.2]  # noqa: S101
        assert str(dataframe.index.tz) == "UTC"  # noqa: S101
        assert dataframe.attrs["dataset_metadata"]["single_metric"] == "abc.temp"  # noqa: S101


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "singletsframe",
            "filters": {
                "value": '{\n    "value": [\n        1,\n        1.2,\n        0.5\n    ],\n    "timestamp": [\n        "2019-08-01T15:42:36.000Z",\n        "2019-08-01T15:45:36.000Z",\n        "2019-08-01T15:48:36.000Z"\n    ]\n}'
            },
        }
    ]
}
RELEASE_WIRING = {
    "input_wirings": [
        {
            "workflow_input_name": "singletsframe",
            "filters": {
                "value": '{\n    "value": [\n        1,\n        1.2,\n        0.5\n    ],\n    "timestamp": [\n        "2019-08-01T15:42:36.000Z",\n        "2019-08-01T15:45:36.000Z",\n        "2019-08-01T15:48:36.000Z"\n    ]\n}'
            },
        }
    ]
}

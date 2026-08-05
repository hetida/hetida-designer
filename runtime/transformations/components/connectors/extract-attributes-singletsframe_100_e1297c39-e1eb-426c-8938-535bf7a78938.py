"""Documentation for Extract Attributes (SingleTSFrame)

# Extract Attributes (SingleTSFrame)

## Description
Extract attributes from a SingleTSFrame.

## Inputs
* **singletsframe** (SingleTSFrame): The input SingleTSFrame.

## Outputs
* **attributes** (Any): A dictionary containing the attributes of the singletsframe.

## Details

**Note:** When wired to a generic REST adapter, attributes are expected to be sent base64-encoded with the key "Data-Attributes" in the header. To process the attributes, the adapter should be implemented accordingly.
"""

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "singletsframe": {"data_type": "SINGLETSFRAME"},
    },
    "outputs": {
        "attributes": {"data_type": "ANY"},
    },
    "name": "Extract Attributes (SingleTSFrame)",
    "category": "Connectors",
    "description": "Extract attributes from a singletsframe",
    "version_tag": "1.0.0",
    "id": "e1297c39-e1eb-426c-8938-535bf7a78938",
    "revision_group_id": "444a0abd-fab9-46f7-b719-11e9c93d4c61",
    "state": "RELEASED",
    "released_timestamp": "2026-08-05T10:00:00+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, singletsframe):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.

    return {"attributes": singletsframe.attrs}


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "singletsframe",
            "filters": {
                "value": '{\n    "__hd_wrapped_data_object__": "DATAFRAME",\n    "__metadata__": {\n        "dataset_metadata": {\n            "single_metric": "abc.temp"\n        }\n    },\n    "__data__": {\n        "value": {\n            "0": 1,\n            "1": 1.2,\n            "2": 0.5\n        },\n        "timestamp": {\n            "0": "2019-08-01T15:42:36.000Z",\n            "1": "2019-08-01T15:45:36.000Z",\n            "2": "2019-08-01T15:48:36.000Z"\n        }\n    }\n}'
            },
        }
    ]
}
RELEASE_WIRING = {
    "input_wirings": [
        {
            "workflow_input_name": "singletsframe",
            "filters": {
                "value": '{\n    "__hd_wrapped_data_object__": "DATAFRAME",\n    "__metadata__": {\n        "dataset_metadata": {\n            "single_metric": "abc.temp"\n        }\n    },\n    "__data__": {\n        "value": {\n            "0": 1,\n            "1": 1.2,\n            "2": 0.5\n        },\n        "timestamp": {\n            "0": "2019-08-01T15:42:36.000Z",\n            "1": "2019-08-01T15:45:36.000Z",\n            "2": "2019-08-01T15:48:36.000Z"\n        }\n    }\n}'
            },
        }
    ]
}

"""Documentation for Add/Update Attributes (SingleTSFrame)

# Add/Update Attributes (SingleTSFrame)

## Description
Add attributes to a SingleTSFrame or update attributes of a SingleTSFrame.
If you wish to attach metadata to a SingleTSFrame, please follow the conventions outlined in the [documentation](https://hetida.github.io/hetida-designer/user_guide/attached_metadata/).

## Inputs
* **singletsframe** (SingleTSFrame): The input SingleTSFrame.
* **attributes** (Any): A dictionary with string keys to be added to the input SingleTSFrame.

## Outputs
* **singletsframe** (SingleTSFrame): The input singletsframe with added attributes.

## Details
Adds attributes to a SingleTSFrame. Adding an attribute with a key, that is already included in the attributes of the singletsframe, will update the corresponding value.

**Note:** Selecting "Only Output" for the output singletsframe means that it is wired to the "direct provisioning" adapter, which sends the data as a stream of records in the response to be displayed in the browser window, but not the attributes. To access the attributes, use the "Extract Attributes (SingleTSFrame)" component.

**Note:** When wired to a generic REST adapter, the attributes are sent base64-encoded with the key "Data-Attributes" in the header. To process the attributes, the adapter should be implemented accordingly.
"""

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "singletsframe": {"data_type": "SINGLETSFRAME"},
        "attributes": {"data_type": "ANY"},
    },
    "outputs": {
        "singletsframe": {"data_type": "SINGLETSFRAME"},
    },
    "name": "Add/Update Attributes (SingleTSFrame)",
    "category": "Connectors",
    "description": "Add attributes to a singletsframe or update attributes of a singletsframe",
    "version_tag": "1.0.0",
    "id": "feeea3fc-f676-4a77-b88d-0ed016fed11f",
    "revision_group_id": "ac47bf43-14e9-4832-bf6a-9c4a56f1b2a8",
    "state": "RELEASED",
    "released_timestamp": "2026-08-05T10:00:00+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, singletsframe, attributes):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    singletsframe.attrs.update(attributes)

    return {"singletsframe": singletsframe}


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "singletsframe",
            "filters": {
                "value": '{\n    "value": [\n        1,\n        1.2,\n        0.5\n    ],\n    "timestamp": [\n        "2019-08-01T15:42:36.000Z",\n        "2019-08-01T15:45:36.000Z",\n        "2019-08-01T15:48:36.000Z"\n    ]\n}'
            },
        },
        {
            "workflow_input_name": "attributes",
            "filters": {"value": '{\n    "a": true,\n    "b": 31.56\n}'},
        },
    ]
}
RELEASE_WIRING = {}

"""Documentation for Pass Through

# Pass Through

## Description
This component just passes data through.

## Inputs
* **input** (Any): The input.

## Outputs
* **output** (Any): The output.

## Details
This component just passes data through. It can be used to map one dynamic workflow input to multiple component inputs.
"""

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "input": {"data_type": "ANY"},
    },
    "outputs": {
        "output": {"data_type": "ANY"},
    },
    "name": "Pass Through NEW",
    "category": "Connectors",
    "description": "Just outputs its input value",
    "version_tag": "1.0.0",
    "id": "1946d5f8-44a8-724c-176f-123456aaaaa1",
    "revision_group_id": "2946d5f8-44a8-724c-176f-123456aaaaa1",
    "state": "DISABLED",
    "released_timestamp": "2025-06-25T17:33:34.387537+00:00",
    "disabled_timestamp": "2026-06-25T17:33:34.387537+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, input):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.

    return {"output": input}


TEST_WIRING_FROM_PY_FILE_IMPORT = {}
RELEASE_WIRING = {}
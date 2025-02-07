"""Documentation for Pass Through (String)

# Pass Through (String)

## Description
This component just passes data through.

## Inputs
* **input** (String): The input String.

## Outputs
* **output** (String): The output String.

## Details
This component just passes data through. It can be used to map one dynamic workflow input to multiple component inputs.
"""

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "input": {"data_type": "STRING"},
    },
    "outputs": {
        "output": {"data_type": "STRING"},
    },
    "name": "Pass Through (String)",
    "category": "Connectors",
    "description": "Just outputs its input value",
    "version_tag": "1.0.0",
    "id": "2b1b474f-ddf5-1f4d-fec4-17ef9122112b",
    "revision_group_id": "2b1b474f-ddf5-1f4d-fec4-17ef9122112b",
    "state": "RELEASED",
    "released_timestamp": "2022-02-10T03:33:33.917427+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, input):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.

    return {"output": input}


TEST_WIRING_FROM_PY_FILE_IMPORT = {}
RELEASE_WIRING = {}

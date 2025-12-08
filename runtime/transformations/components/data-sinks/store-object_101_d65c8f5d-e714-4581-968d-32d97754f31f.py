"""Documentation for Store Object

Documentation for Store Object

# Store an Object in the object Repository

## Description
Serialize an Object and store it in the object Repository.

## Inputs
* **name** (String): The name for the Object.
* **tag** (String): The tag for the Object.
* **data** (Any): The object to store.

## Outputs

## Description
Hetida Designer comes with a simple object store to allow serialization and persistence of Python objects between Workflows and Workflow Executions. A typical use case is storing of a trained machine learning model in a training workflow and loading it in a prediction workflow.

Technically joblib is used for serialization in order to efficiently store numpy arrays and Pandas objects.

The serialized object is stored using the name and a tag. It can be retrieved using the provided loading functionality with the same name and tag combination. Additionally there is a magic "latest" tag which retrieves the last stored object with that name.
"""

# add your own imports here
import hetdesrun.serialization

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "name": {"data_type": "STRING"},
        "tag": {"data_type": "STRING"},
        "data": {"data_type": "ANY"},
    },
    "outputs": {},
    "name": "Store Object",
    "category": "Data Sinks",
    "description": "Serialize an Object and store it in the object Repository",
    "version_tag": "1.0.1",
    "id": "d65c8f5d-e714-4581-968d-32d97754f31f",
    "revision_group_id": "26d99461-38a9-5e92-df4f-d0fd2752879e",
    "state": "RELEASED",
    "released_timestamp": "2025-12-08T15:50:55.349435+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, name, tag, data):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    hetdesrun.serialization.dump_obj(data, name, tag)
    return {}


TEST_WIRING_FROM_PY_FILE_IMPORT = {}
RELEASE_WIRING = {}

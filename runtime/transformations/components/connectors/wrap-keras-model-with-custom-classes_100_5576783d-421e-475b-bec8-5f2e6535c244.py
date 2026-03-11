"""Documentation for Wrap Keras Model with Custom Classes

# Wrap Keras Model with Custom Classes

## Description
Since the Keras load_model function requires passing a dictionary containing all user-defined classes, these classes must be stored along with the model so that they can be extracted by the Blob Storage Adapter at loading time.
This component combines the model with such a dictionary of user-defined classes in a wrapper object and enables the Blob Storage Adapter to properly store and save models with custom classes.

## Inputs
* **model** (Tensorflow Keras Model): Trained model to be saved
* **custom_objects** (Dictionary): Dictionary with all custom classes used in the model. Each key must be the name of the respective class.

## Outputs
* **wrapped_model_with_custom_objects** (WrappedModelWithCustomObjects): Entity of the class WrappedModelWithCustomObjects which contains the model and the custom objects.

## Details
This component cannot be executed with manual input. It is intended to be used within a workflow.
"""

from hdutils import WrappedModelWithCustomObjects

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "model": {"data_type": "ANY"},
        "custom_objects": {"data_type": "ANY"},
    },
    "outputs": {
        "wrapped_model_with_custom_objects": {"data_type": "ANY"},
    },
    "name": "Wrap Keras Model with Custom Classes",
    "category": "Connectors",
    "description": "Wrap tensorflow keras model with custom classes",
    "version_tag": "1.0.0",
    "id": "5576783d-421e-475b-bec8-5f2e6535c244",
    "revision_group_id": "e3a1e276-2aa1-460c-bbc9-c73fa88db2ce",
    "state": "RELEASED",
    "released_timestamp": "2023-04-05T17:11:58.759314+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, model, custom_objects):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    return {
        "wrapped_model_with_custom_objects": WrappedModelWithCustomObjects(
            model=model, custom_objects=custom_objects
        )
    }


TEST_WIRING_FROM_PY_FILE_IMPORT = {}
RELEASE_WIRING = {}

"""Documentation for Test Keras Model

# Test Keras Model on MNIST dataset

## Description
This component is used to demonstrates how to load a Tensorflow Keras model with custom classes in the Blob Storage Adapter.
As an example a simple Tensorflow Keras model with a custom AntirectificationLayer is tested on the Keras MNIST dataset based on the keras tutorial: https://keras.io/examples/keras_recipes/antirectifier/#simple-custom-layer-example-antirectifier.

## Inputs
* **trained_model** (Tensorflow Keras Model): Trained model, e.g. from the component "Train Keras Model with Custom Layer" or from a stored object.

## Outputs
* **metrics** (Dict): Dictionary which contains the metrics of the trained model.

## Details

This component cannot be executed with manual input. It is intended to be used with stored objects or within a workflow.
"""

import contextlib

with contextlib.suppress(ModuleNotFoundError):
    import tensorflow as tf

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "trained_model": {"data_type": "ANY"},
    },
    "outputs": {
        "metrics": {"data_type": "ANY"},
    },
    "name": "Test Keras Model",
    "category": "Examples",
    "description": "Test tensorflow keras model with custom AntirectifierLayer",
    "version_tag": "1.0.0",
    "id": "0c4f85b7-1cf1-48be-8cfb-19f228c1f88e",
    "revision_group_id": "5673a16b-7179-48fc-9472-ab6a169896ab",
    "state": "RELEASED",
    "released_timestamp": "2023-04-05T16:26:28.231707+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, trained_model):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****

    # The data, split between train and test sets
    _, (x_test, y_test) = tf.keras.datasets.mnist.load_data()

    # The data, split between train and test sets
    x_test = x_test.reshape(-1, 784)
    x_test = x_test.astype("float32")
    x_test /= 255

    metrics_values = trained_model.evaluate(x_test, y_test)
    metrics_names = trained_model.metrics_names

    metrics = {}
    for index in range(len(metrics_names)):
        metrics[metrics_names[index]] = metrics_values[index]

    return {"metrics": metrics}


TEST_WIRING_FROM_PY_FILE_IMPORT = {}
RELEASE_WIRING = {}

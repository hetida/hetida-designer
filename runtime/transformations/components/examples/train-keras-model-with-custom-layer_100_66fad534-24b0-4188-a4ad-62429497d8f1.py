"""Documentation for Train Keras Model with Custom Layer

# Train Keras Model with Custom Layer

## Description
This component is used to demonstrates how to persist a Tensorflow Keras model with custom classes in the Blob Storage Adapter.
As an example a simple Tensorflow Keras model with a custom AntirectificationLayer is trained on the Keras MNIST dataset based on the keras tutorial: https://keras.io/examples/keras_recipes/antirectifier/#simple-custom-layer-example-antirectifier.

## Inputs
* **AntirectifierLayer** (Tensorflow Keras Layer): AntirectifierLayer class.

## Outputs
* **trained_model** (Tensorflow Keras Model): Trained model.

## Details

This component cannot be executed with manual input. It is intended to be used within a workflow.
"""

import contextlib

# Tensorflow currently not available in standard designer version.
# Example exists to show how to use keras models with custom layers without the component adapter and to make pytest runnable on all tranformation.
with contextlib.suppress(ModuleNotFoundError):
    import tensorflow as tf


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "AntirectifierLayer": {"data_type": "ANY"},
    },
    "outputs": {
        "trained_model": {"data_type": "ANY"},
    },
    "name": "Train Keras Model with Custom Layer",
    "category": "Examples",
    "description": "Train tensorflow keras model with custom AntirectifierLayer",
    "version_tag": "1.0.0",
    "id": "66fad534-24b0-4188-a4ad-62429497d8f1",
    "revision_group_id": "1fb6b27d-53b6-4442-98d9-e053d07aa8a2",
    "state": "RELEASED",
    "released_timestamp": "2023-04-05T16:50:34.641245+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, AntirectifierLayer):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****

    # Training parameters
    batch_size = 128
    epochs = 20

    # The data, split between train and test sets
    (x_train, y_train), _ = tf.keras.datasets.mnist.load_data()

    x_train = x_train.reshape(-1, 784)
    x_train = x_train.astype("float32")
    x_train /= 255

    # Build the model
    model = tf.keras.Sequential(
        [
            tf.keras.Input(shape=(784,)),
            tf.keras.layers.Dense(256),
            AntirectifierLayer(),
            tf.keras.layers.Dense(256),
            AntirectifierLayer(),
            tf.keras.layers.Dropout(0.5),
            tf.keras.layers.Dense(10),
        ]
    )

    # Compile the model
    model.compile(
        loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
        optimizer=tf.keras.optimizers.RMSprop(),
        metrics=[tf.keras.metrics.SparseCategoricalAccuracy()],
    )

    # Train the model
    model.fit(x_train, y_train, batch_size=batch_size, epochs=epochs, validation_split=0.15)

    return {"trained_model": model}


TEST_WIRING_FROM_PY_FILE_IMPORT = {}
RELEASE_WIRING = {}

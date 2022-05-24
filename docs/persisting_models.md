# Persisting ML / AI Models

After training a model, it is desirable to have a way to persist the model for future use without having to train it again.

hetida designer provides two options to persist your models, suitable for different occasions.

The simpler option is to use the basic components provided, the more sophisticated option is to write a suitable general custom adapter.

## Persisting via Components

In order to persist models, the `Store Object` component is provided in the category `Data Sinks`. In addition to the object to be stored, this component expects a `name` string and a `tag` string as inputs, which in combination are supposed to uniquely identify the respective object. The name and the tag are used to determine the location of the serialized object file. The tag must not be "latest" because that is used internally and has a specific meaning.

In order to load a persisted model, the `Load Object` component is provided in the category `Data Sources`. This component takes a `name` string and a `tag` string as input and returns the object stored under that name and tag.

The directory where the serialized object files are stored within the container is defined by the `MODEL_REPO_PATH` environment variable, which by default is "/mnt/obj_repo".

The `dump_obj` and `load_obj` functions used in these components are based on the `dump` and `load` functions of the [`joblib` module](https://joblib.readthedocs.io/en/latest/persistence.html). These are again based on the corresponding functions of the pickle module from the Python standard library, and thus have the same **security issue** that arbitrary code can be executed when loading a file from an unknown source.

Compared to the pickle functions, the joblib functions have the advantage that they can efficiently work with arbitrary Python objects containing large data, in particular large numpy arrays.

## Persisting via a General Custom Adapter

Writing your own [General Custom Adapter](./adapter_system/general_custom_adapters/instructions.md) has the advantage that you can convert the model to a format of your choice, such as [ONNX](https://onnx.ai/), and transfer the model directly to the sources (or from the sinks) you want.

To get started, you can checkout the [description](./adapter_system/local_file_adapter.md) and implementation of the built-in Local File Adapter, which is a general custom adapter.

In case additional Python libraries such as [`onnx`](https://github.com/onnx/onnx), [`tensorflow-onnx`](https://github.com/onnx/tensorflow-onnx), [`onnx-tensorflow`](https://github.com/onnx/onnx-tensorflow), or [`sklearn-onnx`](https://github.com/onnx/sklearn-onnx) are needed, just follow the instructions on how to add [Custom Python Dependencies](./custom_python_dependencies.md) to your runtime Docker container.
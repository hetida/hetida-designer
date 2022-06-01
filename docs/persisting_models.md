# Persisting ML / AI Models

After training a model, it is desirable to have a way to persist the model for future inference from within another worklfow.

hetida designer provides two options to persist your models, suitable for different occasions.

A simple option for development purposes is to use basic components for serializing objects to disk. However, for production environments it is recommended to write a suitable general custom adapter.

## Persisting and Loading from within Workflows via Components

In order to persist models, the `Store Object` component is provided in the category `Data Sinks`. In addition to the object to be stored, this component expects a `name` string and a `tag` string as inputs, which in combination should uniquely identify the respective object. The name and the tag are used to determine the location of the serialized object file. The tag must not be "latest" because that is used internally and has a specific meaning.

In order to load a persisted model, the `Load Object` component is provided in the category `Data Sources`. This component takes a `name` string and a `tag` string as input and returns the object stored under that name and tag.

The directory where the serialized object files are stored within the container is defined by the `MODEL_REPO_PATH` environment variable, which by default is "/mnt/obj_repo". To make this persistent a volume needs to be mounted there, like in the default docker-compose setup (see `docker-compose.yml`).

The `dump_obj` and `load_obj` functions used in these components are based on the `dump` and `load` functions of the [`joblib` module](https://joblib.readthedocs.io/en/latest/persistence.html). Compared to the pickle functions, the joblib functions have the advantage that they can efficiently work with Python objects containing numpy arrays.
Note that deserializing and executing code is a security risk - you should only load objects from trusted sources.


## Persisting and Loading via a General Custom Adapter

Writing your own [General Custom Adapter](./adapter_system/general_custom_adapters/instructions.md) has the following advantages

* Keeps your workflow modular and reproducible in accordance with hetida designers strict separation of analytics and data ingestion/egestion (Adapter system, wirings etc.). We strongly recommend to follow this approach for production scenarios!
* You may choose a format of your choice, such as [ONNX](https://onnx.ai/) which allows integration into other solutions, even non-Python-based ones.

To get started, besides the [general custom adaper documentation](./adapter_system/general_custom_adapters/instructions.md) you can checkout the [description](./adapter_system/local_file_adapter.md) and implementation of the built-in Local File Adapter, which is a general custom adapter.

In case additional Python libraries such as [`onnx`](https://github.com/onnx/onnx), [`tensorflow-onnx`](https://github.com/onnx/tensorflow-onnx), [`onnx-tensorflow`](https://github.com/onnx/onnx-tensorflow), or [`sklearn-onnx`](https://github.com/onnx/sklearn-onnx) are needed, just follow the instructions on how to add [Custom Python Dependencies](./custom_python_dependencies.md) to your runtime Docker container.
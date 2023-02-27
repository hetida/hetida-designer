# Persisting ML / AI Models

## Overview
After training a statistical / machine learning model, it is desirable to have a way to persist the model for future inference.

The recommended approach is to use [general custom adapters](./adapter_system/general_custom_adapters/instructions.md) to serialize / deserialize the model object as follows:

1. Run a training workflow which outputs the trained model to an ANY type output which is wired to a general custom adapter sink.
2. Employ a fitting inference workflow loading the model into an ANY input from the same general custom adapter.

General custom adapters are preferable here over generic rest adapters since read/write operations run directly from within the runtime Python code. This avoids having to transport potentially large amounts of binary data via http.

hetida designer is equipped with two built-in such general custom adapters suitable for the task of persisiting arbitrary (binary) Python objects. Both use Python's built-in pickle module for serialization / deserialization:

* the [local file adapter](adapter_system/local_file_adapter.md)
* the blob storage adapter (for S3 compatible storage) (TODO)

Apart from these two, you can write your completely own general custom adapters tailored to your specific needs and persistence backends.

Another solution consist of using serialization/deserialization components directly from within the workflows. This is not recommended as its thwarts hetida designer's principles like reproducibility and separation of analytics from data in/egestion. Nevertheless it is explained below.

**General warning on deserialization**: Deserializing executes code and therefore is a security risk - you should only load objects from trusted sources!

### Note on model management
As well as it does not provide scheduling, hetida designer is not a model management framework. It treats models as data that is put out from workflows and read into workflow inputs.

You can of course establish analytical steps of model management like for example automatic performance measuring / evaluation as part of hetida designer workflows.

But the "management" part, i.e. selecting the current/prod model, fallback procedures on declining performance and so on has to be implemented around the systems which invoke hetida designer from the outside.

### Note on custom classes
(TODO)
## Persisting and Loading via General Custom Adapter
### Built in general custom adapters

#### local file adapter
The [local file adapter](adapter_system/local_file_adapter.md) supports pickling objects from ANY typed outputs to disk and loading them into ANY type inputs.

#### blob storage adapter
(TODO)
### Writing your own general custom adapter
If the builtin adapters are not suitable for your scenario, writing your own [General Custom Adapter](./adapter_system/general_custom_adapters/instructions.md) is the recommended way for persisting and loading models. It has the following advantages specific to model persistence:

* Keeps your workflow modular and reproducible in accordance with hetida designers separation of analytics and data ingestion/egestion (Adapter system, wirings etc.). We strongly recommend to follow this approach for production scenarios over for example storing/loading from inside workflow operators as described below!
* Faster and more efficient when handling large models as binary blobs compared to generic rest adapters.
* You may choose a format of your choice, such as [ONNX](https://onnx.ai/) which allows integration into other solutions, even non-Python-based ones.

To get started, besides the [general custom adaper documentation](./adapter_system/general_custom_adapters/instructions.md) you can checkout the [description](./adapter_system/local_file_adapter.md) and implementation of the built-in local file adapter, which is a general custom adapter.

You typically will use the ANY type for arbitrary models / Python objects.

In case additional Python libraries such as [`onnx`](https://github.com/onnx/onnx), [`tensorflow-onnx`](https://github.com/onnx/tensorflow-onnx), [`onnx-tensorflow`](https://github.com/onnx/onnx-tensorflow), or [`sklearn-onnx`](https://github.com/onnx/sklearn-onnx) are needed, just follow the instructions on how to add [Custom Python Dependencies](./custom_python_dependencies.md) to your runtime Docker container.


## Persisting and Loading from within Workflows via Components
A simple option for development purposes is to use basic components for serializing objects to disk. 

**WARNING:** We only recommend this for early development / experimentation as its counteracts basic hetida designer principles. For production environments it is higly recommended to use or write a suitable general custom adapter.

In order to persist objects from within workflows, the `Store Object` component is provided in the category `Data Sinks`. In addition to the object to be stored, this component expects a `name` string and a `tag` string as inputs, which in combination should uniquely identify the respective object. The name and the tag are used to determine the location of the serialized object file. The tag must not be "latest" because that is used internally and has a specific meaning.

In order to load a persisted object, the `Load Object` component is provided in the category `Data Sources`. This component takes a `name` string and a `tag` string as input and returns the object stored under that name and tag.

The directory where the serialized object files are stored within the container is defined by the `MODEL_REPO_PATH` environment variable, which by default is "/mnt/obj_repo". To make this persistent a volume needs to be mounted there, like in the default docker-compose setup (see `docker-compose.yml`).

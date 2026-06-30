# Persisting ML / AI Models

## Overview

After training a statistical / machine learning model, it is desirable to have a way to persist the model for future inference.

The recommended approach is to use a general custom adapter (e.g. the builtin [blob storage adapter](../integration_guide/adapter_system/builtin_adapters/blob_storage_adapter.md)) to serialize / deserialize the model object as follows:

1. Run a training workflow which outputs the trained model to an ANY type output which is wired to a general custom adapter sink.
2. Employ a fitting inference workflow loading the trained model into an ANY input from the same general custom adapter.

General custom adapters are preferable here over generic rest adapters since read/write operations run directly from within the runtime Python code. This avoids having to transport potentially large amounts of binary data via http in json format.

hetida designer is equipped with several built-in such general custom adapters suitable for the task of persisiting arbitrary (binary) Python objects. The following use Python's built-in pickle module for serialization / deserialization:

- the [local file adapter](../integration_guide/adapter_system/builtin_adapters/local_file_adapter.md)
- the [blob storage adapter](../integration_guide/adapter_system/builtin_adapters/blob_storage_adapter.md) (for S3 compatible storage)

The [component adapter](../integration_guide/adapter_system/builtin_adapters/component_adapter.md) allows to write components using arbitrary Python code that act as sources / sinks. This allows for easy custom / ad-hoc integration of additional storage solutions or special formats.

Apart from these, you can write your completely own [general custom adapter](../integration_guide/adapter_system/custom_adapters/general_custom_adapter.md) tailored to your specific needs and persistence backends.

!!! warning
Using serialization/deserialization components directly from within the workflows is possible but not recommended as its thwarts hetida designer's principles like reproducibility and separation of analytics from data in/egestion. The recommendation is to simply use such components via the component adapter instead.

**:warning: General warnings on deserialization :warning:**:

- Deserializing executes code and therefore is a security risk - you should only load objects from trusted sources!
- If code or Python environments change, deserialization may fail at some point. See [notes on deserialization pitfalls](./repr_pitfalls.md) for details. You may prefer code-invariant serialization techniques like [ONNX](https://onnx.ai/) in some cases.

### Model Management

hetida designer is not a model management/ experiment management framework. It simply treats models as data that is put out from workflows and read into workflow inputs.

You can of course establish the _analytical_ steps of model management like for example automatic performance measuring / evaluation as part of hetida designer workflows.

But the _management_ part, i.e. selecting the current/prod model based on evaluation results, fallback procedures on declining performance and so on has to be implemented around the systems which [invoke](../integration_guide/trafo_exec_guide/trafo_execution_overview.md) hetida designer from the outside.

### Custom Classes

You may [import components in other components](./component_writing/component_import.md), which in particular allows to import classes from other components. This enables proper deserialization of trained models using custom classes: Just import the component containing the class definition in an inference component.

## Persisting and Loading via General Custom Adapter

### Built in general custom adapters

#### Mounted Files Adapter

The [Mounted Files Adapter](../integration_guide/adapter_system/builtin_adapters/local_file_adapter.md) supports pickling objects from `ANY` typed outputs to a mounted volume/disk and loading them into `ANY` type inputs.

#### Blob Storage Adapter

The [Blob Storage Adapter](../integration_guide/adapter_system/builtin_adapters/blob_storage_adapter.md) supports pickling objects from `ANY` typed outputs to a mounted Blob storage and loading them into `ANY` type inputs via the S3 standard.

#### Component Adapter

The [Component Adapter](../integration_guide/adapter_system/builtin_adapters/component_adapter.md) is the most customizable solution apart from writing your own adapter. It allows to write custom Python code for accessing 3rd party persistence solutions / storage. Typically you would use `ANY` as type for models.

### Writing your own general custom adapter

If the builtin adapters are not suitable for your scenario, writing your own [General Custom Adapter](../integration_guide/adapter_system/custom_adapters/general_custom_adapter.md) is the recommended way for persisting and loading models. It has the following advantages specific to model persistence:

- Keeps your workflow modular and reproducible in accordance with hetida designers separation of analytics and data ingestion/egestion (Adapter system, wirings etc.). We strongly recommend to follow this approach for production scenarios over for example storing/loading from inside workflow operators as described below!
- Faster and more efficient when handling large models as binary blobs compared to generic rest adapters.
- You may choose a format of your choice, such as [ONNX](https://onnx.ai/) which allows integration into other solutions, even non-Python-based ones.

To get started, besides the [general custom adaper documentation](../integration_guide/adapter_system/custom_adapters/general_custom_adapter.md) you can checkout and read the mentioned builtin adapters code and documentation.

You typically will use the ANY type for arbitrary models / Python objects.

In case additional Python libraries such as [`onnx`](https://github.com/onnx/onnx), [`tensorflow-onnx`](https://github.com/onnx/tensorflow-onnx), [`onnx-tensorflow`](https://github.com/onnx/onnx-tensorflow), or [`sklearn-onnx`](https://github.com/onnx/sklearn-onnx) are needed, just follow the instructions on how to add [Custom Python Dependencies](../deployment_operation/managing_python_dependencies.md) to your runtime Docker container.

## Persisting and Loading from within Workflows via Components

A simple option for development purposes is to use basic components for serializing objects to disk.

!!! warning
We only recommend this for early development / experimentation as its counteracts basic hetida designer principles. For production environments it is higly recommended to use the component adapter or use / write another suitable general custom adapter. Almost always using the component adapter is strictly better and your best option with the least effort and the best cost-benefit ratio

In order to persist objects from within workflows, the `Store Object` component is provided in the category `Data Sinks`. In addition to the object to be stored, this component expects a `name` string and a `tag` string as inputs, which in combination should uniquely identify the respective object. The name and the tag are used to determine the location of the serialized object file. The tag must not be "latest" because that is used internally and has a specific meaning.

In order to load a persisted object, the `Load Object` component is provided in the category `Data Sources`. This component takes a `name` string and a `tag` string as input and returns the object stored under that name and tag.

The directory where the serialized object files are stored within the container is defined by the `MODEL_REPO_PATH` environment variable, which by default is `/mnt/obj_repo`. To make this persistent a volume needs to be mounted there, like in the default [docker-compose setup](https://github.com/hetida/hetida-designer/blob/release/docker-compose.yml).

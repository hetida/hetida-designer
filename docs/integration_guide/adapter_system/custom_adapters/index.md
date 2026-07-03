
# Custom Adapters

Writing custom adapters is the prefered way to connect your organization's internal or external data sources and sinks to hetida designer. There are two kinds of custom adapters you can write:

* Generic Rest adapters
* General Custom adapters

## General custom adapters versus Generic Rest adapters

General custom adapters need to implement 

1. certain web service endpoints for data browsing / filtering and wiring construction in user interfaces

2. runtime functions (Python code) for actually loading / writing data.

The web endpoints from 1. agree with the same-purposed web endpoints of generic rest adapters mentioned below. What makes this adapters "general" is that they are not tied to loading/sending data through web endpoints (HTTP/Rest) like generic Rest adapters, but can provide their completely own method by adding custom plugin-Python-code to the runtime implementation.

Generic Rest adapters need to implement

1. certain web service endpoints for data browsing/ filtering and wiring construction in user interfaces

2. certain additional web service endpoints for receiving and sending data

These web service endpoints are typically implemented as one backend web service and therefore are quite easy to write. They can be written in a programming language of your choice.

General custom adapters need two code artefacts (API, runtime functions) and the runtime functions need to be written in Python.

Generic Rest endpoints provide their data via JSON through web endpoints which is convenient but not suitable for really large data amounts due to serialization/deserialization costs and inefficiently large JSON Request/Response sizes (compared to e.g. binary formats).

General custom adapters can use arbitrary code to access data and therefore can implement fast and efficient direct data access to databases etc. However the custom runtime functions are coupled to the runtime service which may have disadvantages for your deployment setup and security requirements etc. depending on your concrete usage scenario.


!!! tip "Component Adapter"
    For quickly integrating a single data source or sink without needing browsing / discoverability it often is a good idea to start with a [component adapter](../builtin_adapters/component_adapter.md) source or sink component.

## Guides/Examples for writing your own adapters

### General Information

* [Registering adapters](../adapter_registration.md)

### Generic Rest adapters

* [Writing Generic Rest Adapters](./generic_rest_adapters.md)
* [Python Demo Adapter source code](https://github.com/hetida/hetida-designer/tree/release/demo-adapter-python)

### General Custom adapters

* [Writing General Custom Adapters](./general_custom_adapter.md)
* direct link to the [hetdesrun_config.py](https://github.com/hetida/hetida-designer/blob/release/runtime/hetdesrun_config.py) which explains the runtime-side implementation.
* The built-in [local file adapter](../builtin_adapters/local_file_adapter.md) and [sql adapter](../builtin_adapters/sql_adapter.md) are examples of general custom adapters.
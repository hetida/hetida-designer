# Builtin Adapters

* The [direct provisioning](./manual_input.md) adapter is used for manual input or input that is directly provided as part of the wiring of the execution request. And for output that is returned as part of the execution response.
* [Blob Storage Adapter](./blob_storage_adapter.md)
* [Kafka Adapter](./kafka_adapter.md)
* [Local (mounted) File Adapter](./local_file_adapter.md)
* [SQL Adapter](./sql_adapter.md)
* [External Sources Adapter](./external_sources_adapter.md): Builtin access to some external APIs / data sources.
* [Component Adapter](./component_adapter.md): Write components that act as sources or sinks without compromising reproducibility and separation of concerns.


### Built-In adapters

At the moment hetida designer is equipped with the following built-in adapters.

#### Direct provisioning (Manual Input / Only Output)

The `direct_provisioning` adapter is a special adapter that allows to provide data directly when executing a workflow. That means the input values are part of the wiring, i.e. they are provided in the json object.

In particular this adapter is responsible for the [manual input](./manual_input.md) in the designer test execution dialog.

On the output side it handles the case of returning data from outputs with the execution web request: Result data from Outputs "wired" to this adapter is returned as part of the execution response when executing a workflow via the hetida designer backend webservice. This also is the default if an output wiring is not provided for an output.

When automating workflows in production scenarios this adapter is typically used for simple parameters (like FLOAT or STRING inputs) but not for mass data (like DATAFRAME inputs/outputs).

#### Demo adapters

There is a Python demo adapter, that demonstrate the capabilities of the adapter system and how to write your own adapter.

It is a **generic Rest adapter**, a certain kind of custom adapters that is easy to write and provides and receives data through web service endpoints (see below for details).

#### Local File Adapter

This adapter allows to read/write csv or excel files from/to directories directly mounted (as volumes) in the runtime container. This adapter is an example of a **general custom adapter** (read below on what that means).

Detail on usage and configuration of the Local File Adapter can be found [here](./local_file_adapter.md).

#### Blob Storage Adapter
The Blob Storage Adapter allows to read/write objects, such as e.g. trained models, as pickled byte files to a mounted Blob storage based on the S3 standard.

The adapter structure can be configured via a JSON file, in particular which parts of the Blob storage should be accessible via the adapter. Details on usage and configurateon of the Blob Storage Adapter can be found [here](./blob_storage_adapter.md)
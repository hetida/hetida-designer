# Builtin Adapters


* The [direct provisioning](./manual_input.md) adapter is used for manual input or input that is directly provided as part of the wiring of the execution request. And for output that is returned as part of the execution response.
* The [Drop Result](./drop_result_adapter.md) simply drops an output result.
* The [Plot](./plot_adapter.md) adapter provides a PLOTLYJSON for the output using a fixed visualization. It can be used to quickly switch to plotting the result for testing without needing to embed the transformation in a worklfow and to add a plot operator.
* [Blob Storage Adapter](./blob_storage_adapter.md)
* [Kafka Adapter](./kafka_adapter.md)
* [Local (mounted) File Adapter](./local_file_adapter.md)
* [SQL Adapter](./sql_adapter.md)
* [External Sources Adapter](./external_sources_adapter.md): Builtin access to some external APIs / data sources.
* [Component Adapter](./component_adapter.md): Write components that act as sources or sinks without compromising reproducibility and separation of concerns.
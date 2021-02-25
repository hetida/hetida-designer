### Writing a general custom adapter

As said in the introduction, to write a general custom adapter you have to create two code artifacts:

* a web service with some of the endpoints that also occur in generic Rest adapters

* some Python code for actual data retrieval and data sending for the runtime (Runtime Plugin)

## Web service endpoints

You need to implement all those endpoints of the [Generic Rest adapter web service interface](../generic_rest_adapters/web_service_interface.md) that are necessary for the user interface to work. These endpoints will be used to construct wirings which your runtime plugin then receives.

This means all web endpoints that are not purely for data retrieval / data sending like the /dataframe and /timeseries endpoints must be implemented.

### Runtime-Plugin

You have to write Python code as is described in the [hetdesrun_config.py](https://github.com/hetida/hetida-designer/blob/release/runtime/hetdesrun_config.py).

# Adapter Registration

## Registration to Backend

A new adapter must be registered at least in the hetida designer backend in order to make it available to all hetida designer components (backend, frontend, runtime) by setting the environment variable `HETIDA_DESIGNER_ADAPTERS`.

This environment variable is a string consisting of comma-separated entries (one for each adapter) where each entry itself consists of `|`-separated configuration parameters as follows:

1. Adapter ID (String), should be human-readable, must be unique

2. Adapter Name (this is used in the user interface)

3. External Adapter URL (from Frontend)

4. Internal Adapter URL (how the hetida designer runtime reaches the adapter. This may coincide with the External Adapter URL). For general custom adapters this is typically ignored.

I.e. the format is

```
FirstAdapterId|FirstAdapterName|FirstAdapterUrl|FirstAdapterInternalUrl,SecondAdapterIdAdapter2|SecondAdapterName|SecondAdapterUrl|SecondAdapterInternalUrl...
```

Example with two adapters:

```
demo-adapter-python|Python-Demo-Adapter|http://localhost:8092|http://hetida-designer-demo-adapter-python:8092,demo-adapter-java|Java-Demo-Adapter|http://localhost:8091/adapter|http://hetida-designer-demo-adapter-java:8091/adapter    
```

!!! note Note
    The registered adapters can be queried from the hetida designer backend [api](../api.md) endpoint `/api/adapters`. E.g. the hetida designer frontend obtains information of available adapters from there.

## Registering a new generic rest adapter

For a generic rest adapter the runtime service must know its (internal) url to be able to load data from it or send data to it. There are two ways to tell the runtime this information

1. The generic rest adapter can be registered to the hetida designer runtime via the same environment variable `HETIDA_DESIGNER_ADAPTERS` as described above for the backend. **This is the preferred solution since it avoids the need for the runtime to make requests to the backend**
2. If `HETIDA_DESIGNER_BACKEND_API_URL` is configured for the runtime service, the runtime will try to obtain registered adapters from the backend.

## Registering a new general custom adapter

First you have to **register the webservice** of the general custom adapter to the hetida designer backend as explained above.

Second you have to **register your runtime-side Python plugin** via the `hetdesrun_config.py` file. This file is available as `/app/hetdesrun_config.py` in the runtime docker image. You either need to create your own derived Docker image for the runtime replacing this file with your own variant or you mount your adapted hetdesrun_config.py over the existing file effectively shadowing it &ndash; how you do that depends on your environment and setup, see for example [here](https://stackoverflow.com/questions/42248198/how-to-mount-a-single-file-in-a-volume#42260979).

The default `hetdesrun_config.py` (you can find it [here](https://github.com/hetida/hetida-designer/blob/release/runtime/hetdesrun_config.py)) contains a detailed guide how you register your Python plugin functions there. You need to use the Adapter Id with which you register the web service as `adapter_key` there.

Note that the functions you provide must be importable from the /app dir of the docker image. This means if your runtime-side adapter implementation contains Python modules / packages you must make them available in the runtime docker image &ndash; again for example by creating a derived docker image or volume mounting.

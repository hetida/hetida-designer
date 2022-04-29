## Registering a new generic Rest adapter

A new generic Rest adapter must be registered in the hetida designer backend in order to make it available to all hetida designer components (backend, frontend, runtime).

This is done by adding values to the environment variable `org.hetida.designer.backend.installed.adapters` of the hetida designer backend service.

This environment variable is a string consisting of comma-separated entries (one for each adapter) where each entry itself consists of `|`-separated configuration parameters as follows:

1. Adapter ID (String), should be human-readable, must be unique

2. Adapter Name (this is used in the user interface)

3. External Adapter URL (from Frontend)

4. Internal Adapter URL (how the hetida designer runtime reaches the adapter. This may coincide with the External Adapter URL)

I.e. the format is

```
FirstAdapterId|FirstAdapterName|FirstAdapterUrl|FirstAdapterInternalUrl,SecondAdapterIdAdapter2|SecondAdapterName|SecondAdapterUrl|SecondAdapterInternalUrl...
```

Example with both demo adapters from the docker-compose:

```
demo-adapter-python|Python-Demo-Adapter|http://localhost:8092|http://hetida-designer-demo-adapter-python:8092,demo-adapter-java|Java-Demo-Adapter|http://localhost:8091/adapter|http://hetida-designer-demo-adapter-java:8091/adapter    
```

Note: The registered adapters can be queried from the hetida designer backend api endpoint /adapters.

## Registering a new general custom adapter

First you have to **register the webservice** of the general custom adapter in the same way that is explained above for generic Rest adapters.

Second you have to **register your runtime-side Python plugin** via the `hetdesrun_config.py` file. This file is available as /app/hetdesrun_config.py in the runtime docker image. You either need to create your own derived Docker image for the runtime replacing this file with your own variant or you mount your adapted hetdesrun_config.py on the existing file effectively shadowing it &ndash; how you do that depends on your environment and setup, see for example [here](https://stackoverflow.com/questions/42248198/how-to-mount-a-single-file-in-a-volume#42260979).

The default `hetdesrun_config.py` (you can find it [here](https://github.com/hetida/hetida-designer/blob/release/runtime/hetdesrun_config.py)) contains a detailed guide how you register your Python plugin functions there. You need to use the Adapter Id with which you regsister the web service as `adapter_key` there.

Note that the functions you provide must be importable from the /app dir of the docker image. This means if your runtime-side adapter implementation contains Python modules / packages you must make them available in the runtime docker image &ndash; again for example by creating a derived docker image or volume mounting.

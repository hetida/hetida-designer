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

!!! note
    The registered adapters can be queried from the hetida designer backend [api](../api.md) endpoint `/api/adapters`. E.g. the hetida designer frontend obtains information of available adapters from there.

## Registering a new generic rest adapter

For a generic rest adapter the runtime service must know its (internal) url to be able to load data from it or send data to it. There are two ways to tell the runtime this information

1. The generic rest adapter can be registered to the hetida designer runtime via the same environment variable `HETIDA_DESIGNER_ADAPTERS` as described above for the backend. **This is the preferred solution since it avoids the need for the runtime to make requests to the backend**
2. If `HETIDA_DESIGNER_BACKEND_API_URL` is configured for the runtime service, the runtime will try to obtain registered adapters from the backend.

## Validating received metadata

The runtime parses the metadata of SERIES, SINGLETSFRAME and MULTITSFRAME workflow inputs loaded from adapters, including manual input via the direct provisioning adapter, and attaches it as model if it is valid metadata of the [metadata conventions](../../user_guide/attached_metadata.md#metadata-attached-as-model), as far as this can be determined without the data. Whether metadata which does not adhere to the conventions, also in comparison with the data, is reported is configured per adapter via the environment variable `ADAPTER_METADATA_VALIDATION` of the runtime service as json object, mapping adapter ids to one of the following modes. The id of the direct provisioning adapter is `direct_provisioning`.

* `"OFF"`: The metadata is not checked. Metadata not adhering to the conventions is left as it is without notice, so that components find no metadata in it. This is the default for adapters not listed.
* `"WARN"`: If the metadata does not adhere to the conventions, a warning is logged, which mentions the adapter and the workflow inputs with their sources together with the found issues. Missing metadata, e.g. a response without `Data-Attributes` header, does not adhere to the conventions either. The warning lists each distinct issue once, so that e.g. the same unknown field in the metadata of every input or metric does not flood the logs: Issues which only differ in the indices of their locations are summarized as one, with `[*]` for indices differing between the occurrences. It is followed by the number of its occurrences if it occurs several times in an input, and by the inputs it occurs in if several inputs have issues.
* `"ERROR"`: The execution fails if errors are found, with an error message listing them. If only warnings are found, these are logged as with `"WARN"`.

For example:

```
ADAPTER_METADATA_VALIDATION={"hetida-platform-adapter": "WARN", "demo-adapter-python": "ERROR"}
```

The checks are the same as those of the [endpoint for checking metadata](../../user_guide/attached_metadata.md#checking-metadata-via-the-api), including the comparison of the metadata with the received data, after the `attrs` of the input wiring have been merged into the metadata. Other top-level keys of the metadata besides those of the conventions are not reported. DATAFRAME metadata is never checked, since there are no metadata conventions for DATAFRAMEs.

Data loaded by components themselves is not checked by the runtime. The base component "Hetida Platform Signal Timeseries Data" (from 0.1.12 on) checks the metadata of the signals it loads itself, always, also with `"OFF"`, but without comparing it with the data: It logs a warning summarizing the issues of the signals whose metadata does not adhere to the conventions in the same format, or fails if `"ERROR"` is configured for the hetida platform adapter and errors are found.

## Registering a new general custom adapter

First you have to **register the webservice** of the general custom adapter to the hetida designer backend as explained above.

Second you have to **register your runtime-side Python plugin** via the `hetdesrun_config.py` file. This file is available as `/app/hetdesrun_config.py` in the runtime docker image. You either need to create your own derived Docker image for the runtime replacing this file with your own variant or you mount your adapted hetdesrun_config.py over the existing file effectively shadowing it &ndash; how you do that depends on your environment and setup, see for example [here](https://stackoverflow.com/questions/42248198/how-to-mount-a-single-file-in-a-volume#42260979).

The default `hetdesrun_config.py` (you can find it [here](https://github.com/hetida/hetida-designer/blob/release/runtime/hetdesrun_config.py)) contains a detailed guide how you register your Python plugin functions there. You need to use the Adapter Id with which you register the web service as `adapter_key` there.

Note that the functions you provide must be importable from the /app dir of the docker image. This means if your runtime-side adapter implementation contains Python modules / packages you must make them available in the runtime docker image &ndash; again for example by creating a derived docker image or volume mounting.

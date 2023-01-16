# Autoimport

In addition to the automatic deployment of base components and example workflows (see [doc](./base_component_deployment.md)) hetida designer offers automatic import of sets of components/workflows from directories / files mounted into the backend image. This allows for easy deployment and up-to-date-keeping of your own custom sets of components/workflows across hetdia designer instances in different environments.

## Import sources

Import sources can be directories or json files:

* **directories**: directories structured as provided by the export functionality (see [export doc](import_export.md) can be automatically imported
* **json files**: JSON files that contain a list of transformation revisions as provided by the backend api's `/api/transformations` GET endpoint can be automatically imported. This is in particular useful in kubernetes setups where a single file can be easily mounted via a configmap (i.e. no need to create a persistent volume)

Automatic importing happens at backend startup time (prestart) if the environment variable `HD_BACKEND_AUTOIMPORT_DIRECTORY` is set to a directory path. The autoimport will then include all subdirectories in this directory and all `.json` files residing there as import sources. It expects them to be structured as described above.

The backend image already includes a `/mnt/autoimport` that can be used as the directory path for `HD_BACKEND_AUTOIMPORT_DIRECTORY`.

## Configuring autoimport for each import source
If you save/mount an additional file with being the full name of the import source plus an additional suffix `.config.json`, this file is parsed for configuration for that particular import source. For example if your import source is a file `/mnt/automimport/my_trafos.json` this config file must be `/mnt/autoimport/my_trafos.json.config.json`

Its content must a json representation describing an instance of the ImportSourceConfig pydantic class in `/runtime/hetdesrun/trafoutils/io/load.py`. An example would be

```
{
    "filter_params": {
        "category_prefix": "MATH_",
        "include_deprecated": false,
        "include_dependencies": true
    },
    "update_config": {
        "allow_overwrite_released": true
    }
}
```

The filter params determine filters that are applied before importing. In this example we tell it to import all transformation revisions with category starting with "MATH_" which are not deprecated and their dependencies (the later even if they are deprecated!).

The update config is used to control some aspects of the actual importing process. Here we allow to overwrite existing released transformation revisions.

For further details and other options please refer to the source code mentioned above.


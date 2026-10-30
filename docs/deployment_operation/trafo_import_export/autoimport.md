# Autoimport

In addition to the automatic deployment of base components and example workflows (see [doc](./base_trafo_deployment.md)) hetida designer offers automatic import of sets of components/workflows from directories / files mounted into the backend image.

This allows for easy deployment and up-to-date-keeping of your own custom sets of components/workflows across hetida designer instances in different environments.

## Import sources

The autoimport imports from the directory set via the environment variable `HD_BACKEND_AUTOIMPORT_DIRECTORY`. The backend image already includes a `/mnt/autoimport` directory that can be used for it.

The following entries of this directory are import sources:

* **directories**: directories structured as provided by the export functionality (see [export doc](import_export.md)). All `.json` and `.py` files in them, also in their subdirectories, are imported.
* **json files**: JSON files that contain a list of transformation revisions as provided by the backend api's `/api/transformations` GET endpoint, or a single transformation revision. A list is in particular useful in kubernetes setups where a single file can be easily mounted via a configmap (i.e. no need to create a persistent volume)
* **python files**: `.py` files containing the code of a component

Other files are ignored with a warning. Hidden entries, i.e. starting with a dot, are ignored, e.g. the internal entries of a Kubernetes configmap mounted as directory. An import source which cannot be loaded, e.g. due to invalid json, is not imported. This is logged as error, but does not prevent importing the other import sources.

Automatic importing happens at each start of the backend if `HD_BACKEND_AUTOIMPORT_DIRECTORY` is set, see [database preparation](../database_configuration.md#database-preparation-at-backend-start). If the directory does not exist, the backend logs a warning. In addition autoimport can be triggered directly via the maintenance/trigger_autoimport endpoint, see [maintenance docs](../maintenance/index.md). Both import the same way.

## Configuring the autoimport

The import sources without config file (see below) are imported together. The following environment variables configure how:

- HD_BACKEND_AUTOIMPORT_DIRECTORY_STRIP_WIRINGS (for strip_wirings)
- HD_BACKEND_AUTOIMPORT_DIRECTORY_ALLOW_OVERWRITE_RELEASED (for allow_overwrite_released)
- HD_BACKEND_AUTOIMPORT_DIRECTORY_UPDATE_COMPONENT_CODE (for update_component_code)
- HD_BACKEND_AUTOIMPORT_DIRECTORY_DEPRECATE_OLDER_REVISIONS (for deprecate_older_revisions)

Per default, all of the configurable variables are set to "false". See the documentation for [sync](./sync.md) for further information on allow_overwrite_released and update_component_code.

## Configuring autoimport for each import source
If you save/mount an additional file having the full name of the import source plus an additional suffix `.config.json`, this file is parsed for configuration for that particular import source. For example if your import source is a file `/mnt/autoimport/my_trafos.json` this config file must be `/mnt/autoimport/my_trafos.json.config.json`

Its content must consist of a json representation describing an instance of the ImportSourceConfig pydantic class in `/runtime/hetdesrun/trafoutils/io/load.py`. An example would be

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

Both `filter_params` and `update_config` are required, otherwise the import source is not imported. The config file replaces the environment variables described above for its import source: Options not set in it have the defaults of the ImportSourceConfig class, which differ from them in some cases, e.g. `update_component_code` is true.

For further details and other options please refer to the source code mentioned above and the backend openapi documentation (at suburl /api/docs) for the /api/transformations PUT endpoint.

## Order of import

First the import sources without config file are imported, then the ones with config file, sorted by their paths. If several import sources without config file contain a transformation revision with the same id, the one from the last path is imported. Within the import sources without config file and within each import source with config file, components and workflows are imported in the order of their dependencies.

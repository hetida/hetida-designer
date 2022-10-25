# Export and Import of Components/Workflows

Components and Workflows can be exported and imported via the backend API endpoints. To make that easier, scripts are available that can be run from the runtime Docker image. This can be used to keep local file copies as backup or to get components/workflows from one designer installation to another.

This guide assumes the default docker-compose setup described in the project README.

## Exporting all components and workflows

Go to a directory where you want to store the exported components and workflows.
Now run 

```shell
docker run --rm \
  -e "HETIDA_DESIGNER_BACKEND_API_URL=http://hetida-designer-backend:8090/api/" \
  --name htdruntime_export \
  --mount type=bind,source="$(pwd)",target=/mnt/obj_repo \
  --network hetida-designer-network \
  --entrypoint python \
  hetida/designer-runtime -c 'from hetdesrun.exportimport.export import export_all; export_all("/mnt/obj_repo/exported_data/");'
```

The command will create a subdirectory `exported_data` in your current directory with subfolders `components` and `workflows` each of which contains subfolders corresponding to the categories in which the components and workflows are stored in individual json files.

## <a name="import"></a> Importing all components and workflows

> :warning: IMPORTANT: If you have existing workflows/components in your installation you should do a complete database backup as is described in [backup](./backup.md), just in case something bad happens! Note that importing overwrites possibly existing revisions with the same id.

Simply run the following command to import the exported components and workflows from the same directory:

```shell
docker run --rm \
  -e "HETIDA_DESIGNER_BACKEND_API_URL=http://hetida-designer-backend:8090/api/" \
  --name htdruntime_import \
  --mount type=bind,source="$(pwd)",target=/mnt/obj_repo \
  --network hetida-designer-network \
  --entrypoint python \
  hetida/designer-runtime -c 'from hetdesrun.exportimport.importing import import_transformations; import_transformations("/mnt/obj_repo/exported_data/", update_component_code=False);'
```

The input parameter `update_component_code` of the `import_transformations` function is optional and set to `True` by default. When set to `True`, the code is updated even of components in the "RELEASED" state &ndash; based on the current implementation of the `update_code` function &ndash; before they are stored in the database.
This has the advantage that the automatically generated part of the code corresponds to the latest schema and contains all relevant information about the component.
Setting the parameter to `False` ensures that the code is not changed, but remains exactly as it has been exported.

## Importing components from single python files

Components are also importable from python files, which can be created by simply copying the component code from the hetida designer user interface into a .py file. When importing such a file, the module docstring from the third line onwards will be used as documentation.

Note, that the .py file does not include the test wiring of the component, which is included in the json export format above. Components as .py files should be located in the same subdirectories as ordinary component files.

## Remove test wirings when importing

You may want to ignore the test wirings stored in the component/workflow files during import. One reason may be that the target backend validates incoming test wirings of the imported workflows and components: Adapters present in a test wiring must be registered under the same adapter key in the target backend.

To ignore test wirings when importing, simply add a keyword parameter `strip_wirings=True` to the call of the `import_transformations` function in the commands documented above.


## Import new components and workflows added to the git repository

There are two different ways to import new components and workflows added to the git repository.
You can use the [autodeployment feature](./base_component_deployment.md) or you can use the import feature described [above](#import).

### Import new components and workflows via autodeploy

If you (re-)start the backend container, e.g. to deploy the latest release, without setting the environment variables `HD_BACKEND_AUTODEPLOY_BASE_TRANSFORMATIONS` and `HD_BACKEND_PRESERVE_DB_ON_AUTODEPLOY` to `false` in the `docker-compose.yml` or `docker-compose-dev.yml` file, all base components and example workflows will be (re-)imported.
To disable overwriting existing base components and example workflows with status `RELEASED` or `DISABLED` you can additionally set the environment variable `HD_BACKEND_PRESERVE_DB_ON_AUTODEPLOY` to `false` in the `docker-compose.yml` or `docker-compose-dev.yml` file. Components and workflows with status `DRAFT` will be overwritten in any case.

### Import new compoments and workflows running a command in a local docker instance
The base components and example workflows provided with hetida designer are contained in the `transformations/' directory within the docker container.

**Note:** The version of the components and workflows imported depends on the version of the image you use when running this command instead of the version of the hetida designer instance to which they are imported.

To disable overwriting existing base components and example workflows with status `RELEASED` or `DISABLED` you can set the input parameter `allow_overwrite_released` to `False`. Components and workflows with status `DRAFT` will be overwritten in any case.

You can simply run the following command to import all components and workflows from there:

```shell
docker run --rm \
  -e "HETIDA_DESIGNER_BACKEND_API_URL=http://hetida-designer-backend:8090/api/" \
  --name htdruntime_import \
  --network hetida-designer-network \
  --entrypoint python \
  hetida/designer-runtime -c 'from hetdesrun.exportimport.importing import import_transformations; import_transformations("transformations/", allow_overwrite_released=False, update_component_code=False);'
```

If you run the command in the same environment as your instance is running, you can bypass the REST API and more directly access the database by setting the optional input paramter `directly_into_db' to true, which is most likely faster:

```shell
docker run --rm \
  --name htdruntime_import \
  --entrypoint python \
  hetida/designer-runtime -c 'from hetdesrun.exportimport.importing import import_transformations; import_transformations("transformations/", allow_overwrite_released=False, update_component_code=False, directly_into_db=True);'
```

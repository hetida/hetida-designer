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
  hetida/designer-runtime -c 'from hetdesrun.exportimport.export import export_transformations; export_transformations("/mnt/obj_repo/exported_data/");'
```

The command will create a subdirectory `exported_data` in your current directory with subfolders `components` and `workflows` each of which contains subfolders corresponding to the categories in which the components and workflows are stored in individual json files.

## Exporting selected components and workflows

To export only selected components and workflows instead of all, the `export_transformations` accepts several optional input parameters to filter for the desired components and workflows.

- type: must be either "COMPONENT" or "WORKFLOW" (if specified)
- state: must be either "DRAFT", "RELEASED" or "DISABLED" (if specified)
- ids: a list of ids, only components/workflows whose ids are included in this list will be exported
- names: a list of names, only components/workflows whose names are included in this list will be exported
- category: a category, only components/workflows in this category will be exported
- include_deprecated: if set to false, deprecated components/workflows will **not** be exported (default: true)

If more than one of these parameters is specified, only the components/workflows that pass all filters will be exported, which corresponds to a logical "and" connection of the filter criteria.

The exported JSON files are automatically saved in subfolders corresponding to the categories of the exported components and workflows within subfolders corresponding to their type ("components" or "workflows").

**Note:** Storing a workflow in the database that contains components or other workflows that are not yet stored in the database will result in an error.
Therefore, the export function also automatically exports all dependent transformation revisions, regardless of whether they match the filters.

For example, the shell command to export the components that return the mathematical constants e and $\pi$ is

```shell
docker run --rm \
  -e "HETIDA_DESIGNER_BACKEND_API_URL=http://hetida-designer-backend:8090/api/" \
  --name htdruntime_export \
  --mount type=bind,source="$(pwd)",target=/mnt/obj_repo \
  --network hetida-designer-network \
  --entrypoint python \
  hetida/designer-runtime -c 'from hetdesrun.exportimport.export import export_transformations; export_transformations("/mnt/obj_repo/exported_data/", type="COMPONENT", category="Arithmetic", names=["E", "Pi"]);'
```

## <a name="import"></a> Importing all components and workflows

> :warning: IMPORTANT: If you have existing workflows/components in your installation you should do a complete database backup as is described in [backup](./backup.md), just in case something bad happens! Note that importing overwrites possibly existing revisions with the same id.

To disable overwriting existing base components and example workflows with status `RELEASED` or `DISABLED` you can set the input parameter `allow_overwrite_released` to `False`. Components and workflows with status `DRAFT` will be overwritten in any case.

Simply run the following command to import the exported components and workflows from the same directory:

```shell
docker run --rm \
  -e "HETIDA_DESIGNER_BACKEND_API_URL=http://hetida-designer-backend:8090/api/" \
  --name htdruntime_import \
  --mount type=bind,source="$(pwd)",target=/mnt/obj_repo \
  --network hetida-designer-network \
  --entrypoint python \
  hetida/designer-runtime -c 'from hetdesrun.exportimport.importing import import_transformations; import_transformations("/mnt/obj_repo/exported_data/", allow_overwrite_released=False, update_component_code=False);'
```

The input parameter `update_component_code` of the `import_transformations` function is optional and set to `True` by default. When set to `True`, the code is updated even of components in the "RELEASED" state &ndash; based on the current implementation of the `update_code` function &ndash; before they are stored in the database.
This has the advantage that the automatically generated part of the code corresponds to the latest schema and contains all relevant information about the component.
Setting the parameter to `False` ensures that the code is not changed, but remains exactly as it has been exported.

## Importing directly into the database

If you run the command in the same environment as your instance is running, you can bypass the REST API and more directly access the database by setting the optional input paramter `directly_into_db` to true, which is most likely faster:

```shell
docker run --rm \
  --name htdruntime_import \
  --entrypoint python \
  hetida/designer-runtime -c 'from hetdesrun.exportimport.importing import import_transformations; import_transformations("/mnt/obj_repo/exported_data/"", directly_into_db=True);'
```

## Importing components from python files

Components can be imported not only from `.json` files, but also from `.py` files. Such Python files should contain the code itself defining a main function as well as a dictionary called `COMPONENT_INFO` containing the attributes of the corresponding component, just like the components created in the web application.

Attributes that are not provided will be set to the following default values:
* id: `<randomly generated UUID>`
* revision_group_id: `<randomly generated UUID>`
* name: `"Unnamed Component"`
* version_tag: `"1.0.0"`
* description: `"No description provided"`
* category: `"Other"`
* state: `"RELEASED"`
* released_timestamp: `<time of import>`
* inputs: `{}`
* outputs: `{}`

If present, the module docstring (starting from its third line) is used as documentation. 

**Note:** There is no possibility to include the test wiring of the component in `.py` files. The test wiring can only be included in the `.json` export format.

## Remove test wirings when importing

You may want to ignore the test wirings stored in the component/workflow files during import. One reason may be that the target backend validates incoming test wirings of the imported workflows and components: Adapters present in a test wiring must be registered under the same adapter key in the target backend.

To ignore test wirings when importing, simply add a keyword parameter `strip_wirings=True` to the call of the `import_transformations` function in the commands documented above.

## Deprecate older revisions when importing new ones

To ensure that only the latest revision of a revision group can be used, you can deprecate all other revisions of the same revision group during import by setting the parameter `deprecate_older_revisions=True` in the `import_transformations` function call.
If the latest revision of a revision group is stored in the database, all imported transformation revisions of this group will be deprecated.

## Generate file with paths to json files in import order

To generate a file which contains line by line the paths to all exported `.json` files in the order in which they should be imported, just execute the following command with the path to the directory to which the `.json` files have been exported and the path to where this file should be written.

```shell
docker run --rm \
  --name htdruntime_import \
  --entrypoint python \
  hetida/designer-runtime -c 'from hetdesrun.exportimport.importing import generate_import_order_file; generate_import_order_file("exported_data", "json_import_order.txt");'
```

In case this directory contains also component code as `.py` files that you want to import as `.json` files, set the option `transform_py_to_json` to `True` and the corresponding `.json` files will be generated and added to the list of paths in the generated newly file.

## Import new components and workflows added to the git repository

If you (re-)start the backend container, you can use the [autodeployment feature](./base_component_deployment.md).
For a running backend container you can use the function `import_transformations`.

The base components and example workflows provided with hetida designer are contained in the `transformations/` directory within the docker container.

**Note:** The version of the components and workflows imported depends on the version of the image you use when running this command instead of the version of the hetida designer instance to which they are imported.

You can simply run the following command to import all components and workflows from there:

```shell
docker run --rm \
  -e "HETIDA_DESIGNER_BACKEND_API_URL=http://hetida-designer-backend:8090/api/" \
  --name htdruntime_import \
  --network hetida-designer-network \
  --entrypoint python \
  hetida/designer-runtime -c 'from hetdesrun.exportimport.importing import import_transformations; import_transformations("transformations/");'
```
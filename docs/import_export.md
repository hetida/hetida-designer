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

## Importing all components and workflows

> :warning: IMPORTANT: If you have existing workflows/components in your installation you should do a complete database backup as is described in [backup](./backup.md), just in case something bad happens! Note that importing overwrites possibly existing revisions with the same id.

Simply run the following command to import the exported components and workflows from the same directory:

```shell
docker run --rm \
  -e "HETIDA_DESIGNER_BACKEND_API_URL=http://hetida-designer-backend:8090/api/" \
  --name htdruntime_import \
  --mount type=bind,source="$(pwd)",target=/mnt/obj_repo \
  --network hetida-designer-network \
  --entrypoint python \
  hetida/designer-runtime -c 'from hetdesrun.exportimport.importing import import_transformations; import_transformations("/mnt/obj_repo/exported_data/");'
```

## Importing components from single python files

Components are also importable from python files, which can be created by simply copying the component code from the hetida designer user interface into a .py file. When importing such a file, the module docstring from the third line onwards will be used as documentation.

Note, that the .py file does not include the test wiring of the component, which is included in the json export format above. Components as .py files should be located in the same subdirectories as ordinary component files.

## Remove test wirings when importing
You may want to ignore the test wirings stored in the component/workflow files during import. One reason may be that the target backend validates incoming test wirings of the imported workflows and components: Adapters present in a test wiring must be registered under the same adapter key in the target backend.

To ignore test wirings when importing, simply add a keyword parameter `strip_wirings=True` to the call of the `import_transformations` function in the commands documented above.


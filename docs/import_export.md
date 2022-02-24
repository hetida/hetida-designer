# Export and Import of Components/Workflows

Components and Workflows can be exported and imported via the backend API endpoints. To make that easier, scripts are available that can be run from the runtime Docker image. This can be used to keep local file copies as backup or to get components/workflows from one designer installation to another.

This guide assumes the default docker-compose setup described in the project README.

## Exporting all components and workflows

First you should do a complete database backup as is described in [backup](./backup.md), just in case something bad happens.

Then go to a directory where you want to store the exported components and workflows.
Now run 

```shell
docker run --rm \
  -e "HETIDA_DESIGNER_BACKEND_API_URL=http://hetida-designer-backend:8090/api/" \
  --name htdruntime_export \
  --mount type=bind,source="$(pwd)",target=/mnt/obj_repo \
  --network hetida-designer-network \
  --entrypoint python \
  hetida/designer-runtime -c 'from hetdesrun.exportimport.export import export_all; export_all("/mnt/obj_repo/exported_data/", True);'
```

The command will create a subdirectory `exported_data` in your current directory with subfolders `components` and `workflows` each of which contains subfolders corresponding to the categories in which the components and workflows are stored in individual json files.

## Importing components and Workflows

> :warning: IMPORTANT: If you have existing workflows/components in your installation you should do a complete database backup as is described in [backup](./backup.md), just in case something bad happens!

Simply run the following command to import the exported components and workflows from the same directory:

```shell
docker run --rm \
  -e "HETIDA_DESIGNER_BACKEND_API_URL=http://hetida-designer-backend:8090/api/" \
  --name htdruntime_import \
  --mount type=bind,source="$(pwd)",target=/mnt/obj_repo \
  --network hetida-designer-network \
  --entrypoint python \
  hetida/designer-runtime:0.7.0 -c 'from hetdesrun.exportimport.importing import import_all; import_all("/mnt/obj_repo/exported_data/");'
```


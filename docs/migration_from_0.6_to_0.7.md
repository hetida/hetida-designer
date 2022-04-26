# Migration from 0.6 to 0.7.2

Version 0.7 features a complete rewrite of the hetida designer application backend from Java to Python. In particular the database entity model was completely revised.

As a consequence of this, the migration from 0.6.* to 0.7.2 involves manual steps which we describe in this guide. In summary, all components and workflows need to be exported to files from the 0.6 installation and then imported back into the upgraded 0.7 installation.

This guide assumes the default docker compose setup from the Readme. For other setups you have to edit the relevant environment variables like `HETIDA_DESIGNER_BACKEND_API_URL` in the commands below.

> **Note**: When updating your designer installations you must take care of the ports of the backend service. The old backend docker image uses 8080, whereas the new backend docker image uses 8090.

## Step 1: Exporting all components and workflows on 0.6.*

First you should do a complete database backup as is described in [backup](./backup.md), just in case something bad happens.

Then go to a directory where you want to store the exported components and workflows.
Now run 

```shell
docker run --rm \
  -e "HETIDA_DESIGNER_BACKEND_API_URL=http://hetida-designer-backend:8080/api/" \
  --name htdruntime_export \
  --mount type=bind,source="$(pwd)",target=/mnt/obj_repo \
  --network hetida-designer-network \
  --entrypoint python \
  hetida/designer-runtime:0.7.2 -c 'from hetdesrun.exportimport.export import export_all; export_all("/mnt/obj_repo/migration_data/", True);'
```

The command will create a subdirectory `migration_data` in your current directory with subfolders `components` and `workflows` each of which contains subfolders corresponding to the categories in which the components and workflows are stored in individual json files.

## Step 2: Importing into 0.7.2

Now upgrade your designer installation to 0.7.2 (As part of this you need to completely delete your database schema / all tables prior to starting the new version. For the docker-compose setup simply delete the postgres volume). Then run the following command to import the exported components and workflows from the same directory:

```shell
docker run --rm \
  -e "HETIDA_DESIGNER_BACKEND_API_URL=http://hetida-designer-backend:8090/api/" \
  --name htdruntime_import \
  --mount type=bind,source="$(pwd)",target=/mnt/obj_repo \
  --network hetida-designer-network \
  --entrypoint python \
  hetida/designer-runtime:0.7.2 -c 'from hetdesrun.exportimport.importing import import_all; import_all("/mnt/obj_repo/migration_data/");'
```


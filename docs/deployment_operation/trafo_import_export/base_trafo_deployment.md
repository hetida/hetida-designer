# Deployment of Base Component and Workflows

At each start of the backend the included base components and workflows are deployed automatically, also if the hetida designer database is not empty (see below).

You can suppress the auto-deployment by setting the environment variable `HD_BACKEND_AUTODEPLOY_BASE_TRANSFORMATIONS` to `false` in the `docker-compose.yml` or `docker-compose-dev.yml` file.


```yaml
...

  hetida-designer-backend:
    ...
    environment:
      ...
      - HD_BACKEND_AUTODEPLOY_BASE_TRANSFORMATIONS=false
      ...
    ...
...
```

!!! warning "Warning"

    If the database is not empty, the base components and workflows stored in your database are overwritten by the version in the image. This way fixes of base components and workflows arrive with a new image, even if they are made in already released revisions. This might affect the reproducibility of workflows using them.

You can disable auto-deployment if the database is not empty by setting the environment variable `HD_BACKEND_PRESERVE_DB_ON_AUTODEPLOY` to `true`.

You can restrict overwriting released and deprecated components and workflows during the auto-deployment by setting the environment variable `HD_BACKEND_ALLOW_OVERWRITE_RELEASED` to `false`, see below.

!!! tip "Recommendation"

    It is recommended to allow overwriting so that bug fixes of released components and workflows are automatically deployed. If you preserve the database or disabled overwriting during auto-deploy, you can deploy such updates manually as described below.

Not setting `HD_BACKEND_AUTODEPLOY_BASE_TRANSFORMATIONS` or `HD_BACKEND_ALLOW_OVERWRITE_RELEASED` has the same result as setting them to `true`. Not setting `HD_BACKEND_PRESERVE_DB_ON_AUTODEPLOY` has the same result as setting it to `false`.

### What is overwritten

The auto-deployment identifies base components and workflows by their id. It does not change components and workflows with other ids, e.g. the ones you created, including new revisions of base components and workflows, except that operators of deprecated base components and workflows are marked as deprecated in workflows using them, as always when deprecating. It adds base components and workflows missing in the database, also if you deleted them.

For base components and workflows already in the database, it depends on `HD_BACKEND_ALLOW_OVERWRITE_RELEASED`:

| Base component or workflow in the database | `HD_BACKEND_ALLOW_OVERWRITE_RELEASED=true` (default) | `HD_BACKEND_ALLOW_OVERWRITE_RELEASED=false` |
|---|---|---|
| You changed only its documentation or test wiring (the inputs and outputs last used for execution in the user interface) | documentation and test wiring are reset to the version in the image | documentation and test wiring are reset to the version in the image |
| You deprecated it | released again, documentation and test wiring are reset | kept as it is, including documentation and test wiring |
| The image contains a different version of it, e.g. a fix | overwritten by the version in the image, including documentation and test wiring | kept as it is, including documentation and test wiring |
| The image contains it deprecated | deprecated, otherwise kept as it is | deprecated, otherwise kept as it is |

With `HD_BACKEND_ALLOW_OVERWRITE_RELEASED=false`, the backend logs a warning for each base component or workflow it keeps as it is, at each start. This also applies to base workflows containing base components you deprecated.

Only `HD_BACKEND_PRESERVE_DB_ON_AUTODEPLOY=true` or `HD_BACKEND_AUTODEPLOY_BASE_TRANSFORMATIONS=false` keep all your changes of base components and workflows in a non-empty database.

## Manual Deployment of Base Component and Workflows
If you de-activated auto-deployment of base components and workflows and want to deploy them now at a later stage, you should run

```shell
docker run --rm \
  -e "HETIDA_DESIGNER_BACKEND_API_URL=http://hetida-designer-backend:8090/api/" \
  --name htdruntime_deployment \
  --network hetida-designer-network \
  --entrypoint python hetida/designer-runtime -c 'from hetdesrun.exportimport.importing import import_transformations_from_dir; import_transformations_from_dir("./transformations/");'
```
This does not overwrite released and deprecated base components and workflows already in the database. To deploy fixes of them as well, add `allow_overwrite_released=True` to the call of `import_transformations_from_dir`, or use the maintenance endpoint `deploy_base_trafos` with the query parameter `allow_overwrite_released=true`, see [maintenance](../maintenance/index.md). Check the documentation of [Export and Import of Components/Workflows](./import_export.md) for an introduction of the available options.

Note that in the case of the development environment it makes sense to run the deployment command using the locally
built runtime image via

```shell
docker run --rm \
  -e "HETIDA_DESIGNER_BACKEND_API_URL=http://hetida-designer-backend:8090/api/" \
  --name htdruntime_deployment \
  --network hetida-designer-network \
  --entrypoint python hetida-designer-hetida-designer-runtime -c 'from hetdesrun.exportimport.importing import import_transformations_from_dir; import_transformations_from_dir("./transformations/");'
```

In case your checked out repository directory has a different name replace `hetida-designer-hetida-designer-runtime` by `<directory name>-hetida-designer-runtime`.

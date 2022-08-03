# Deployment of Base Component and Workflows

If the database is empty the base components and workflows will be deployed automatically.
You can suppress the auto-deployment by setting the environment variable `HD_BACKEND_AUTODEPLOY_BASE_TRANSFORMATIONS` to false `false` in the `docker-compse.yml` or `docker-compse.yml` file.


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

You can also run auto-deployment even if the database is not empty by setting the environment variable `HD_BACKEND_PRESERVE_DB_ON_AUTODEPLOY` to false `false` in the `docker-compse.yml` or `docker-compse.yml` file.
In that case the base components stored in your database are overwritten by the latest (git) version and might affect the reproducibility of workflows using them. Despite that any other components or workflows that you created stay untouched.

Not setting these environement variables has the same result as setting them to `true`.

## Manual Deployment of Base Component and Workflows
If you skipped auto-deployment of base components and workflows and want to deploy them now at a later stage, you should run

```shell
docker run --rm \
  -e "HETIDA_DESIGNER_BACKEND_API_URL=http://hetida-designer-backend:8090/api/" \
  --name htdruntime_deployment \
  --network hetida-designer-network \
  --entrypoint python hetida/designer-runtime -c 'from hetdesrun.exportimport.importing import import_transformations; import_transformations("./transformations/");'
```

Note that in the case of the development environment it makes sense to run the deployment command using the locally
built runtime image via

```shell
docker run --rm \
  -e "HETIDA_DESIGNER_BACKEND_API_URL=http://hetida-designer-backend:8090/api/" \
  --name htdruntime_deployment \
  --network hetida-designer-network \
  --entrypoint python hetida-designer_hetida-designer-runtime -c 'from hetdesrun.exportimport.importing import import_transformations; import_transformations("./transformations/");'
```

In case your checked out repository directory has a different name replace `hetida-designer_hetida-designer-runtime` by `<directory name>_hetida-designer-runtime`.

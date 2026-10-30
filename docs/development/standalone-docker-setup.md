# Standalone Docker Setup

This manual explains how to set up the main application submodules as docker containers without using docker-compose.

## Installing prerequisite dependencies

You'll have to install a recent version of [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
and [docker](https://docs.docker.com/get-docker/).

!!! note "Note for Windows Users"
    On Windows, we recommend to configure Docker to use Linux Containers (the default setting) and git to use the checkout strategy *Checkout as-is, commit Unix-sytyle line endings*. In every case, make sure that these settings match.

## Getting the source code

Get the source code by entering the following commands in your terminal:

```shell
git clone git@github.com:hetida/hetida-designer.git
cd hetida-designer
git checkout develop
```

## Application Submodules

The application consists of three submodules: a backend REST service, a runtime that
executes hetida designer workflows, and a frontend that allows you to interact with the
backend and the runtime to build components, workflows and test them. Note that both backend and runtime can be run together or as separated services. The latter is recommended for security reasons and to be able to scale the runtime separately from the application backend.

You'll find corresponding Dockerfiles in the source code's root folder. You can start (parts of) hetida designer in standalone docker containers as follows. The containers find each other by their names in a common docker network, which you create via

```shell
docker network create hetida-designer-network
```

#### Database

The backend stores components, workflows etc. in a PostgreSQL database. Run

```shell
docker run -d --name hetida-designer-db --network hetida-designer-network \
  -e POSTGRES_DB=hetida_designer_db -e POSTGRES_USER=hetida_designer_dbuser \
  -e POSTGRES_PASSWORD=hetida_designer_dbpasswd \
  -v hetida_designer_postgres_data:/var/lib/postgresql postgres:18
```

to run it. The backend uses it with its default database settings, see [Database Configuration](../deployment_operation/database_configuration.md).

#### Backend and runtime image

Backend and runtime use the same image. Run `docker build -t hetida/runtime -f ./Dockerfile-runtime .` to build it.

#### Runtime

Run

```shell
docker run -d --name hetida-designer-runtime --network hetida-designer-network \
  -e HD_IS_BACKEND_SERVICE=false -e HD_USE_AUTH=false \
  -p 127.0.0.1:8091:8090 hetida/runtime
```

to run the runtime. After this the runtime OpenAPI UI is available at http://127.0.0.1:8091/docs.

#### Backend

Run

```shell
docker run -d --name hetida-designer-backend --network hetida-designer-network \
  -e HD_IS_RUNTIME_SERVICE=false -e HD_USE_AUTH=false \
  -p 127.0.0.1:8080:8090 hetida/runtime
```

to run the backend. It prepares the database at its start and executes components and workflows via the runtime container. After this the backend OpenAPI UI is available at http://127.0.0.1:8080/docs.

#### Backend + Runtime as one container

Instead of separate backend and runtime containers, you can run both in one container via

```shell
docker run -d --name hetida-designer-backend --network hetida-designer-network \
  -e HD_USE_AUTH=false \
  -p 127.0.0.1:8080:8090 hetida/runtime
```

After this the combined backend + runtime OpenAPI UI is available at http://127.0.0.1:8080/docs.

#### Frontend

1. Run `docker build -t hetida/frontend -f ./Dockerfile-frontend .` to build the image.
2. Run

    ```shell
    docker run -d --name hetida-designer-frontend --network hetida-designer-network \
      -p 127.0.0.1:80:8080 hetida/frontend
    ```

    to run the frontend. It forwards requests to the backend container `hetida-designer-backend`. After this the frontend is available at http://127.0.0.1.

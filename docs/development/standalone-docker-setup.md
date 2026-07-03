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

You'll find corresponding Dockerfiles in the source code's root folder. You can start (parts of) hetida designer in standalone docker containers as follows.

#### Frontend

1. Change `apiEndpoint` in `hetida_designer_config.json` to `http://localhost:8080/api`.
2. Run `docker build -t hetida/frontend -f ./Dockerfile-frontend .` to build the image.
3. Run `docker run -d -p 127.0.0.1:80:80 hetida/frontend` to run the frontend image. (use `-d` flag to run container in background)

#### Backend

1. Run `docker build -t hetida/backend -f ./Dockerfile-runtime .` to build the image.
2. Run `docker run -e HD_IS_RUNTIME_SERVICE=false --network hetida-designer-network -p 127.0.0.1:8080:8090 hetida/backend` to run the backend image. (use -d flag to run container in background). After this the backend OpenAPI UI is available at http://127.0.0.1:8090/docs.

#### Runtime

1. Run `docker build -t hetida/runtime -f ./Dockerfile-runtime .` to build the image.
2. Run `docker run -e HD_IS_BACKEND_SERVICE=false -p 127.0.0.1:8091:8090 hetida/runtime` to run the runtime image (use -d flag to run container in background). After this the runtime OpenAPI UI is available at http://127.0.0.1:8091/docs.

#### Backend + Runtime as one container
1. Run `docker build -t hetida/backend_runtime -f ./Dockerfile-runtime .` to build the image.
2. Run `docker run -p 127.0.0.1:8092:8090 hetida/backend_runtime` to run the image (use -d flag to run container in background). After this the combined backend + runtime OpenAPI UI is available at http://127.0.0.1:8092/docs.


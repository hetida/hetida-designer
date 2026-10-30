# Development Setup

## Contributing
We recommend to read our [contributor guidelines](https://github.com/hetida/hetida-designer/blob/release/CONTRIBUTING.md)
if you'd like to contribute your improvements back to us.

## Nix Shell based development setup

Using [nix](https://nixos.org/) it is possible to have a development setup where all services are started simultaneously in "dev mode" (aka: watching for changes and restarting accordingly).

First install nix as recommended for your operating system.

Then run

```shell
nix-shell --pure
```
to start a nix shell and afterwards

```shell
overmind s
```

to start all services. You can abort overmind using ++ctrl+s++ and leave the nix-shell using ++ctrl+d++ in most terminals.

!!! note
    The PostgreSQL database of this setup is recreated empty at each start of its overmind process, e.g. at each `overmind s`. So all components, workflows and further data stored in it are lost, except for the base components and workflows which the backend deploys again.


## Containerized development setup

### Setting up a docker development environment

Make sure you have read and understood how to set up and start hetida designer using docker compose (see [get started docs](../get_started.md)) and [docker](./standalone-docker-setup.md).

This is important, as usually you'll not want to develop on all three submodules (backend, rutnime, frontend) of the application at the same time. A partial docker setup will help you to have your development environment up and running quickly, as you'll only work locally on the
submodule that you'd like to change.

There is a `docker-compose-dev.yml` that builds images from your local development files which you can use via

```shell
docker compose -f docker-compose-dev.yml up -d
```

!!! tip
    The dockerfiles assume a linux/amd64 platform/architecture, you may have to turn on / configure emulation if you are building on another architecture, for example on ARM based environments.

Once you have the application running, only stop the container containing the submodule that you want to work on. We use a monorepo approach, so all submodules can be found in the same [git repository](https://github.com/hetida/hetida-designer).

### Running single services in development mode

Depending on whether you want to work on the frontend, backend, or runtime, find the
instructions on setting up one of these modules for development below.

#### Frontend

Dependencies: Node 22.23.4 and npm 10.9.x (other versions are not tested).

1. Navigate to the `frontend` folder.
2. Run `npm install` to install application dependencies.
3. Run `npm run start` to run the frontend on port 4200.

The frontend subdirectory also contains end-to-end tests via playwright documented [here](https://github.com/hetida/hetida-designer/blob/release/frontend/end2end_tests.md).

#### Runtime and Backend
Dependencies: Python 3.14 (other versions are not
tested, but higher versions will probably work as well). 

You may need additional packages like a C compiler (e.g. gcc) depending on your
OS's availability of precompiled packages for numerical libraries like **numpy**
or **scipy**. That said, development on Linux is recommended.

1. Navigate to the `runtime` folder.
2. Create, sync and activate virtual environmnet: `./pipt shell`

Now a development web server using a sqlite in-memory db can be started via
```shell
HOST=127.0.0.1 PORT=8000 python main.py
```

If `HD_RUNTIME_ENVIRONMENT_FILE` is not set, `main.py` started directly like this from the `runtime` directory uses the environment file `local_dev.env` there, which sets `HD_DATABASE_URL` to the in-memory database. This database is migrated and filled with the base components and workflows at each start, also at each restart of the web server due to code changes with `DEVELOPMENT_MODE=true`. Unlike in the docker image, it does not need to be allowed via `HD_ALLOW_IN_MEMORY_DB`, but `WEB_CONCURRENCY` greater than 1 is refused with it, since each web server process would have its own in-memory database.

If you want to develop against the postgres db running in the docker compose dev environment the command is
```shell
HOST=127.0.0.1 PORT=8000  HD_DATABASE_URL="postgresql+psycopg://hetida_designer_dbuser:hetida_designer_dbpasswd@localhost:5430/hetida_designer_db" python main.py
```

The environment variable takes precedence over `HD_DATABASE_URL` from `local_dev.env`. To configure the database via `HD_DB_HOST`, `HD_DB_PORT` etc. instead, additionally set `HD_RUNTIME_ENVIRONMENT_FILE=""`, since `HD_DATABASE_URL` takes precedence over them, see [Database Configuration](../deployment_operation/database_configuration.md). Before starting the web server, `main.py` prepares the database like in the docker image, see [database preparation](../deployment_operation/database_configuration.md#database-preparation-at-backend-start).

In both cases the OpenAPI UI can be found at http://localhost:8000/docs. Set `DEVELOPMENT_MODE=true` to restart the web server automatically on code changes.

!!! note
    This starts runtime+backend combined. If you only want one of both you have to deactivate the other one by setting one of the environment variables `HD_IS_BACKEND_SERVICE` or `HD_IS_RUNTIME_SERVICE` to `false`.

When deactivating the backend endpoints you do not need to specify a database connection URL.

#### Running Runtime + Backend Tests

1. Navigate to the `runtime` folder.
2. Activate virtual environment with `./pipt shell`.
3. Run `./run test`.

## Frontend Development

See

* [frontend coding standards](https://github.com/hetida/hetida-designer/blob/release/frontend/CODING_STANDARDS.md)
* [end to end tests](https://github.com/hetida/hetida-designer/blob/release/frontend/end2end_tests.md)


## Backend/Runtime Development

See 

* [runtime Readme](https://github.com/hetida/hetida-designer/blob/release/runtime/README.md)
* [runtime coding standards](https://github.com/hetida/hetida-designer/blob/release/runtime/CODING_STANDARDS.md)
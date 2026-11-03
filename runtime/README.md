# Hetida Designer Runtime and Backend

The hetida designer runtime is the hetida designer submodule responsible for execution of Python code and workflows.

The hetida designer backend is the submodule which offers the API for frontend and for 3rd party services.

Both are written in Python and their code resides in the runtime subdirectory.

> **Note**: All described command line commands in this file assume that the runtime subdirectory of the hetida designer repository is the current working directory.

## Development Setup

Make sure Python 3.14 is installed and available on your path. You may need additional packages like a C compiler (e.g. gcc) depending on your OS's availability of precompiled packages for numerical libraries like **numpy** or **scipy**.

We heavily recommend Linux as operating system for development. In particular we point out that locked dependency files in this repository are created only for Linux environments with CPython which corresponds to the targeted Docker image environment.

1. Navigate to the `runtime` folder.
2. Create, sync and activate virtual environmnet: `./pipt shell`

Now a development web server using a sqlite in-memory db can be started via

```
python main.py
```

Run

```
HD_USE_AUTH=false python main.py
```

to start it with auth deactivated.

If `HD_RUNTIME_ENVIRONMENT_FILE` is not set, `main.py` started directly like this from the `runtime` directory uses the environment file `local_dev.env` there, which sets `HD_DATABASE_URL` to the in-memory database. This database is migrated and filled with the base components and workflows at each start, also at each restart of the web server due to code changes with `DEVELOPMENT_MODE=true`. Unlike in the docker image, it does not need to be allowed via `HD_ALLOW_IN_MEMORY_DB`, but `WEB_CONCURRENCY` greater than 1 is refused with it, since each web server process would have its own in-memory database.

If you want to develop against the postgres db running in the docker compose dev environment the command is

```
HD_DATABASE_URL="postgresql+psycopg://hetida_designer_dbuser:hetida_designer_dbpasswd@localhost:5430/hetida_designer_db" python main.py
```

The environment variable takes precedence over `HD_DATABASE_URL` from `local_dev.env`. To configure the database via `HD_DB_HOST`, `HD_DB_PORT` etc. instead, additionally set `HD_RUNTIME_ENVIRONMENT_FILE=""`, since `HD_DATABASE_URL` takes precedence over them, see [Database Configuration](../docs/deployment_operation/database_configuration.md). Before starting the web server, `main.py` prepares the database like in the docker image, see [database preparation](../docs/deployment_operation/database_configuration.md#database-preparation-at-backend-start).

In both cases the OpenAPI UI can be found at http://localhost:8000/docs. Set `DEVELOPMENT_MODE=true` to restart the web server automatically on code changes.

Note that this starts runtime+backend combined. If you only want one of both you have to deactivate the other one by setting one of the environment variables `HD_IS_BACKEND_SERVICE` or `HD_IS_RUNTIME_SERVICE` to `false`.

When deactivating the backend endpoints you do not need to specify a database connection URL.

Most following commands assume that that the virtual environment is active (step 2).

## Dependency Management

For the hetida designer runtime/backend we rely on [pip-tools](https://github.com/jazzband/pip-tools) for depedency management. We use a wrapper script called `pipt` to faciliate working with pip-tools.
Pip-tools supports having a tree of interdependent dependency sets such that each set is locked with its locked dependent dependency sets as constraints. This is called ["layered dependencies"](https://github.com/jazzband/pip-tools#workflow-for-layered-requirements) in the pip-tools documentation.

This feature allows users of the runtime to [merge their specific Python dependencies](../docs/custom_python_dependencies.md) in their own docker images.

### Basic dependency management

Abstract dependencies can be added and locked using the `./pipt add` subcommand, e.g.

```
./pipt add 'requests>=2'
```

or

```
./pipt add --dev pytest
```

with deactivated virtual environment.

Afterwards (re)activating the environment with `./pipt shell` will automatically sync to the locked versions.

### Upgrade Dependencies

Upgrade and lock all dependencies with deactivated virtual environmnet via

```
./pipt upgrade
```

This upgrades the locked dependency files `requirements-base.txt`, `requirements.txt` and `requirements-dev.txt`.

After that

```
./pipt shell
```

will automatically sync and activate your environment.

## QA

### <a name="runtime-tests"></a> Tests

With activated virtual environment, run

```
python -m pytest --cov=hetdesrun tests
```

from the runtime directory to obtain unit test results including coverage report.

### Code Quality Check / Linting

Ruff can be used to check static code quality during development:

```
ruff hetdesrun tests
```

Used rules are controlled through the `pyproject.toml` file in the runtime directory of the repository.

It is recommended to set up your editor/IDE to use ruff from the virtual environment with this `pyproject.toml`.

### Code formatting

As code formatter, [black](https://github.com/ambv/black) is used in combination with ruff for import sorting. It is recommended to configure your IDE to automatically format Python code with black during save and sort imports using ruff. See the `format` subcommand in the `run`
script.

### Type Hints

Runtime/Backend code is currently mostly type hinted. You may use [mypy](http://mypy-lang.org/) for static type checking via

```
python3 -m mypy hetdesrun
```

The Mypy configuration can be found in `mypy.ini` file in /runtime directory.

We recommend to set up your IDE to use mypy with this mypy configuration file.

### Run script

The runtime directory contains a `run` bash script with multiple subcommands which may faciliate using the qa tools mentioned above. Run `./run usage` for further information.

In particular the `./run check` command runs several checks exiting with non-zero status if one of them fails.

### Quality Gates: Github actions

Some of the qa tools mentioned above are run as part of github actions to ensure code quality.

## Documentation

Documentation is built via [zensical](https://zensical.org/) from the markdown files in `/docs`. Activate the runtime virtual environment as described above from within the `/runtime` directory. Than change to the git repo main directory and run

```
zensical serve
```

Now a preview of the generated site is available under http://localhost:8000.

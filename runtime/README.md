# Hetida Designer Runtime and Backend

The hetida designer runtime is the hetida designer submodule responsible for execution of Python code and workflows.

The hetida designer backend is the submodule which offers the API for frontend and for 3rd party services.

Both are written in Python and their code resides in the runtime subdirectory.

> **Note**: All described command line commands in this file assume that the runtime subdirectory of the hetida designer repository is the current working directory.

## Development Setup
Make sure Python 3.12 is installed and available on your path. You may need additional packages like a C compiler (e.g. gcc) depending on your OS's availability of precompiled packages for numerical libraries like **numpy** or **scipy**. 

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

If you want to develop against the postgres db running in the docker-compose dev environment the command is
```
HD_DATABASE_URL="postgresql+psycopg2://hetida_designer_dbuser:hetida_designer_dbpasswd@localhost:5430/hetida_designer_db" python main.py
```

In both cases the OpenAPI UI can be found at http://localhost:8000/docs.

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

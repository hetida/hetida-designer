# Hetida Designer Python Demo Adapter

The hetida designer Python demo adapter is an example for a generic REST adpater that provides and
receives data to/from workflows during execution.

> Note: All described command line commands in this file assume that the demo-adapter-python
subdirectory of the hetida designer repository is the current working directory.

## Development Setup
Make sure Python 3.9 is installed and available on your path. You may need additional packages like a C compiler (e.g. gcc) depending on your OS's availability of precompiled packages for numerical libraries like **numpy** or **scipy**.

We recommend Linux as operating system for development. In particular we point out that locked dependency files in this repository are created only for Linux environments with CPython.

1. Navigate to the `demo-adapter-python` folder.
2. Create, sync and activate virtual environmnet: `./pipt shell`

Now a development web server can be started via `python main.py`.

Most following commands assume that that the virtual environment is active (step 2).

## Dependency Management
For the hetida designer python demo adapter we rely on [pip-tools](https://github.com/jazzband/pip-tools) for depedency management. We use a wrapper script called `pipt` to faciliate working with pip-tools.

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

### <a name="demo-adapter-python-tests"></a> Tests
With activated virtual environment, run
```
python -m pytest --cov=demo_adapter_python tests
```
from the demo-adapter-python directory to obtain unit test results including coverage report.

### Code Quality Check
Pylint can be used to check static code quality during development:
```
pylint demo_adapter_python
```
Used pylint rules are controlled through the `pylintrc` file in the demo-adapter-python directory of the repository.

It is recommended to set up your editor/IDE to use pylint with this `pylintrc`.

### Code formatting
As code formatter, [black](https://github.com/ambv/black) is used. It is recommended to configure your IDE to automatically format Python code with black during save. Currently black formatting is not enforced as part of the build process.

### Type Hints
Python demo adapter code is currently mostly type hinted. You may use [mypy](http://mypy-lang.org/) for static type checking via
```
python -m mypy demo_adapter_python
```
The Mypy configuration can be found in `mypy.ini` file in /demo-adapter-python directory.

We recommend to set up your IDE to use mypy with this mypy configuration file.

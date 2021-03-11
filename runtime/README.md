# Hetida Designer Runtime

The hetida designer runtime is the hetida designer submodule responsible for execution of Python code and workflows. It is written in Python itself.

> Note: All described command line commands in this file assume that the runtime subdirectory of the hetida designer repository is the current working directory.

## Development Setup
Make sure Python 3.8 is installed and available on your path. You may need additional packages like a C compiler (e.g. gcc) depending on your OS's availability of precompiled packages for numerical libraries like **numpy** or **scipy**. We recommend Linux as operating system for development.

1. Navigate to the `runtime` folder.
2. Create virtual environment: `python -m venv venv`
3. Activate virtual environment: `source venv/bin/activate`
4. Install dependency management tooling: `python3 -m pip install pip==21.0.1 pip-tools==5.5.0`
5. Install development dependencies: `pip-sync ./requirements.txt ./requirements-dev.txt`

All following commands assume that that the virtual environment is active (step 3).

## Dependency Management
For the hetida designer runtime we rely on [pip-tools](https://github.com/jazzband/pip-tools) for depedency management.
Pip-tools supports having a tree of interdependant dependency sets such that each set is locked with its locked dependant dependency sets as constraints. This is called ["layered dependencies"](https://github.com/jazzband/pip-tools#workflow-for-layered-requirements) in the pip-tools documentation.

This feature allows users of the runtime to merge their specific Python dependencies in their own docker images.

TODO: Explicit documentation of merging of custom dependencies via pip-tools layered dependency mechanism.

### Basic pip-tools usage
Abstract dependencies go into `requirements.in` while abstract development-only dependencies (test libraries, code quality check libraries etc) should be placed in `requirements-dev.in`.

All following commands are run with activated development virtual environment.

#### Locking Dependencies
Lock all dependencies via
```
rm requirements.txt requirements-dev.txt && pip-compile --generate-hashes && pip-compile --generate-hashes requirements-dev.in
```
This updates the locked dependency files `requirements.txt` and `requirements-dev.txt`.

#### Updating development virtual environment
Update your development virtual environment to the current locked dependencies via 

```
pip-sync requirements.txt requirements-dev.txt
```

#### Upgrade dependencies
All dependencies are upgraded via
```
pip-compile --generate-hashes --upgrade && pip-compile --generate-hashes --upgrade requirements-dev.in
```

### <a name="runtime-tests"></a> Tests
With activated virtual environment, run
```
python -m pytest --cov=hetdesrun tests
```
from the runtime directory to obtain unit test results including coverage report.
Additionally there are unit tests / doctests for the basic components:

```
python -m pytest --doctest-modules components
```

### Code Quality Check
Pylint can be used to check static code quality during development:
```
pylint hetdesrun
```
Used pylint rules are controlled through the `pylintrc` file in the runtime directory of the repository.

It is recommended to set up your editor/IDE to use pylint with this `pylintrc`.

### Code formatting
As code formatter, [black](https://github.com/ambv/black) is used. It is recommended to configure your IDE to automatically format Python code with black during save. Currently black formatting is not enforced as part of the build process.

### Type Hints
Runtime code is currently mostly type hinted. You may use [mypy](http://mypy-lang.org/) for static type checking via
```
python3 -m mypy hetdesrun
```
The Mypy configuration can be found in `mypy.ini` file in /runtime directory.

We recommend to set up your IDE to use mypy with this mypy configuration file.

# Hetida Designer Python Demo Adapter

The hetida designer Python demo adapter is an example for a generic REST adpater that provides and
receives data to/from workflows during execution.

> Note: All described command line commands in this file assume that the demo-adapter-python
subdirectory of the hetida designer repository is the current working directory.

## Development Setup
Make sure Python 3.9 is installed and available on your path. You may need additional packages like a C compiler (e.g. gcc) depending on your OS's availability of precompiled packages for numerical libraries like **numpy** or **scipy**. We recommend Linux as operating system for development.

1. Navigate to the `demo-adapter-python` folder.
2. Create virtual environment: `python3.9 -m venv venv`
3. Activate virtual environment: `source venv/bin/activate`
4. Install dependency management tooling: `python -m pip install pip==21.3.1 pip-tools==6.4.0 wheel==0.37.0`
5. Install development dependencies: `pip-sync ./requirements.txt ./requirements-dev.txt`

Now a development web server can be started via `python main.py`.

All following commands assume that that the virtual environment is active (step 3).

## Dependency Management
For the hetida designer python demo adapter we rely on [pip-tools](https://github.com/jazzband/pip-tools) for depedency management.

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
python3 -m mypy demo_adapter_python
```
The Mypy configuration can be found in `mypy.ini` file in /demo-adapter-python directory.

We recommend to set up your IDE to use mypy with this mypy configuration file.

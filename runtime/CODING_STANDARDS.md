# hetida designer Runtime - Coding Standards

Our most important code style rule is: **Write code for humans.** Make your code
as readable, maintainable and debuggable as possible. Rather than sticking to the letter of rigid coding standards ask yourself: "What is the solution that provides most benefit to our users with the lowest total cost of ownership?"

## Python Coding Standard
The core of our coding standards is of course [PEP8](https://www.python.org/dev/peps/pep-0008/).

We prefer more explicit code over some very Python-idiomatic structures where this may increase readability for developers from other languages (since Hetida Designer is a multi-language project). An example is Python's boolean evaluation of any type: We prefer `if my_object is None:` over `if my_object:`.

## Specific Topics

> **Note**: All described command line runs in this file assume that the runtime directory is the current working directory and a development virtual environment is set up and activated.

### Code formatting
As code formatter, [black](https://github.com/ambv/black) is used. It is recommended to configure your editor/IDE to automatically format Python code with black during save. Currently black formatting is not enforced as part of the build process.


### Code Quality Check
Pylint is recommended to be used to check static code quality. See [Runtime Readme](./README.md) for details on running and configuring pylint. Used pylint rules are controlled through the `pylintrc` file in the runtime directory of the repository.

Pylint isn't perfect. We sometimes need to suppress its warnings manually through comments
in code like
```
...
try: # pylint: disable=broad-except
...
```
Or we add general exceptions to the `pylintrc`. 

Note that currently build processes do not include pylint checking, we may add that in the future to enforce code quality according to the `pylintrc` file.

It is recommended to set up your editor/IDE to use pylint with this `pylintrc`.


### Unit Tests
See [Runtime Readme](./README.md) for details on running tests.

New code for the runtime should always come with appropriate unit tests and contributions should at best increase overall test coverage.


### Type Hints
Currently good part of the source code is equipped with [type hints](https://www.python.org/dev/peps/pep-0484/). Build processes do not include static type checking.

For the hetdesrun package we are striving to gradually add more type hints during ongoing development and intend to fully employ [mypy](http://mypy-lang.org/) for static type checking. (hint: contributions are very welcome! You may start from `# type: ignore` comments). See the [Runtime Readme](./README.md) on running static type checks and configuration.

Note that we do not plan to add type hints to the code of base components, since they should provide easily readable / beginner friendly examples for starting out on writing custom components.

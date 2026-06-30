## Logging in user / component code

When writing component code you can use logging in the usual and recommended way of the Python stdlib logging module:

```python
...

import logging
logger = logging.getLogger(__name__)

...

def main(...):
    ...
    logger.info("My log message")

```

The hetida designer runtime enriches the logs with execution context information (component name, version, id, operator information) as described for system-generated logs above.

In addition to the log output of the runtime service, these logs can also be viewed in the test execution result display. If you switch to the raw response view you can also see the additional execution context information in the raw json response.

## Component Code Logging settings

See [logging configuration documentation](../../deployment_operation/logging.md#component-code-logging) for configuring log level and maximum log messages for component code logging.

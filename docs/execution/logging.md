# Reading Log Messages of Workflow and Component Executions


## Log messages by hetida designer
Log messages issued by hetida designer during the execution of a component or workflow contain the corresponding job id at the end of the message.

If the calculation of the output of a certain operator within a workflow is started and especially if an error occurs, the type (`tr type`), id (`tr id`), name (`tr name`), and tag (`tr tag`) of the transformation as well as the hierarchical nesting succession of the operator ids (`op id(s)`) and names (`op name(s)`) are additionally specified. The former helps to find and open e.g. a component via the sidebar in order to search for the error in the code, the latter helps to recognize at which point in the workflow and thus also with which input the error arose.

Example:
```
2025-06-25 15:31:02,670 1913209 DEBUG: Starting computation [in /home/testinstance/runtime/hetdesrun/runtime/engine/plain/workflow.py:235, job_id=08729294-11cb-48c6-86f9-6ff5b74e7514,
     tr type: COMPONENT, tr id: 7a1a818f-fa89-6062-1e0e-fc80539bbe0a, tr name: Pass Through (DataFrame), tr tag: 1.0.0,
     op id(s): \9733454a-0dba-466a-a6ba-66d428247fb9\f56bc623-4d6a-45f8-a082-64ab6eee13a4\,
     op name(s): \Test\Pass Through (DataFrame)\
 ]
```

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

The hetida designer runtime enriches the logs with the execution context information (component name, version, id, operator information), just like the hetida designer log messages described above.

In addition to the log output of the runtime service, these logs can also be viewed in the test execution result display. If you switch to the raw response view you can also see the additional execution context information in the raw json response.

Note that by default the log level is filtered against the runtime service's log level
but this can be configured separately through the runtime's environment variable `USER_COMPONENT_CODE_LOG_LEVEL` (e.g. `DEBUG`, `INFO`, `WARNING`, `ERROR`).

Furthermore `USER_COMPONENT_CODE_LOG_MAX_LEN` can be configured to only display a limited subset of the most recent log messages.

# Logging settings

hetida designer exposes several environment variables controlling logging details. See the [configuration code](../../runtime/hetdesrun/webservice/config.py) for details and descriptions.
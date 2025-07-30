# Reading Log Messages of Workflow and Component Executions


## Log entries by hetida designer
Log records issued by hetida designer during the execution of a component or workflow are structured output.  
They are made up of a JSON containing at least the following fields, in this order:
* timestamp
* level
* message
* logger (name of the logger)
* func_name (name of the function the message originates from)
* filename
* lineno (line number)
* job_id

If the calculation of the output of a certain operator within a workflow is started and especially if an error occurs, the type (`tr_type`), id (`tr_id`), name (`tr_name`), and tag (`tr_tag`) of the transformation as well as the hierarchical nesting succession of the operator ids (`op_id(s)`) and names (`op_name(s)`) are additionally specified. In the case of an error, an `exception` field is also specified. The transformation (`tr`) information helps to find and open e.g. a component via the sidebar in order to search for the error in the code, the operator (`op`) information helps to recognize at which point in the workflow and thus also with which input the error arose.

A log entry may contain additional fields, e.g. `execution_result_response`. Additional fields are appended to the entry in alphabetical order, after the last main field. This could be `job_id`, `op_name` or `exception`.

Example log entry:
```json
{
    "timestamp": "2025-07-30T11:45:55.704334Z",
    "level": "debug",
    "message": "Starting computation",
    "logger": "internal_runtime_execution_logger",
    "func_name": "result",
    "filename": "workflow.py",
    "lineno": 382,
    "job_id": "861b3b9845c6428eb0814bd146013a41",
    "tr_id": "704ebd70-e840-45fb-9053-4d383a8e91f0",
    "tr_name": "COMPONENT EXECUTION WRAPPER WORKFLOW",
    "tr_tag": "1.0.0",
    "tr_type": "WORKFLOW",
    "op_id": "\\d10ec25b-93f0-4244-856e-e337bfe02527\\",
    "op_name": "\\COMPONENT EXECUTION WRAPPER WORKFLOW\\",
}
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

The hetida designer runtime enriches the logs with the execution context information (component name, version, id, operator information) and transforms them into structured entries. These entries are equivalent to the hetida designer log entries described above.

In addition to the log output of the runtime service, these logs can also be viewed in the test execution result display. If you switch to the raw response view you can also see the additional execution context information in the raw json response.

Note that by default the log level is filtered against the runtime service's log level
but this can be configured separately through the runtime's environment variable `USER_COMPONENT_CODE_LOG_LEVEL` (e.g. `DEBUG`, `INFO`, `WARNING`, `ERROR`).

Furthermore `USER_COMPONENT_CODE_LOG_MAX_LEN` can be configured to only display a limited subset of the most recent log messages.

# Logging settings

hetida designer exposes several environment variables controlling logging details. See the [configuration code](../../runtime/hetdesrun/webservice/config.py) for details and descriptions.
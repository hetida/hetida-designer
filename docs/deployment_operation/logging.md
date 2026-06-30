# Logging

## Log entries by hetida designer

During the execution of a component or workflow, hetida designer emits structured log records.  
These records are logged as a JSON, containing at least the following fields:

- timestamp
- level
- message
- logger (name of the logger)
- func_name (name of the function the message originates from)
- filename
- lineno (line number)
- job_id

If the calculation of the output of a certain operator within a workflow is started and especially if an error occurs, the type (`tr_type`), id (`tr_id`), name (`tr_name`), and tag (`tr_tag`) of the transformation as well as the hierarchical nesting succession of the operator ids (`op_id(s)`) and names (`op_name(s)`) are additionally provided. In the case of an error, an `exception` field is also provided. The fields prefixed with `tr` help to find and open e.g. a component via the sidebar in order to search for the error in the code, the fields prefixed with `op` help to recognize at which point in the workflow the error arose.

A log entry may contain additional fields, e.g. `execution_result_response`.

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
  "op_name": "\\COMPONENT EXECUTION WRAPPER WORKFLOW\\"
}
```

## Logging configuration

hetida designer exposes several environment variables controlling logging details. See the [configuration code](https://github.com/hetida/hetida-designer/blob/release/runtime/hetdesrun/webservice/config.py) for details and descriptions.

## Component Code Logging

See [component logging](../user_guide/component_writing/component_code_logging.md).

Note that by default the log level for component code logging is filtered against the runtime service's log level but this can be configured separately through the runtime's environment variable `USER_COMPONENT_CODE_LOG_LEVEL` (e.g. `DEBUG`, `INFO`, `WARNING`, `ERROR`).

Furthermore `USER_COMPONENT_CODE_LOG_MAX_LEN` can be configured to only display a limited subset of the most recent log messages.

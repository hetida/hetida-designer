# Structuring Exceptions

When a workflow/component raises an exception during execution, this exception is captured by hetida designers and suitable information about the error (like its message) is attached to the execution response json.

In production scenarios it is often necessary to react programmatically to certain situations / errors. For this, parsing the error message text for details is not optimal. The service/component triggering the execution often needs a more structured access to such details and component code authors need a way to provide this information.

Therefore hetida designer provides the following ways to component code authors to raise their own exceptions explicitely enriched with information to pe propagated in a structured way into the execution json response.

## ComponentException Class
Generally, a `ComponentException` class is available, which can be enriched with an optional error code and optional extra information besides the error message itself.

The error code can be either an integer or a string. The extra information must be a dictionary. Both will then be accessible in the response.

The following example shows how this exception can be used in component code:

```python
from hetdesrun.runtime.exceptions import ComponentException

# ...

def main(*, dividend, divisor):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    if divisor == 0:
        raise ComponentException("The divisor must not equal zero!", error_code=422)
    return {"result": dividend / divisor}
```

Executing a component with the above code and inputs `1` and `0` results in a json object like the following for the attribute `error` in the response.

```json
"error": {
    "type": "ComponentException",
    "error_code": 422,
    "message": "The divisor must not equal zero!",
    "extra_information": null,
    "process_stage": "EXECUTING_COMPONENT_CODE",
    "operator_info": {
        "transformation_info": {
            "id": "c4dbcc42-eaec-4587-a362-ce6567f21d92",
            "name": "Raise Exception",
            "tag": "0.1.0",
            "type": "COMPONENT"
        },
        "hierarchy_in_workflow": {
            "by_name": [
                "COMPONENT EXECUTION WRAPPER WORKFLOW",
                "Raise Exception Example Component"
            ],
            "by_id": [
                "31d1979f-57c7-4fa8-82b4-2b6dec5f5265",
                "c84fb859-5c91-44a0-8d8b-6657b43ab5de"
            ]
        }
    },
    "location": {
        "file": "component code",
        "function_name": "main",
        "line_number": 29
    }
}
```

Since the exception is raised within the component code, the `file` attribute of the `location` is just `component code` (in all other cases it is the path to the corresponding file).

The `process_stage` attribute can take one of the following values:
* PARSING_WORKFLOW
* LOADING_DATA_FROM_ADAPTERS
* PARSING_LOADED_DATA
* EXECUTING_COMPONENT_CODE
* SENDING_DATA_TO_ADAPTERS 
* ENCODING_RESULTS_TO_JSON

Of course, only exceptions raised in the process stage `EXECUTING_COMPONENT_CODE` cause errors with the `operator_info` attribute.

### Raising Component Input Validation Errors

One of the most frequent use cases for exceptions is dealing with unexpected input. For this there is a subclass of `ComponentException` called `ComponentInputValidationException`. Components should check their inputs and raise this exception if some of them are invalid.

This exception has the additional input parameter `input_names`, which should be filled with the list of component input names that are invalid when raised. It is then added to the `extra_information` dictionary under the key `input_names`.

It is of course also possible to inherit again from this exception or from `ComponentException` itself.

```python
from hetdesrun.runtime.exceptions import ComponentInputValidationException


class SeriesTypeException(ComponentInputValidationException):
    """Exception in case of unexpected value type"""

# ...

def main(*, series):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    if len(series) == 0:
        raise ComponentInputValidationException(
            "The series must not be empty!",
            error_code="EmptySeries",
            input_names=["series"],
        )
    if series.values.dtype not in ("int64", "float64"):
        raise SeriesTypeException(
            "Excpeted series with values of type int or float, but got type "
            + str(series.values.dtype),
            error_code="WrongKindOfSeries",
            input_names=["series"],
        )
    return {"result": series.mean()}
```

```json
"error": {
    "type": "ComponentInputValidationException",
    "error_code": "EmptySeries",
    "message": "The series must not be empty!",
    "extra_information": {"input_names": ["series"]},
    "process_stage": "EXECUTING_COMPONENT_CODE",
    "operator_info": {
        "transformation_info": {
            "id": "d9e64b95-b7fa-4e0d-b284-41cc6a5dfaf9",
            "name": "Raise Inherited Exception",
            "tag": "0.1.0",
            "type": "COMPONENT"
        },
        "hierarchy_in_workflow": {
            "by_name": [
                "Wrapper Workflow",
                "Raise Inherited Exception"
            ],
            "by_id": [
                "2ddb3898-60a5-4ef6-bf6f-f803f370df8d",
                "233911db-5b9d-41e6-b217-1b1bbe36df2b"
            ]
        }
    },
    "location": {
        "file": "component code",
        "function_name": "main",
        "line_number": 34
    }
}
```

## Not using the predefined classes
To develop the component code independently of the hetdesrun library, exceptions that are handled similarly can be defined locally in the component code as follows.

First, such an exception must of course enable initialization with a message and an error code (and possibly input_names).

```python
class SeriesTypeException(Exception):
    __is_hetida_designer_exception__ = True

    def __init__(self, msg, error_code, input_names, **kwargs) -> None:
        self.error_code = error_code
        self.extra_information = {"input_names": input_names}
        super().__init__(msg, **kwargs)
```

... TODO ...

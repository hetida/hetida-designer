# Structuring Exceptions

Usually in python projects exceptions are structured by inheritance and can be imported where needed.
Since code is capsulated in components in the hetida designer, importing definitions is more complicated.
Re-defining exceptions in each component would be both tidious and error prone.

Therefore the `ComponentException` is defined in the hetida designer runtime, which can be enriched with an error code instead.
The error code can be either an integer or a string.
It is the responsibility of the authors of component code to use the error code in a way that structures the exceptions.

The following example shows how this exception can be used in the component code:

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

Executing a component with the above code and the inputs `1` and `0` will yield a json such as the following for the attribute `error` in the response. 

```json
"error": {
    "type": "ComponentException",
    "error_code": 422,
    "message": "The divisor must not equal zero!",
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
                "Wrapper Workflow",
                "Raise Exception"
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

In such a case, where the exception is raised inside the component code the attribute `file` of the `location` will just be `component code` in all other cases it will be the path to the corresponding file.

The attribute `process_stage` can take one of the following values:
* PARSING_WORKFLOW
* LOADING_DATA_FROM_ADAPTERS
* PARSING_LOADED_DATA
* EXECUTING_COMPONENT_CODE
* SENDING_DATA_TO_ADAPTERS 
* ENCODING_RESULTS_TO_JSON

Only exceptions raised in the process stage `EXECUTING_COMPONENT_CODE` result in errors with the attributes `operator_info`, for the other porcess stages that information is not accessible.

Since the most frequent application for exceptions are about handling unexpected inputs, there is also the  `ComponentInputValidationException` inheriting from `ComponentException` defined in the hetida designer runtime.
It is of course also possible to inherit again from this exception or from the `ComponentException` itself.

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
            "The divisor must not equal zero!", error_code="EmptySeries"
        )
    if series.values.dtype not in ("int64", "float64"):
        raise SeriesTypeException(
            "Excpeted series with values of type int or float, but got type "
            + str(series.values.dtype),
            error_code="WrongKindOfSeries",
        )
    return {"result": series.mean()}
```

```json
"error": {
    "type": "ComponentInputValidationException",
    "error_code": "EmptySeries",
    "message": "The divisor must not equal zero!",
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
        "line_number": 32
    }
}
```

Importing the `ComponentException` or `ComponentInputValidationException` means that the component code cannot be executed externally.
To enable both, using the error code and executing the component code externally, an exception must be defined locally in the component code.
This component must obviously allow initialization with a message and an error code.
The name can be chosen freely.

```python
class ComponentException(Exception):
    def __init__(self, msg, error_code, **kwargs) -> None:
        self.error_code = error_code
        super().__init__(msg, **kwargs)
```

The most common mistake to directly return the result instead of a dictionary with the component output names as keys

```python
return series.mean()
```

or a misspelled output name, e.g. due to a changed output name, which has not yet been updated in the output dictionary

```python
return {"mean": series.mean()}
```

will result in a `RuntimeExecutionError`:

```json
"error": {
    "type": "RuntimeExecutionError",
    "error_code": null,
    "message": "Component function of component instance \\f7c20ae9-5141-447c-8ae8-086edfc8d231\\76cf9d97-4007-48d8-8ca5-89320df9caab\\ from component \\Wrapper Workflow\\Raise Inherited Exception\\ did not return an output dict!",
    "process_stage": "EXECUTING_COMPONENT_CODE",
    "operator_info": {...},
    "location": {
        "file": "/app/hetdesrun/runtime/engine/plain/workflow.py",
        "function_name": "_run_comp_func",
        "line_number": 209
    }
}
```

or `KeyError`, respectively:

```json
"error": {
    "type": "KeyError",
    "error_code": null,
    "message": "'result'",
    "process_stage": "EXECUTING_COMPONENT_CODE",
    "operator_info": {...},
    "location": {
        "file": "/app/hetdesrun/runtime/engine/plain/workflow.py",
        "function_name": "result",
        "line_number": 384
    }
}
```

If the data type of an output and the type of the provided data do not match, it depends on the type of adapter and expected data type the what happens.
With the direct provisioning adapter the result will just be displayed without an exception.
In case of a general custom adapter it depends on the implementation of that adapter if an exception is raised.
In case of a generic REST adapter an exception will be raised in the generic rest adapter part of the runtime if the component output datatype is `SERIES`, `DATAFRAME` or `MULTITSFRAME`:
```json
"error": {
    "type": "AdapterOutputDataError",
    "error_code": null,
    "message": "Did not receive Pandas Series as expected from workflow output. Got <class 'numpy.float64'> instead.",
    "process_stage": "SENDING_DATA_TO_ADAPTERS",
    "operator_info": null,
    "location": {
        "file": "/app/hetdesrun/adapters/generic_rest/send_ts_data.py",
        "function_name": "ts_to_list_of_dicts",
        "line_number": 42
    }
},
```
All other data types can only be assigned to metadata sinks which are handled differently, i.e. the data is send to the adapter which then raises an exception:
```json
"error": {
    "type": "AdapterConnectionError",
    "error_code": null,
    "message": "Posting metadata to generic rest adapter endpoint http://hetida-designer-demo-adapter-python:8092/thingNodes/root.plantA/metadata/Plant%20Age%20in%20Years failed. Status code: 500. Text: Internal Server Error",
    "process_stage": "SENDING_DATA_TO_ADAPTERS",
    "operator_info": null,
    "location": {
        "file": "/app/hetdesrun/adapters/generic_rest/send_metadata.py",
        "function_name": "send_single_metadatum_to_adapter",
        "line_number": 82
    }
},
```

An error in the input wiring such as the wrong data type (`dataframe` instead of `timeseries(float)`) will lead to similar errors.

```json
"error": {
    "type": "AdapterConnectionError",
    "error_code": null,
    "message": "Requesting framelike data from generic rest adapter endpoint http://hetida-designer-demo-adapter-python:8092/dataframe failed. Status code: 404. Text: {\"detail\":\"No dataframe data available with provided id 'root.plantA.picklingUnit.influx.temp'.\"}",
    "process_stage": "LOADING_DATA_FROM_ADAPTERS",
    "operator_info": null,
    "location": {
        "file": "/app/hetdesrun/adapters/generic_rest/load_framelike.py",
        "function_name": "load_framelike_data",
        "line_number": 157
    }
},
```
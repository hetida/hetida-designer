# Structuring Exceptions

In order to further progress errors in other instances, the `ComponentException` is defined in the hetida designer runtime, which can be enriched with an optional error code and optional extra information besides the error message itself.
The error code can be either an integer or a string.
The extra information must be a dictionary.
The values of both of these attributes will then be accessible in the response.
It is the responsibility of component code authors to use the error code in a way that structures the exceptions.

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

In such a case where the exception is raised within the component code, the `file` attribute of the `location` is just `component code`, in all other cases it is the path to the corresponding file.

The `process_stage` attribute can take one of the following values:
* PARSING_WORKFLOW
* LOADING_DATA_FROM_ADAPTERS
* PARSING_LOADED_DATA
* EXECUTING_COMPONENT_CODE
* SENDING_DATA_TO_ADAPTERS 
* ENCODING_RESULTS_TO_JSON

Only exceptions raised in the process stage `EXECUTING_COMPONENT_CODE` cause errors with the `operator_info` attribute, for the other porcess stages this information is not accessible.

Since the most common use case for exceptions is dealing with unexpected input, there is also `ComponentInputValidationException` defined in the hetida designer runtime.
This class inherits from `ComponentException` and has the additional input parameter `input_names`, which consumes a list of strings that is added to the `extra_information` dictionary under the key `input_names`.
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

To develop the component code independently of the hetdesrun library, exceptions must be defined locally in the component code.
This exception must of course enable initialization with a message and an error code.

```python
class SeriesTypeException(Exception):
    def __init__(self, msg, error_code, input_names, **kwargs) -> None:
        self.__is_hetida_designer_exception__ = True
        self.error_code = error_code
        self.extra_information = {"input_names": input_names}
        super().__init__(msg, **kwargs)
```

The most common errors, namely the direct return of the result instead of a dictionary with the component output names as keys 

```python
return series.mean()
```

or a misspelled output name, e.g. due to a changed output name that has not yet been updated in the output dictionary,

```python
return {"mean": series.mean()}
```

result in a `RuntimeExecutionError`:

```json
"error": {
    "type": "RuntimeExecutionError",
    "error_code": null,
    "message": "Component function of component instance \\f7c20ae9-5141-447c-8ae8-086edfc8d231\\76cf9d97-4007-48d8-8ca5-89320df9caab\\ from component \\Wrapper Workflow\\Raise Inherited Exception\\ did not return an output dict!",
    "extra_information": null,
    "process_stage": "EXECUTING_COMPONENT_CODE",
    "operator_info": {...},
    "location": {
        "file": "/app/hetdesrun/runtime/engine/plain/workflow.py",
        "function_name": "_run_comp_func",
        "line_number": 209
    }
}
```

or `KeyError`:

```json
"error": {
    "type": "KeyError",
    "error_code": null,
    "message": "'result'",
    "extra_information": null,
    "process_stage": "EXECUTING_COMPONENT_CODE",
    "operator_info": {...},
    "location": {
        "file": "/app/hetdesrun/runtime/engine/plain/workflow.py",
        "function_name": "result",
        "line_number": 384
    }
}
```

If the data type of an output and the type of the provided data do not match, it depends on the type of adapter and the expected data type what happens.
With the direct provisioning adapter, the result is just displayed without an exception.
In the case of a general custom adapter, it depends on the implementation of that adapter whether an exception is raised.
In the case of a generic REST adapter, an exception is raised in the generic rest adapter part of the runtime if the component output data type is `SERIES`, `DATAFRAME`, or `MULTITSFRAME`:

```json
"error": {
    "type": "AdapterOutputDataError",
    "error_code": null,
    "message": "Did not receive Pandas Series as expected from workflow output. Got <class 'numpy.float64'> instead.",
    "extra_information": null,
    "process_stage": "SENDING_DATA_TO_ADAPTERS",
    "operator_info": null,
    "location": {
        "file": "/app/hetdesrun/adapters/generic_rest/send_ts_data.py",
        "function_name": "ts_to_list_of_dicts",
        "line_number": 42
    }
},
```

All other data types can only be assigned to metadata sinks which are handled differently, i.e. the data is sent to the adapter, which then raises an exception:

```json
"error": {
    "type": "AdapterConnectionError",
    "error_code": null,
    "message": "Posting metadata to generic rest adapter endpoint http://hetida-designer-demo-adapter-python:8092/thingNodes/root.plantA/metadata/Plant%20Age%20in%20Years failed. Status code: 500. Text: Internal Server Error",
    "extra_information": null,
    "process_stage": "SENDING_DATA_TO_ADAPTERS",
    "operator_info": null,
    "location": {
        "file": "/app/hetdesrun/adapters/generic_rest/send_metadata.py",
        "function_name": "send_single_metadatum_to_adapter",
        "line_number": 82
    }
},
```

An error in the input wiring such as an incorrect data type (`dataframe` instead of `timeseries(float)`) will result in similar errors in the `LOADING_DATA_FROM_ADAPTERS` process stage.

```json
"error": {
    "type": "AdapterConnectionError",
    "error_code": null,
    "message": "Requesting framelike data from generic rest adapter endpoint http://hetida-designer-demo-adapter-python:8092/dataframe failed. Status code: 404. Text: {\"detail\":\"No dataframe data available with provided id 'root.plantA.picklingUnit.influx.temp'.\"}",
    "extra_information": null,
    "process_stage": "LOADING_DATA_FROM_ADAPTERS",
    "operator_info": null,
    "location": {
        "file": "/app/hetdesrun/adapters/generic_rest/load_framelike.py",
        "function_name": "load_framelike_data",
        "line_number": 157
    }
},
```
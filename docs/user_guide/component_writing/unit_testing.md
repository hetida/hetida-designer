# Unit Testing

For components, unit tests can be written directly in their code.

## Writing unit tests

Unit tests should be entered directly in your component code, as functions prefixed with `test_`.

For example entering the following function at the bottom of a component which contains a `TEST_WIRING_FROM_PY_FILE_IMPORT` will create a test that runs the component's main function with those input wirings which are `direct_provisioning` data.

```py
from hdutils import parse_value  # noqa: E402


def test_run_with_test_wiring():
    result = main(
        **{
            inp_wiring["workflow_input_name"]: parse_value(
                inp_wiring["filters"]["value"],
                COMPONENT_INFO["inputs"][inp_wiring["workflow_input_name"]][
                    "data_type"
                ],
                nullable=True,
            )
            for inp_wiring in TEST_WIRING_FROM_PY_FILE_IMPORT["input_wirings"]
            if inp_wiring.get("adapter_id", "direct_provisioning")  == "direct_provisioning"
        }
    )

    assert isinstance(result, dict)
    ...
```

## Writing doctests
You can enter doctests as [usual](https://docs.python.org/3/library/doctest.html) in your functions docstring. For the component's main function the docstring must be entered below the comment marking the end of the auto-generated function header:
```py
...
def main(...)
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****

    """Are doctests working?
    >>> 2 + 3
    5
    """
```

## Running Unit Tests

In the hetida designer UI component unit tests can be run via the unit testing button:

<figure markdown="span">
![](../../assets/unit-testing-button.png){ width=30 }
</figure>


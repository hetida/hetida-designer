from hetdesrun.component.load import import_comp
module_exposing_func = import_comp("60ae0402-44cb-4f01-9b16-f1053e8f116c")
doubling_func = module_exposing_func.my_exposed_func

# %%
# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "inp": {"data_type": "INT"},
    },
    "outputs": {
        "outp": {"data_type": "INT"},
    },
    "name": "Import a function from other component with tests",
    "category": "Draft",
    "description": "Imports a function from another component and has unit tests",
    "version_tag": "0.1.0",
    "id": "0fa4c2a8-05d6-4a92-a5b7-7cf6cbdcc478",
    "revision_group_id": "9c8d95de-0e02-4dbd-8fd2-1b3b7e3f52e5",
    "state": "DRAFT",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, inp):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****

    # write your function code here.
    return {"outp": doubling_func(inp) + 3}


def test_imported_doubling_func():
    assert doubling_func(21) == 42


def test_main():
    assert main(inp=2)["outp"] == 7

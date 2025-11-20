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
    "name": "Import a function from other component",
    "category": "Draft",
    "description": "Imports a function from another component",
    "version_tag": "0.1.0",
    "id": "fff908dd-6670-42f2-afd9-c10184334976",
    "revision_group_id": "c0b6ac50-fd56-4e34-9404-5ab62db4b812",
    "state": "DRAFT",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, inp):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****

    # write your function code here.
    return {"outp": doubling_func(inp) + 3}


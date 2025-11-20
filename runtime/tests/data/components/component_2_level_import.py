from hetdesrun.component.load import import_comp
module_exposing_func = import_comp("fff908dd-6670-42f2-afd9-c10184334976")
doubling_func = module_exposing_func.doubling_func


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
    "name": "Component importing func over 2 levels",
    "category": "Draft",
    "description": "Import a func from another component that itself imports it",
    "version_tag": "0.1.0",
    "id": "b7a72a3d-7aad-41f9-b732-9ff4198efb0d",
    "revision_group_id": "5b73f7b6-a4b0-43c1-bd36-83b04cbd345c",
    "state": "DRAFT",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, inp):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****

    # write your function code here.
    return {"outp": doubling_func(inp) + 5}
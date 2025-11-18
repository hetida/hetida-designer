def my_exposed_func(a: int):
    return a * 2

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
    "name": "Component exposing functions",
    "category": "Draft",
    "description": "Exposes some functions for importing from other components",
    "version_tag": "0.1.0",
    "id": "60ae0402-44cb-4f01-9b16-f1053e8f116c",
    "revision_group_id": "ce650a88-a9e7-49ad-9232-335a921ecbd3",
    "state": "DRAFT",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, inp):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****

    # write your function code here.
    return {"outp": my_exposed_func(inp)}


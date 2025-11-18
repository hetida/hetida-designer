from hetdesrun.component.load import import_comp
myself_module = import_comp("ed0a8c97-38e0-41fd-80d8-42c3ab0eb226")
func_from_self = module_exposing_func.func

def func(a):
    return a * 17


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
    "name": "Component self import",
    "category": "Draft",
    "description": "imports itself",
    "version_tag": "0.1.0",
    "id": "ed0a8c97-38e0-41fd-80d8-42c3ab0eb226",
    "revision_group_id": "bf10c313-6e11-4687-ac5b-d6c7dcf682ca",
    "state": "DRAFT",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, inp):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****

    # write your function code here.
    return {"outp": func_from_self(inp)}
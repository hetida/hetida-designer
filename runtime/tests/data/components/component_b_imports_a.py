from hetdesrun.component.load import import_comp
myself_module = import_comp("fc3b45cd-a310-4b1b-90bb-65ce5f6370c3")

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
    "name": "Component B imports A",
    "category": "Draft",
    "description": "b imports a",
    "version_tag": "0.1.0",
    "id": "abaf222d-5f39-4ed5-843b-a68f0f734f71",
    "revision_group_id": "b806ab46-195d-48d2-bd7c-c1e1716b75b8",
    "state": "DRAFT",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, inp):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****

    # write your function code here.
    return {"outp": inp}
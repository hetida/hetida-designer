from hetdesrun.component.load import import_comp
myself_module = import_comp("abaf222d-5f39-4ed5-843b-a68f0f734f71")

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
    "name": "Component A imports B",
    "category": "Draft",
    "description": "a imports b",
    "version_tag": "0.1.0",
    "id": "fc3b45cd-a310-4b1b-90bb-65ce5f6370c3",
    "revision_group_id": "1450fa0e-8583-4dbf-94a3-6dbd0870f0b0",
    "state": "DRAFT",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, inp):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****

    # write your function code here.
    return {"outp": inp}
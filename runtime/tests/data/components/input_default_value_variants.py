# add your own imports here, e.g.
# import pandas as pd
# import numpy as np

# See
#   https://github.com/hetida/hetida-designer/tree/release/docs/component_tips.md
# for component writing features and tips (logging, debugging, importing other components)


# %%
# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "inp_bool_default_actual_null": {"data_type": "BOOLEAN", "default_value": None},
        "inp_bool_default_null_string": {"data_type": "BOOLEAN", "default_value": None},
        "inp_bool_required": {"data_type": "BOOLEAN"},
        "inp_bool_default_true": {"data_type": "BOOLEAN", "default_value": True},
        "inp_bool_default_false": {"data_type": "BOOLEAN", "default_value": False},
    },
    "outputs": {
        "result": {"data_type": "ANY"},
    },
    "name": "Input with default value variants",
    "category": "Test",
    "description": "New created component",
    "version_tag": "0.1.1",
    "id": "198fbdd5-dc02-4640-8032-2354bc6cc6b0",
    "revision_group_id": "bf06402b-3265-450f-a595-e8e82b58fa64",
    "state": "RELEASED",
    "released_timestamp": "2025-12-10T20:36:50.151919+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(
    *,
    inp_bool_required,
    inp_bool_default_actual_null=None,
    inp_bool_default_null_string=None,
    inp_bool_default_true=True,
    inp_bool_default_false=False,
):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****

    # write your function code here.
    return {
        "result": {
            "inp_bool_default_actual_null": inp_bool_default_actual_null,
            "inp_bool_default_null_string": inp_bool_default_null_string,
            "inp_bool_required": inp_bool_required,
            "inp_bool_default_true": inp_bool_default_true,
            "inp_bool_default_false": inp_bool_default_false
        }
    }


# %%

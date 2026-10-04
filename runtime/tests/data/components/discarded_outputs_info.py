from hdutils import plot_output_needed
from hetdesrun.runtime.context import output_is_discarded

# %%
# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {},
    "outputs": {
        "info": {"data_type": "ANY"},
        "data": {"data_type": "INT"},
        "plot": {"data_type": "PLOTLYJSON"},
    },
    "name": "Discarded outputs info",
    "category": "Draft",
    "description": "Reports which of its outputs are discarded",
    "version_tag": "0.1.0",
    "id": "befc012c-9495-45da-aa0f-463cf87a6c95",
    "revision_group_id": "4221bca4-e8a0-4542-8df4-8842b964e34c",
    "state": "DRAFT",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main():
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****

    # write your function code here.
    return {
        "info": {
            "info_discarded": output_is_discarded("info"),
            "data_discarded": output_is_discarded("data"),
            "plot_discarded": output_is_discarded("plot"),
            "plot_needed": plot_output_needed("plot"),
        },
        "data": 42,
        "plot": {},
    }


TEST_WIRING_FROM_PY_FILE_IMPORT = {}
RELEASE_WIRING = None

# %%

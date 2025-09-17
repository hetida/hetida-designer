from hdhelpers import get_plot_target_settings

# %%
# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {},
    "outputs": {
        "context_info": {"data_type": "ANY"},
    },
    "name": "Test context",
    "category": "Draft",
    "description": "New created component",
    "version_tag": "0.1.0",
    "id": "b1a81204-eef0-4830-9303-8452613cb99c",
    "revision_group_id": "3fa814ae-fe0c-42d0-9b50-1a3df45e5e72",
    "state": "DRAFT",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main():
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****

    # write your function code here.
    return {"context_info": get_plot_target_settings().model_dump()}


TEST_WIRING_FROM_PY_FILE_IMPORT = {}
RELEASE_WIRING = None

# %%

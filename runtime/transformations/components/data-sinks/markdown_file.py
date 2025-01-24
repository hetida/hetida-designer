"""Markdown File

# Markdown file

Save string context (e.g. markdown) in a file
"""

# %%
# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "data": {"data_type": "STRING"},
        "path": {"data_type": "STRING"},
    },
    "outputs": {},
    "name": "Markdown File",
    "category": "DataSinks",
    "description": "Save string in file.",
    "version_tag": "0.1.0",
    "id": "c7fc3132-459c-4ede-8b06-59974b50eb17",
    "revision_group_id": "37d96b49-5d39-4497-b0db-c25ca1490c5b",
    "state": "RELEASED",
    "released_timestamp": "2025-01-15T14:23:00.577460+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, data, path):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****

    # write your function code here.
    with open(path, "w") as f:
        f.write(data)


TEST_WIRING_FROM_PY_FILE_IMPORT = {}
RELEASE_WIRING = {}

# %%

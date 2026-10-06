import logging

logger = logging.getLogger(__name__)

# %%
# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {},
    "outputs": {
        "plot": {"data_type": "PLOTLYJSON"},
    },
    "name": "Logging plot",
    "category": "Draft",
    "description": "Logs when it creates its plot",
    "version_tag": "0.1.0",
    "id": "d126bf3c-afb0-4f54-b854-12d8a28cd052",
    "revision_group_id": "dc4b4667-9a61-4138-9368-d6fe20b454ad",
    "state": "DRAFT",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main():
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****

    # write your function code here.
    logger.info("Creating plot")
    return {"plot": {"data": [], "layout": {}}}


TEST_WIRING_FROM_PY_FILE_IMPORT = {}
RELEASE_WIRING = None

# %%

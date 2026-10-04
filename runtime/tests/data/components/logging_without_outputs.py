import logging

logger = logging.getLogger(__name__)

# %%
# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {},
    "outputs": {},
    "name": "Logging without outputs",
    "category": "Draft",
    "description": "Logs when it is run and has no outputs",
    "version_tag": "0.1.0",
    "id": "4ed731bf-4e6e-4239-81b5-f80bfd8778b6",
    "revision_group_id": "f934072d-4db5-45d0-805b-37e3979e8645",
    "state": "DRAFT",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main():
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****

    # write your function code here.
    logger.info("Running without outputs")
    return {}


TEST_WIRING_FROM_PY_FILE_IMPORT = {}
RELEASE_WIRING = None

# %%

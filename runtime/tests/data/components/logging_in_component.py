from logging import getLogger

from hetdesrun import logger as hetdesrun_runtime_exec_logger
from hetdesrun.runtime import runtime_execution_logger
from hetdesrun.runtime.logging import _get_execution_context

logger = getLogger(__name__)



# %%
# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "new_input_1": {"data_type": "STRING"},
    },
    "outputs": {
        "exec_context": {"data_type": "ANY"},
        "dunder_name": {"data_type": "STRING"},
        "logger_filters": {"data_type": "ANY"},
        "logger_name": {"data_type": "STRING"},
    },
    "name": "Test logging",
    "category": "Test",
    "description": "New created component",
    "version_tag": "0.1.0",
    "id": "abafbb92-3cdf-45a4-98ad-c72d9cf0b705",
    "revision_group_id": "577616a3-2265-468f-acb7-d7895436a289",
    "state": "DRAFT",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, new_input_1):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****

    # write your function code here.
    logger.info("TEST LOGGING COMPONENT WITH COMPONENT MODULE LOGGER")
    hetdesrun_runtime_exec_logger.info("TEST LOGGING hetdesrun_runtime_exec_logger")
    runtime_execution_logger.info("TEST LOGGING runtime_execution_logger")
    getLogger("hetdesrun").info("TEST LOGGING hetdesrun module logger")
    return {"exec_context": None, "dunder_name": __name__, "logger_filters": logger.filters, "logger_name": logger.name}
import logging

from hetdesrun.runtime.context import (
    get_hierarchy_object_info,
    get_global_time_interval_info,
)
from hdutils import get_plot_target_settings

logger = logging.getLogger(__name__)
import pandas as pd

# %%
# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {},
    "outputs": {
        "context_information": {"data_type": "ANY"},
    },
    "name": "Context Information",
    "category": "Test",
    "description": "Test context information",
    "version_tag": "0.1.0",
    "id": "016f96c5-776e-41f7-9824-1d818c47f2db",
    "revision_group_id": "2cef85bc-7a38-4071-8f55-19a9a8c54bac",
    "state": "RELEASED",
    "released_timestamp": "2025-12-12T08:58:59.325140+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main():
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****

    # write your function code here.
    global_time_interval = get_global_time_interval_info()
    logger.info(f"Global time interval: {str(global_time_interval)}")

    hierarchy_object = get_hierarchy_object_info()
    logger.info(f"Hierarchy Object Info: {str(hierarchy_object)}")

    plot_target_settings = get_plot_target_settings()
    logger.info(f"Plot Target Settings: {str(plot_target_settings)}")

    return {
        "context_information": {
            "hierarchy_object_info": hierarchy_object,
            "global_time_interval": global_time_interval,
            "plot_target_settings": plot_target_settings,
        }
    }


TEST_WIRING_FROM_PY_FILE_IMPORT = {}
RELEASE_WIRING = None
# %%

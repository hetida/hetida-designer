import asyncio
import logging

logger = logging.getLogger(__name__)

# %%
# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "inp": {"data_type": "STRING", "default_value": "Some Test String"},
        "first_wait": {"data_type": "FLOAT"},
        "second_wait": {"data_type": "FLOAT"},
    },
    "outputs": {
        "out": {"data_type": "STRING"},
    },
    "name": "Provide String async Test",
    "category": "Draft",
    "description": "For testing component adapter concurrency",
    "version_tag": "0.1.0",
    "id": "ee2734f9-ccf9-4849-8ee6-d183e9bbb736",
    "revision_group_id": "88180ae2-bbd8-43be-9317-66ddc819d719",
    "state": "RELEASED",
    "released_timestamp": "2026-02-25T13:47:41.681695+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


async def main(*, first_wait, second_wait, inp="Some Test String"):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****

    # write your function code here.
    logger.info(f"First wait for providing: {inp}")
    await asyncio.sleep(first_wait)
    logger.info(f"Inbetween waiting for providing: {inp}")
    await asyncio.sleep(second_wait)
    logger.info(f"After second wait for providing: {inp}")
    return {"out": inp}


# %%
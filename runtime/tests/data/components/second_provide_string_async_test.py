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
    "name": "Second Provide String async Test",
    "category": "Draft",
    "description": "For testing component adapter concurrency",
    "version_tag": "0.1.0 Copy",
    "id": "6291684c-5249-4a99-9080-1ffa55399a01",
    "revision_group_id": "d5885ce0-d162-4f03-bc7a-a923501d241c",
    "state": "RELEASED",
    "released_timestamp": "2026-02-25T13:54:14.526225+00:00",
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
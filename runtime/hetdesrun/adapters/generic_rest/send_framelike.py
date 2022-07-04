"""Sending framelike data

Common utilities for sending data that is frame-like (tabular), i.e. dataframes as well as
timeseries (where the later can be understood as special dataframe/table)
"""
import datetime
import logging
from posixpath import join as posix_urljoin
from typing import List, Literal

import httpx
from httpx import AsyncClient

from hetdesrun.adapters.exceptions import AdapterConnectionError
from hetdesrun.adapters.generic_rest.auth import get_generic_rest_adapter_auth_headers
from hetdesrun.adapters.generic_rest.baseurl import get_generic_rest_adapter_base_url

logger = logging.getLogger(__name__)


async def post_framelike_records(
    list_of_records: List[dict],
    ref_id: str,
    adapter_key: str,
    endpoint: Literal["timeseries", "dataframe"],
    client: AsyncClient,
) -> None:
    """Post a list of dicts (records) to the appropriate endpoint"""
    headers = get_generic_rest_adapter_auth_headers()

    url = posix_urljoin(await get_generic_rest_adapter_base_url(adapter_key), endpoint)

    start_time = datetime.datetime.now(datetime.timezone.utc)
    logger.info(
        "Start sending framelike data at %s to %s for id %s",
        start_time.isoformat(),
        url,
        ref_id,
    )

    try:
        response = await client.post(
            url,
            params=[("id" if endpoint == "dataframe" else "timeseriesId", ref_id)],
            json=list_of_records,
            headers=headers,
            timeout=60,
        )
    except httpx.HTTPError as e:
        msg = f"Http error while posting framelike data to {url} for id {ref_id}: {str(e)}"
        logger.info(msg)
        raise AdapterConnectionError(msg) from e

    if response.status_code not in (200, 201):
        msg = (
            f"Failed posting framelike data to {url} for id {ref_id}."
            f" Status code: {str(response.status_code)}. Response text: {response.text}"
        )
        raise AdapterConnectionError(msg)
    logger.info(
        "Successfully finished posting framelike data to %s for id %s at %s",
        url,
        ref_id,
        datetime.datetime.now(datetime.timezone.utc).isoformat(),
    )

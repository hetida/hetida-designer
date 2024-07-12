"""Sending framelike data

Common utilities for sending data that is frame-like (tabular), i.e. dataframes as well as
timeseries (where the later can be understood as special dataframe/table)
"""

import base64
import datetime
import json
import logging
from posixpath import join as posix_urljoin
from typing import Any, Literal

import httpx
from httpx import AsyncClient

from hetdesrun.adapters.exceptions import AdapterConnectionError
from hetdesrun.adapters.generic_rest.auth import get_generic_rest_adapter_auth_headers
from hetdesrun.adapters.generic_rest.baseurl import get_generic_rest_adapter_base_url
from hetdesrun.webservice.auth_outgoing import ServiceAuthenticationError

logger = logging.getLogger(__name__)


def encode_attributes(df_attrs: Any) -> str:
    df_attrs_json_str = json.dumps(df_attrs)
    logger.debug("df_attrs_json_str=%s", df_attrs_json_str)
    df_attrs_bytes = df_attrs_json_str.encode("utf-8")
    base64_bytes = base64.b64encode(df_attrs_bytes)
    base64_str = base64_bytes.decode("utf-8")
    logger.debug("base64_str=%s", base64_str)
    return base64_str


async def post_framelike_records(
    list_of_records: list[dict],
    attributes: Any | None,
    ref_id: str,
    additional_params: list[tuple[str, str]],
    adapter_key: str,
    endpoint: Literal["timeseries", "dataframe", "multitsframe"],
    client: AsyncClient,
) -> None:
    """Post a list of dicts (records) to the appropriate endpoint"""
    try:
        headers = await get_generic_rest_adapter_auth_headers(external=True)
    except ServiceAuthenticationError as e:
        msg = (
            "Failed to get auth headers for posting framelike data to adapter"
            f"with key {adapter_key}. Error was:\n{str(e)}"
        )
        logger.info(msg)
        raise AdapterConnectionError(msg) from e

    if attributes is not None and len(attributes) != 0:
        logger.debug("Sending Data-Attributes via POST request header")
        headers["Data-Attributes"] = encode_attributes(attributes)

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
            params=[
                ("timeseriesId" if endpoint == "timeseries" else "id", ref_id),
                *additional_params,
            ],
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

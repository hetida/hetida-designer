import asyncio
import logging
import urllib
from posixpath import join as posix_urljoin
from typing import Any, Dict

import httpx

from hetdesrun.adapters.exceptions import AdapterConnectionError
from hetdesrun.adapters.generic_rest.auth import get_generic_rest_adapter_auth_headers
from hetdesrun.adapters.generic_rest.baseurl import get_generic_rest_adapter_base_url
from hetdesrun.adapters.generic_rest.external_types import ExternalType
from hetdesrun.models.adapter_data import RefIdType
from hetdesrun.models.data_selection import FilteredSink
from hetdesrun.webservice.config import get_config

logger = logging.getLogger(__name__)


async def post_json_with_open_client(
    open_client: httpx.AsyncClient, url: str, json_payload: Dict
) -> httpx.Response:
    return await open_client.post(
        url,
        json=json_payload,
    )


async def send_single_metadatum_to_adapter(
    filtered_sink: FilteredSink,
    metadatum_value: Any,
    adapter_key: str,
    client: httpx.AsyncClient,
) -> None:
    if filtered_sink.ref_id_type == RefIdType.SOURCE:
        endpoint = "sources"
    elif filtered_sink.ref_id_type == RefIdType.SINK:
        endpoint = "sinks"
    else:
        endpoint = "thingNodes"

    url = posix_urljoin(
        await get_generic_rest_adapter_base_url(adapter_key),
        endpoint,
        urllib.parse.quote(str(filtered_sink.ref_id)),
        "metadata",
        urllib.parse.quote(str(filtered_sink.ref_key)),
    )

    value_datatype = ExternalType((filtered_sink.type)).value_datatype
    assert value_datatype is not None  # for mypy

    try:
        resp = await post_json_with_open_client(
            open_client=client,
            url=url,
            json_payload=(
                {
                    "key": filtered_sink.ref_key,
                    "value": metadatum_value,
                    "dataType": value_datatype.value,
                }
            ),
        )
    except httpx.HTTPError as e:
        msg = (
            f"Posting metadata to generic rest adapter endpoint {url}"
            f" failed with Exception {str(e)}"
        )

        logger.info(msg)
        raise AdapterConnectionError(
            f"Posting metadata from generic rest adapter endpoint {url} failed."
        ) from e

    if resp.status_code not in (200, 201):
        msg = (
            f"Posting metadata to generic rest adapter endpoint {url} failed."
            f" Status code: {resp.status_code}. Text: {resp.text}"
        )
        logger.info(msg)
        raise AdapterConnectionError(msg)
    logger.debug(
        "Received Response for metadata posting from url %s:\n%s", url, str(resp.text)
    )


async def send_multiple_metadata_to_adapter(
    filtered_sinks: Dict[str, FilteredSink],
    data_to_send: Dict[str, Any],
    adapter_key: str,
) -> None:
    headers = get_generic_rest_adapter_auth_headers()

    async with httpx.AsyncClient(
        headers=headers, verify=get_config().hd_adapters_verify_certs
    ) as client:
        wf_output_names = filtered_sinks.keys()
        await asyncio.gather(
            *(
                send_single_metadatum_to_adapter(
                    filtered_sinks[wf_output_name],
                    data_to_send[wf_output_name],
                    adapter_key=adapter_key,
                    client=client,
                )
                for wf_output_name in wf_output_names
            )
        )

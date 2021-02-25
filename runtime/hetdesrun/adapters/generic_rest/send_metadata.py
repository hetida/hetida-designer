from typing import Dict, Any
import asyncio

import urllib
import logging
from posixpath import join as posix_urljoin

import httpx

from hetdesrun.models.data_selection import FilteredSink

from hetdesrun.models.adapter_data import RefIdType

from hetdesrun.adapters.generic_rest.auth import get_generic_rest_adapter_auth_headers

from hetdesrun.adapters.generic_rest.baseurl import get_generic_rest_adapter_base_url

from hetdesrun.adapters.generic_rest.external_types import (
    ExternalType,
)

from hetdesrun.service.config import runtime_config


from hetdesrun.adapters.exceptions import (
    AdapterConnectionError,
)

logger = logging.getLogger(__name__)


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
        resp = await client.post(
            url,
            json=(
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

    if resp.status_code != 200 and resp.status_code != 201:
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
        headers=headers, verify=runtime_config.hd_adapters_verify_certs
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

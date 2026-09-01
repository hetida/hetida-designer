import asyncio
import logging
import urllib
from posixpath import join as posix_urljoin
from typing import Any
from uuid import UUID

import httpx

from hetdesrun.adapters.exceptions import AdapterConnectionError, AdapterOutputDataError
from hetdesrun.adapters.generic_rest.auth import get_generic_rest_adapter_auth_headers
from hetdesrun.adapters.generic_rest.baseurl import get_generic_rest_adapter_base_url
from hetdesrun.adapters.generic_rest.client import get_generic_rest_adapter_client
from hetdesrun.adapters.generic_rest.external_types import ExternalType
from hetdesrun.models.adapter_data import RefIdType
from hetdesrun.models.data_selection import FilteredSink
from hetdesrun.runtime.logging import job_id_context_filter
from hetdesrun.webservice.auth_outgoing import ServiceAuthenticationError

logger = logging.getLogger(__name__)


async def post_json_with_open_client(
    open_client: httpx.AsyncClient,
    url: str,
    params: list[tuple[str, Any]],
    json_payload: dict,
    headers: dict[str, str],
) -> httpx.Response:
    return await open_client.post(
        url,
        params=params,
        json=json_payload,
        headers=headers,
    )


async def send_single_metadatum_to_adapter(
    filtered_sink: FilteredSink,
    metadatum_value: Any,
    adapter_key: str,
    client: httpx.AsyncClient,
    headers: dict[str, str],
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

    params = list(filtered_sink.filters.items())
    job_id: str | UUID | None = job_id_context_filter.get_value("currently_executed_job_id")

    if job_id is not None:
        params.append(("job_id", str(job_id)))

    value_datatype = ExternalType(filtered_sink.type).value_datatype
    assert value_datatype is not None  # for mypy   # noqa: S101

    try:
        value_datatype.parse_object(metadatum_value)
    except ValueError as error:
        raise AdapterOutputDataError(
            f"Received metadatum value '{metadatum_value}' cannot be parsed "
            f"as the declared data type {value_datatype.name}."
        ) from error

    try:
        resp = await post_json_with_open_client(
            open_client=client,
            url=url,
            params=params,
            json_payload=(
                {
                    "key": filtered_sink.ref_key,
                    "value": metadatum_value,
                    "dataType": value_datatype.value,
                }
            ),
            headers=headers,
        )
    except httpx.HTTPError as e:
        msg = (
            f"Posting metadata to generic rest adapter endpoint {url}"
            f" failed with Exception: {str(e)}"
        )
        logger.info(msg)
        raise AdapterConnectionError(msg) from e

    if resp.status_code not in (200, 201):
        msg = (
            f"Posting metadata to generic rest adapter endpoint {url} failed."
            f" Status code: {resp.status_code}. Text: {resp.text}"
        )
        logger.info(msg)
        raise AdapterConnectionError(msg)
    logger.debug("Received Response for metadata posting from url %s:\n%s", url, str(resp.text))


async def send_multiple_metadata_to_adapter(
    filtered_sinks: dict[str, FilteredSink],
    data_to_send: dict[str, Any],
    adapter_key: str,
) -> None:
    try:
        headers = await get_generic_rest_adapter_auth_headers(external=True)
    except ServiceAuthenticationError as e:
        msg = (
            "Failed to get auth headers for sending multiple metadata to adapter"
            f"with key {adapter_key}. Error was:\n{str(e)}"
        )
        logger.info(msg)
        raise AdapterConnectionError(msg) from e

    client = get_generic_rest_adapter_client(adapter_key)
    wf_output_names = filtered_sinks.keys()
    await asyncio.gather(
        *(
            send_single_metadatum_to_adapter(
                filtered_sinks[wf_output_name],
                data_to_send[wf_output_name],
                adapter_key=adapter_key,
                client=client,
                headers=headers,
            )
            for wf_output_name in wf_output_names
        )
    )

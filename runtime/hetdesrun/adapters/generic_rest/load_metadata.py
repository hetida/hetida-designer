import asyncio
import logging
import urllib
from posixpath import join as posix_urljoin
from typing import Any
from uuid import UUID

import httpx
from pydantic import BaseModel, ValidationError

from hetdesrun.adapters.exceptions import (
    AdapterConnectionError,
    AdapterHandlingException,
)
from hetdesrun.adapters.generic_rest.auth import get_generic_rest_adapter_auth_headers
from hetdesrun.adapters.generic_rest.baseurl import get_generic_rest_adapter_base_url
from hetdesrun.adapters.generic_rest.client import get_generic_rest_adapter_client
from hetdesrun.adapters.generic_rest.external_types import ExternalType, ValueDataType
from hetdesrun.models.adapter_data import RefIdType
from hetdesrun.models.data_selection import FilteredSource
from hetdesrun.runtime.logging import job_id_context_filter
from hetdesrun.webservice.auth_outgoing import ServiceAuthenticationError

logger = logging.getLogger(__name__)


class Metadatum(BaseModel):
    key: str
    value: Any = None
    dataType: ValueDataType | None = None


async def load_single_metadatum_from_adapter(
    filtered_source: FilteredSource,
    adapter_key: str,
    client: httpx.AsyncClient,
    headers: dict[str, str],
) -> Any:
    if filtered_source.ref_id_type == RefIdType.SOURCE:
        endpoint = "sources"
    elif filtered_source.ref_id_type == RefIdType.SINK:
        endpoint = "sinks"
    else:
        endpoint = "thingNodes"

    url = posix_urljoin(
        await get_generic_rest_adapter_base_url(adapter_key),
        endpoint,
        urllib.parse.quote(str(filtered_source.ref_id)),
        "metadata",
        urllib.parse.quote(str(filtered_source.ref_key)),
    )

    params = list(filtered_source.filters.items())
    job_id: str | UUID | None = job_id_context_filter.get_value("currently_executed_job_id")

    if job_id is not None:
        params.append(("job_id", str(job_id)))

    try:
        resp = await client.get(url, params=params, headers=headers)
    except httpx.HTTPError as e:
        msg = (
            f"Requesting metadata data from generic rest adapter endpoint {url}"
            f" failed with Exception: {str(e)}"
        )

        logger.info(msg)
        raise AdapterConnectionError(msg) from e

    if resp.status_code != 200:
        msg = (
            f"Requesting metadata data from generic rest adapter endpoint {url} failed."
            f" Status code: {resp.status_code}. Text: {resp.text}"
        )
        logger.info(msg)
        raise AdapterConnectionError(msg)

    try:
        metadatum = Metadatum.model_validate(resp.json())
    except ValidationError as e:
        msg = (
            f"Validation failure trying to parse received metadata from adapter"
            f"url {url}: {str(resp.json())}\nError is: " + str(e)
        )

        logger.info(msg)
        raise AdapterHandlingException(msg) from e

    logger.debug("Received metadata json from url %s:\n%s", url, str(resp.json()))

    if metadatum.key != str(filtered_source.ref_key):
        msg = (
            f"received metadata has wrong key "
            f"(not the requested one {str(filtered_source.ref_key)})"
            f". Received metdatum is {str(metadatum)}"
        )
        logger.info(msg)
        raise AdapterConnectionError(msg)

    value_datatype = ExternalType(filtered_source.type).value_datatype
    assert value_datatype is not None  # for mypy   # noqa: S101

    if metadatum.dataType is not None and metadatum.dataType != value_datatype:
        msg = (
            f"received metadata has wrong value dataType "
            f"(not the requested one inside {str(filtered_source.type)})"
            f". Received metdatum is {str(metadatum)}"
        )
        logger.info(msg)
        raise AdapterConnectionError(msg)

    try:
        parsed_value = value_datatype.parse_object(metadatum.value)
    except ValidationError as e:
        msg = (
            f"Validation failure trying to parse received metadata from adapter"
            f"url {url}: {str(metadatum)}\nError is: " + str(e)
        )

        logger.info(msg)
        raise AdapterHandlingException(msg) from e
    return parsed_value  # type: ignore


async def load_multiple_metadata(
    data_to_load: dict[str, FilteredSource], adapter_key: str
) -> dict[str, Any]:
    try:
        headers = await get_generic_rest_adapter_auth_headers(external=True)
    except ServiceAuthenticationError as e:
        msg = (
            "Failed to get auth headers for loading multiple metadata from adapter"
            f"with key {adapter_key}. Error was:\n{str(e)}"
        )
        logger.info(msg)
        raise AdapterHandlingException(msg) from e

    client = get_generic_rest_adapter_client(adapter_key)
    loaded_metadata = await asyncio.gather(
        *(
            load_single_metadatum_from_adapter(
                filtered_source,
                adapter_key,
                client,
                headers=headers,
            )
            for filtered_source in data_to_load.values()
        )
    )
    return dict(zip(data_to_load.keys(), loaded_metadata, strict=True))

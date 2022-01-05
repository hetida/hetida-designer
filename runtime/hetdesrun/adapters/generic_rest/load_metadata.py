from typing import Dict, Any, Optional

import asyncio

import urllib
import logging
from posixpath import join as posix_urljoin


import httpx
from pydantic import (  # pylint: disable=no-name-in-module
    BaseModel,
    ValidationError,
)

from hetdesrun.models.data_selection import FilteredSource


from hetdesrun.models.adapter_data import RefIdType

from hetdesrun.adapters.exceptions import (
    AdapterConnectionError,
    AdapterHandlingException,
)

from hetdesrun.adapters.generic_rest.auth import get_generic_rest_adapter_auth_headers

from hetdesrun.adapters.generic_rest.baseurl import get_generic_rest_adapter_base_url

from hetdesrun.adapters.generic_rest.external_types import ExternalType

from hetdesrun.service.config import runtime_config


from hetdesrun.adapters.generic_rest.external_types import ValueDataType

logger = logging.getLogger(__name__)


class Metadatum(BaseModel):
    key: str
    value: Any
    dataType: Optional[ValueDataType] = None


async def load_single_metadatum_from_adapter(
    filtered_source: FilteredSource, adapter_key: str, client: httpx.AsyncClient
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
    try:
        resp = await client.get(url)
    except httpx.HTTPError as e:
        msg = (
            f"Requesting metadata data from generic rest adapter endpoint {url}"
            f" failed with Exception {str(e)}"
        )

        logger.info(msg)
        raise AdapterConnectionError(
            f"Requesting metadata from generic rest adapter endpoint {url} failed."
        ) from e

    if resp.status_code != 200:
        msg = (
            f"Requesting metadata data from generic rest adapter endpoint {url} failed."
            f" Status code: {resp.status_code}. Text: {resp.text}"
        )
        logger.info(msg)
        raise AdapterConnectionError(msg)

    try:
        metadatum = Metadatum.parse_obj(resp.json())
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
    assert value_datatype is not None  # for mypy

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
    data_to_load: Dict[str, FilteredSource], adapter_key: str
) -> Dict[str, Any]:
    headers = get_generic_rest_adapter_auth_headers()
    async with httpx.AsyncClient(
        headers=headers, verify=runtime_config.hd_adapters_verify_certs
    ) as client:
        loaded_metadata = await asyncio.gather(
            *(
                load_single_metadatum_from_adapter(filtered_source, adapter_key, client)
                for filtered_source in data_to_load.values()
            )
        )
    return dict(zip(data_to_load.keys(), loaded_metadata))

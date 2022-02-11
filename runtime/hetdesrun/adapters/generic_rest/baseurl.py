"""Loading and caching of generic rest adapter base urls"""

import threading
from typing import List, Dict

import logging

from posixpath import join as posix_urljoin

import httpx

from pydantic import BaseModel, ValidationError  # pylint: disable=no-name-in-module

from hetdesrun.webservice.config import runtime_config

from hetdesrun.adapters.generic_rest.auth import get_generic_rest_adapter_auth_headers
from hetdesrun.adapters.exceptions import (
    AdapterConnectionError,
    AdapterHandlingException,
)


logger = logging.getLogger(__name__)

generic_rest_adapter_urls_lock = threading.Lock()

# inititalize cache for adapter urls as global singleton
try:
    with generic_rest_adapter_urls_lock:
        generic_rest_adapter_urls  # pylint: disable=pointless-statement
except NameError:
    with generic_rest_adapter_urls_lock:
        generic_rest_adapter_urls: Dict[str, str] = {}


class BackendRegisteredGenericRestAdapter(BaseModel):
    id: str
    name: str
    url: str
    internalUrl: str


class BackendRegisteredGenericRestAdapters(BaseModel):
    __root__: List[BackendRegisteredGenericRestAdapter]


async def load_generic_adapter_base_urls() -> List[BackendRegisteredGenericRestAdapter]:
    """Loads generic REST adapter infos from the corresponding designer backend endpoint"""

    headers = get_generic_rest_adapter_auth_headers()

    url = posix_urljoin(runtime_config.hd_backend_api_url, "adapters/")
    logger.info("Start getting Generic REST Adapter URLS from HD Backend url %s", url)

    async with httpx.AsyncClient(
        verify=runtime_config.hd_backend_verify_certs
    ) as client:
        try:
            resp = await client.get(url, headers=headers)
        except httpx.HTTPError as e:
            msg = f"Failure connecting to hd backend adapters endpoint ({url}): " + str(
                e
            )
            logger.info(msg)
            raise AdapterConnectionError(msg) from e

    if resp.status_code != 200:
        msg = (
            f"HTTP failure trying to receive generic adapter infos from hd backend ({url}):"
            f" Status code {str(resp.status_code)}. Response: {resp.text}"
        )

        logger.info(msg)
        raise AdapterConnectionError(msg)

    try:
        loaded_generic_rest_adapters: List[
            BackendRegisteredGenericRestAdapter
        ] = BackendRegisteredGenericRestAdapters.parse_obj(resp.json()).__root__
    except ValidationError as e:
        msg = "Failure trying to parse received generic adapter infos: " + str(e)

        logger.info(msg)
        raise AdapterHandlingException(msg) from e

    logger.info(
        "Finished getting Generic REST Adapter URLS from HD Backend url %s", url
    )

    return loaded_generic_rest_adapters


async def update_generic_adapter_base_urls_cache() -> None:
    """Update the cached mapping from adapter keys to their base urls"""
    generic_adapter_infos = await load_generic_adapter_base_urls()

    global generic_rest_adapter_urls  # pylint: disable=global-statement,global-variable-not-assigned
    with generic_rest_adapter_urls_lock:
        for generic_adapter_info in generic_adapter_infos:
            generic_rest_adapter_urls[
                generic_adapter_info.id
            ] = generic_adapter_info.internalUrl


async def get_generic_rest_adapter_base_url(
    adapter_key: str, retry: bool = True
) -> str:
    """Load url from cache and update url cache if necessary"""
    try:
        return generic_rest_adapter_urls[adapter_key]
    except KeyError as e:
        if retry:
            logger.info(
                "Try updating cached generic REST adapter urls since key %s was not found",
                adapter_key,
            )
            await update_generic_adapter_base_urls_cache()
            return await get_generic_rest_adapter_base_url(adapter_key, retry=False)
        # no retry:
        msg = (
            f"Could not find / load necessary generic REST adapter url "
            f"from designer backend for adapter key {adapter_key}. "
            "Make sure the adapter with that key is properly registered"
            " in the designer backend."
        )
        logger.info(msg)
        raise AdapterHandlingException(msg) from e

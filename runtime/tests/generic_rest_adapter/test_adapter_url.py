from unittest import mock

import pytest

from hetdesrun.adapters.exceptions import (
    AdapterConnectionError,
    AdapterHandlingException,
)
from hetdesrun.adapters.generic_rest.baseurl import (
    get_generic_rest_adapter_base_url,
    update_generic_adapter_base_urls_cache,
)
from hetdesrun.backend.models.adapter import AdapterFrontendDto


@pytest.mark.asyncio
async def test_base_url_fetching_internally():
    """Test the case when backend and runtime are served from the same service"""
    get_all_adapters_response_mock = [
        AdapterFrontendDto.parse_obj(
            {
                "id": "test_adapter_key",
                "url": "http://hetida.de",
                "internalUrl": "http://hetida.de",
                "name": "test",
            }
        )
    ]

    with mock.patch(
        "hetdesrun.adapters.generic_rest.baseurl.get_all_adapters",
        return_value=get_all_adapters_response_mock,
    ):
        with mock.patch(
            "hetdesrun.webservice.config.runtime_config.is_backend_service",
            True,
        ):
            assert (
                await get_generic_rest_adapter_base_url("test_adapter_key")
                == "http://hetida.de"
            )


@pytest.mark.asyncio
async def test_base_url_fetching():
    response_mock = mock.Mock()
    response_mock.status_code = 200
    response_mock.json = mock.Mock(
        return_value=[
            {
                "id": "test_adapter_key",
                "url": "http://hetida.de",
                "internal_url": "http://hetida.de",
                "name": "test",
            }
        ]
    )
    with mock.patch(
        "hetdesrun.adapters.generic_rest.baseurl.httpx.AsyncClient.get",
        return_value=response_mock,
    ):
        with mock.patch(
            "hetdesrun.webservice.config.runtime_config.is_backend_service",
            False,
        ):
            assert (
                await get_generic_rest_adapter_base_url("test_adapter_key")
                == "http://hetida.de"
            )

    response_mock.status_code = 400
    with mock.patch(
        "hetdesrun.adapters.generic_rest.baseurl.httpx.AsyncClient.get",
        return_value=response_mock,
    ):
        with mock.patch(
            "hetdesrun.webservice.config.runtime_config.is_backend_service",
            False,
        ):
            with pytest.raises(AdapterConnectionError):
                await update_generic_adapter_base_urls_cache()

            with pytest.raises(AdapterHandlingException):
                response_mock.status_code = 200
                # wrong json
                response_mock.json = mock.Mock(
                    return_value=[
                        {
                            "key": "test_adapter_key",
                            "url": "http://hetida.de",
                            "internal_url": "http://hetida.de",
                            "name": "test",
                        }
                    ]
                )
                await update_generic_adapter_base_urls_cache()


@pytest.mark.asyncio
async def test_adapter_key_not_found():
    response_mock = mock.Mock()
    response_mock.status_code = 200
    response_mock.json = mock.Mock(return_value=[])
    with mock.patch(
        "hetdesrun.adapters.generic_rest.baseurl.httpx.AsyncClient.get",
        return_value=response_mock,
    ):
        with pytest.raises(AdapterHandlingException):
            await get_generic_rest_adapter_base_url("non_present_key")

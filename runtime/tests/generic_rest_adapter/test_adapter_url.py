from unittest import mock
import pytest

from hetdesrun.adapters.generic_rest.baseurl import (
    get_generic_rest_adapter_base_url,
    update_generic_adapter_base_urls_cache,
)
from hetdesrun.adapters.exceptions import (
    AdapterConnectionError,
    AdapterHandlingException,
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
                "internalUrl": "http://hetida.de",
                "name": "test",
            }
        ]
    )
    with mock.patch(
        "hetdesrun.adapters.generic_rest.baseurl.httpx.AsyncClient.get",
        return_value=response_mock,
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
                        "internalUrl": "http://hetida.de",
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
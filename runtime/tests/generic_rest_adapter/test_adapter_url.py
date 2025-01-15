import logging
from unittest import mock

import pytest

from hetdesrun.adapters.exceptions import (
    AdapterHandlingException,
)
from hetdesrun.adapters.generic_rest.baseurl import (
    get_generic_rest_adapter_base_url,
    update_generic_adapter_base_urls_cache,
)
from hetdesrun.backend.models.adapter import AdapterFrontendDto
from hetdesrun.webservice.config import get_config


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

    with mock.patch(  # noqa: SIM117
        "hetdesrun.adapters.generic_rest.baseurl.get_all_adapters",
        return_value=get_all_adapters_response_mock,
    ):
        with mock.patch(
            "hetdesrun.webservice.config.runtime_config.is_backend_service",
            True,
        ):
            assert await get_generic_rest_adapter_base_url("test_adapter_key") == "http://hetida.de"


@pytest.mark.asyncio
async def test_base_url_fetching_externally(caplog):
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
    with mock.patch(  # noqa: SIM117
        "hetdesrun.adapters.generic_rest.baseurl.httpx.AsyncClient.get",
        return_value=response_mock,
    ):
        with mock.patch(
            "hetdesrun.webservice.config.runtime_config.is_backend_service",
            False,
        ):
            assert await get_generic_rest_adapter_base_url("test_adapter_key") == "http://hetida.de"

    with mock.patch(  # noqa: SIM117
        "hetdesrun.adapters.generic_rest.baseurl.httpx.AsyncClient.get",
        return_value=response_mock,
    ):
        with (
            mock.patch(
                "hetdesrun.webservice.config.runtime_config.is_backend_service",
                False,
            ),
        ):
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
            with pytest.raises(AdapterHandlingException):
                await update_generic_adapter_base_urls_cache()


@pytest.mark.asyncio
async def test_base_url_fetching_externally_fallback_to_registration_in_runtime(caplog):
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

    with (
        mock.patch(  # noqa: SIM117
            "hetdesrun.adapters.generic_rest.baseurl.httpx.AsyncClient.get",
            return_value=response_mock,
        ),
        mock.patch(
            "hetdesrun.webservice.config.runtime_config.is_backend_service",
            False,
        ),
        mock.patch(
            "hetdesrun.webservice.config.runtime_config.hd_adapters",
            "some_adapter|Some Adaper|http://external|http://internal",
        ),
    ):
        response_mock.status_code = (
            400  # make request explicietly fail so that only fallback is used
        )
        assert not get_config().is_backend_service
        assert get_config().hd_adapters.startswith("some_adapter|")

        with caplog.at_level(logging.WARNING):
            await update_generic_adapter_base_urls_cache(clear=True)

        assert "Could not obtain adapter internalUrls from backend in runtime" in caplog.text
        # got info from registration instead:
        assert await get_generic_rest_adapter_base_url("some_adapter") == "http://internal"

        # did not get info from request to backend since it failed:
        with pytest.raises(AdapterHandlingException):
            await get_generic_rest_adapter_base_url("test_adapter_key")


@pytest.mark.asyncio
async def test_adapter_key_not_found():
    response_mock = mock.Mock()
    response_mock.status_code = 200
    response_mock.json = mock.Mock(return_value=[])
    with mock.patch(  # noqa: SIM117
        "hetdesrun.adapters.generic_rest.baseurl.httpx.AsyncClient.get",
        return_value=response_mock,
    ):
        with pytest.raises(AdapterHandlingException):
            await get_generic_rest_adapter_base_url("non_present_key")

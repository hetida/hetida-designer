from unittest import mock

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from hetdesrun.webservice.application import init_app


@pytest.fixture(scope="session")
def app_without_auth() -> FastAPI:
    with mock.patch("hetdesrun.webservice.config.runtime_config.auth", False):
        return init_app()


@pytest.fixture
def async_test_client_for_external_sources_tests(
    app_without_auth: FastAPI,
) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app_without_auth), base_url="http://test")


@pytest_asyncio.fixture
async def open_async_test_client_for_external_sources_tests(
    async_test_client_for_external_sources_tests,
):
    async with async_test_client_for_external_sources_tests as client:
        yield client

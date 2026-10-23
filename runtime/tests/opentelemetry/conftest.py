from collections.abc import Generator
from unittest import mock

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from hetdesrun.webservice.application import init_app


@pytest.fixture(scope="function")  # noqa: PT003
def activate_logfire() -> Generator:
    with mock.patch(
        "hetdesrun.webservice.config.runtime_config.otel_via_logfire_active", new=True
    ) as _fixture:
        yield _fixture


@pytest.fixture(scope="function")  # noqa: PT003
def deactivate_auth() -> Generator:
    with mock.patch("hetdesrun.webservice.config.runtime_config.auth", new=False) as _fixture:
        yield _fixture


@pytest.fixture(scope="function")  # noqa: PT003
def app_without_auth_with_logfire(
    deactivate_auth: Generator, activate_logfire: Generator
) -> FastAPI:
    return init_app()


@pytest_asyncio.fixture(scope="function")
async def async_test_client_with_logfire(app_without_auth_with_logfire: FastAPI) -> AsyncClient:
    async with LifespanManager(app_without_auth_with_logfire) as manager:
        return AsyncClient(transport=ASGITransport(app=manager.app), base_url="http://test")

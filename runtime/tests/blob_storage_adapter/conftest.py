from collections.abc import Generator
from unittest import mock

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from hetdesrun.webservice.application import init_app


@pytest.fixture(scope="session")
def mock_adapter_hierarchy_location_in_config() -> Generator:
    with mock.patch(
        "hetdesrun.adapters.blob_storage.config.get_blob_adapter_config",
        adapter_hierarchy_location="tests/data/blob_storage/blob_storage_adapter_hierarchy.json",
    ) as _fixture:
        yield _fixture


@pytest.fixture(scope="session")
def app_without_auth_with_blob_storage_adapter(
    mock_adapter_hierarchy_location_in_config,
) -> FastAPI:
    with mock.patch("hetdesrun.webservice.config.runtime_config.auth", False):
        return init_app()


@pytest.fixture
def async_test_client_with_blob_storage_adapter(
    app_without_auth_with_blob_storage_adapter: FastAPI,
) -> AsyncClient:
    return AsyncClient(
        app=app_without_auth_with_blob_storage_adapter, base_url="http://test"
    )

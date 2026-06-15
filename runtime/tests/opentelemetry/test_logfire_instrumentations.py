import os
from collections.abc import Generator
from unittest import mock

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from logfire.testing import CaptureLogfire

from hetdesrun.trafoutils.trafo_collection import TrafoCollection
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


@pytest.mark.asyncio
async def test_logfire_activation(
    mocked_clean_test_db_session,
    async_test_client,
    async_test_client_with_logfire,
    capfire: CaptureLogfire,
):

    with TrafoCollection(save_to_db=True) as tc:
        pt_string = tc.add_from_json_file(
            os.path.join(
                "transformations",
                "components",
                "connectors",
                "pass-through-string_100_2b1b474f-ddf5-1f4d-fec4-17ef9122112b.json",
            )
        )

    # first without logfire activated via our config option.
    # Note that logfire.testing will actually
    # call logfire.configure against its test exporters, so there will be spans!
    # but there won't be spans from the extra instrumentations we configure
    # if logfire is active, so we can measure a difference.

    exporter = capfire.exporter
    exporter.clear()

    async with async_test_client as client:
        resp = await client.post(
            "/api/transformations/execute",
            json={
                "id": str(pt_string.id),
                "wiring": {
                    "input_wirings": [
                        {
                            "adapter_id": "direct_provisioning",
                            "workflow_input_name": "input",
                            "filters": {"value": "TEST"},
                        }
                    ],
                },
            },
        )
    assert resp.status_code == 200
    num_spans_without = len(exporter.exported_spans_as_dict())

    # now with logfire, using the ordinary async_client

    exporter = capfire.exporter
    exporter.clear()

    async with async_test_client_with_logfire as client:
        resp = await client.post(
            "/api/transformations/execute",
            json={
                "id": str(pt_string.id),
                "wiring": {
                    "input_wirings": [
                        {
                            "adapter_id": "direct_provisioning",
                            "workflow_input_name": "input",
                            "filters": {"value": "TEST"},
                        }
                    ],
                },
            },
        )
    assert resp.status_code == 200

    assert len(exporter.exported_spans_as_dict()) > num_spans_without
    assert len(exporter.exported_spans_as_dict()) > 5

import json
from unittest import mock

import pytest
from httpx import ASGITransport, AsyncClient

from hetdesrun.persistence.dbservice.revision import (
    store_single_transformation_revision,
)
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.webservice.application import init_app


@pytest.fixture()
def _db_with_multits_viz_component(mocked_clean_test_db_session):
    with open(
        "transformations/components/visualization/multitsframe-plot-with-multiple-y-axes_100_28120522-a6a5-418f-a658-ab19d5beefe2.json"
    ) as f:
        trafo_data = json.load(f)
    store_single_transformation_revision(TransformationRevision(**trafo_data))


@pytest.fixture()
def activate_auth():
    with mock.patch(
        "hetdesrun.webservice.config.runtime_config.auth", True
    ) as _fixture:
        yield _fixture


@pytest.fixture()
def app_with_auth(activate_auth):
    return init_app()


@pytest.fixture
def async_test_client_with_auth(app_with_auth):
    return AsyncClient(
        transport=ASGITransport(app=app_with_auth), base_url="http://test"
    )


@pytest.mark.asyncio
async def test_unauthorized_dashboard_endpoint(
    _db_with_multits_viz_component,  # noqa: PT019
    async_test_client,
):
    async with async_test_client as client:
        response = await client.get(
            "/api/transformations/28120522-a6a5-418f-a658-ab19d5beefe2/dashboard"
        )

        assert response.status_code == 200
        assert "<html" in response.text
        assert (
            "gridstack" in response.text
        )  # actually a dashboard and not the login stub


@pytest.mark.asyncio
async def test_unauthorized_dashboard_positioning(
    _db_with_multits_viz_component,  # noqa: PT019
    async_test_client,
):
    async with async_test_client as client:
        response = await client.put(
            "/api/transformations/28120522-a6a5-418f-a658-ab19d5beefe2/dashboard/positioning",
            json=[{"x": 2, "y": 2, "w": 8, "h": 5, "id": "plot"}],
        )
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_authorized_dashboard_endpoint(
    _db_with_multits_viz_component,  # noqa: PT019
    async_test_client_with_auth,
):
    async with async_test_client_with_auth as client:
        response = await client.get(
            "/api/transformations/28120522-a6a5-418f-a658-ab19d5beefe2/dashboard"
        )
        assert response.status_code == 200
        assert "<html" in response.text
        assert (
            "gridstack" not in response.text
        )  # actually a dashboard and not the login stub

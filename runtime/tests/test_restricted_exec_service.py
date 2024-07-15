import json
from unittest import mock
from uuid import UUID

import pytest
from httpx import ASGITransport, AsyncClient

from hetdesrun.backend.execution import ExecByIdInput
from hetdesrun.persistence.dbservice.revision import (
    store_single_transformation_revision,
)
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.webservice.application import init_app


@pytest.fixture()
def restricted_webservice_mode_pass_through_string_component():
    with mock.patch(
        "hetdesrun.webservice.config.runtime_config.restrict_to_trafo_exec_service",
        {UUID("2b1b474f-ddf5-1f4d-fec4-17ef9122112b")},
    ) as _fixture:
        yield _fixture


@pytest.fixture()
def single_allowed_app(deactivate_auth, restricted_webservice_mode_pass_through_string_component):
    return init_app()


@pytest.fixture()
def single_allowed_client(single_allowed_app):
    return AsyncClient(transport=ASGITransport(app=single_allowed_app), base_url="http://test")


@pytest.fixture()
def _db_with_string_pass_through_component(mocked_clean_test_db_session):
    with open(
        "transformations/components/connectors/pass-through-string_100_2b1b474f-ddf5-1f4d-fec4-17ef9122112b.json"
    ) as f:
        trafo_data = json.load(f)
    store_single_transformation_revision(TransformationRevision(**trafo_data))


@pytest.mark.asyncio
async def test_restricted_single_allowed(
    single_allowed_client,
    _db_with_string_pass_through_component,  # noqa: PT019
):
    exec_by_id_input = ExecByIdInput(
        id="2b1b474f-ddf5-1f4d-fec4-17ef9122112b",
        wiring={
            "input_wirings": [
                {
                    "adapter_id": "direct_provisioning",
                    "filters": {"value": "Test exec"},
                    "use_default_value": False,
                    "workflow_input_name": "input",
                }
            ],
            "output_wirings": [],
        },
        run_pure_plot_operators=False,
    )

    async with single_allowed_client as client:
        # correct id works
        response = await client.post(
            "/api/transformations/execute", json=json.loads(exec_by_id_input.json())
        )

        assert response.status_code == 200

        result = response.json()
        assert result["output_results_by_output_name"]["output"] == "Test exec"

        # wrong id implies 403 (forbidden)
        exec_by_id_input.id = "aaaaaaaa-aaaa-bbbb-cccc-111111111111"

        response = await client.post(
            "/api/transformations/execute", json=json.loads(exec_by_id_input.json())
        )

        assert response.status_code == 403

        # backend info endpoint still works
        response = await client.get("/api/info")

        assert response.status_code == 200

        # other backend endpoints not available
        response = await client.get("/api/transformations")

        assert response.status_code == 404

        # other runtime endpoints not available
        response = await client.post("/engine/runtime")

        assert response.status_code == 404

import json
import os

import pytest

from hetdesrun.models.execution import ExecByIdInput
from hetdesrun.persistence.dbservice.revision import (
    store_single_transformation_revision,
)
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.trafoutils.io.load import load_json


@pytest.fixture
def workflow_upgrade_operators(_all_pass_through_components):
    path_to_json_file = os.path.join(
        "tests",
        "data",
        "components",
        "name-series_100.json",
    )
    tr_json = load_json(path_to_json_file)
    store_single_transformation_revision(TransformationRevision(**tr_json))

    path_to_json_file = os.path.join(
        "tests",
        "data",
        "components",
        "name-series_101.json",
    )
    tr_json = load_json(path_to_json_file)
    store_single_transformation_revision(TransformationRevision(**tr_json))

    path_to_json_file = os.path.join(
        "tests",
        "data",
        "workflows",
        "test_operator_upgrading.json",
    )
    tr_json = load_json(path_to_json_file)

    workflow_trafo = TransformationRevision(**tr_json)
    store_single_transformation_revision(workflow_trafo)

    return workflow_trafo


@pytest.mark.asyncio
async def test_upgrade_workflow_operator_runs(
    workflow_upgrade_operators, async_test_client, caplog
):
    # Check workflow is executable with test wiring.

    exec_input = ExecByIdInput(
        id=workflow_upgrade_operators.id,
        wiring=workflow_upgrade_operators.test_wiring,
    )

    async with async_test_client as ac:
        resp = await ac.post(
            "/api/transformations/execute", json=json.loads(exec_input.model_dump_json())
        )

        assert resp.status_code == 200

        resp_json = resp.json()
        assert resp_json["error"] is None
        assert isinstance(resp_json["output_results_by_output_name"]["s_out"], dict)
        assert (
            resp_json["output_results_by_output_name"]["s_out"]["__data__"]["name"] == "test_name"
        )

        # Upgrade operator explicitely to 1.0.1 via web endpoint.

        resp = await ac.put(
            f"/api/transformations/{str(workflow_upgrade_operators.id)}/upgrade_operators/9706f684-77d0-4e24-8bba-ae960a3e9f2e/?new_operator_transformation_revision_id=530e54d4-8d1d-477c-a439-c746c37092f8",
            json=json.loads(workflow_upgrade_operators.model_dump_json()),
        )

        assert resp.status_code == 201

        TransformationRevision(**(resp.json()))  # validates correctly

        # Note: validations of WorkflowContent log with warning level when they
        # need to fix the workflow. We want to make sure that
        # upgrading operators produces a workflow which does not need any fixing!

        # The advantage is that we can test against this validation-fixing, i.e. we
        # know that we do the right thing if no warnings occur.

        assert "For the io interface input" not in caplog.text
        assert "is in the worklow content but not in the io interface" not in caplog.text
        assert "Found no workflow content" not in caplog.text
        assert "there is not workflow content" not in caplog.text

        for record in caplog.records:
            assert record.levelname != "WARNING"
            assert record.levelname != "WARN"

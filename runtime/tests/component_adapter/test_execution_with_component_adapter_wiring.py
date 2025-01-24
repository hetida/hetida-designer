import json
from unittest import mock
from uuid import UUID

import pytest

from hetdesrun.backend.execution import (
    TrafoExecutionComponentAdapterComponentsNotFound,
    execute_transformation_revision,
)
from hetdesrun.models.execution import ExecByIdInput


@pytest.mark.asyncio
@pytest.mark.usefixtures(
    "_components_for_component_adapter_tests", "_pass_through_multits_component_in_db"
)
async def test_component_source_wiring_executes_correctly():
    """Execute a trafo wired with a component adapter source"""

    exec_input = ExecByIdInput(
        id=UUID("78ee6b00-9239-4214-b9bf-a093647f33f5"),  # pass through multits
        wiring={
            "input_wirings": [
                {
                    "workflow_input_name": "input",
                    "adapter_id": "component-adapter",
                    "ref_id": "f2a39f6b-3336-44f2-8c4f-2fd0a4651dd0",
                    "filters": {
                        "timestampFrom": "2025-01-14-12:00:00+00:00",
                        "timestampTo": "2025-01-15-12:00:00+00:00",
                        "frequency": "3h",
                        "metrics": "a,b",
                        "random_seed": 42,
                        "metrics_parameters": r"{}",
                    },
                }
            ]
        },
    )

    with pytest.raises(
        TrafoExecutionComponentAdapterComponentsNotFound
    ):  # validation fails since this is a DRAFT component
        exec_result = await execute_transformation_revision(exec_input)

    # Now allow DRAFT components:
    with mock.patch(
        "hetdesrun.adapters.component_adapter.config.component_adapter_config.allow_draft_components",
        True,
    ):
        exec_result = await execute_transformation_revision(exec_input)
        assert exec_result.error is None
        multitsframe = exec_result.output_results_by_output_name["output"]
        assert len(multitsframe) > 0


@pytest.mark.asyncio
@pytest.mark.usefixtures(
    "_components_for_component_adapter_tests", "_pass_through_multits_component_in_db"
)
async def test_component_source_wiring_executes_via_backend_webservice(async_test_client):
    exec_input = ExecByIdInput(
        id=UUID("78ee6b00-9239-4214-b9bf-a093647f33f5"),  # pass through multits
        wiring={
            "input_wirings": [
                {
                    "workflow_input_name": "input",
                    "adapter_id": "component-adapter",
                    "ref_id": "f2a39f6b-3336-44f2-8c4f-2fd0a4651dd0",
                    "filters": {
                        "timestampFrom": "2025-01-14-12:00:00+00:00",
                        "timestampTo": "2025-01-15-12:00:00+00:00",
                        "frequency": "3h",
                        "metrics": "a,b",
                        "random_seed": 42,
                        "metrics_parameters": r"{}",
                    },
                }
            ]
        },
    )
    with mock.patch(
        "hetdesrun.adapters.component_adapter.config.component_adapter_config.allow_draft_components",
        True,
    ):
        async with async_test_client as ac:
            resp = await ac.post("/api/transformations/execute", json=json.loads(exec_input.json()))

    assert resp.status_code == 200
    assert resp.json()["error"] is None
    assert isinstance(resp.json()["output_results_by_output_name"]["output"], dict)


@pytest.mark.asyncio
@pytest.mark.usefixtures("_markdown_file_component_sink", "_pass_through_str")
async def test_component_sink_wiring_executes_correctly(tmpdir):
    """Execute a trafo wired with a component adapter sink"""

    target_path = tmpdir / "out_file.md"

    exec_input = ExecByIdInput(
        id=UUID("2b1b474f-ddf5-1f4d-fec4-17ef9122112b"),  # pass through multits
        wiring={
            "input_wirings": [
                {
                    "workflow_input_name": "input",
                    "adapter_id": "direct_provisioning",
                    "filters": {"value": "test"},
                }
            ],
            "output_wirings": [
                {
                    "workflow_output_name": "output",
                    "adapter_id": "component-adapter",
                    "ref_id": "c7fc3132-459c-4ede-8b06-59974b50eb17",
                    "filters": {"path": str(target_path)},
                }
            ],
        },
    )

    exec_result = await execute_transformation_revision(exec_input)
    assert exec_result.error is None
    assert len(exec_result.output_results_by_output_name) == 0

    with open(target_path) as f:
        content = f.read()

    assert content == "test"


@pytest.mark.asyncio
@pytest.mark.usefixtures("_markdown_file_component_sink", "_pass_through_str")
async def test_component_sink_wiring_executes_via_backend_webendpoint(async_test_client, tmpdir):
    target_path = tmpdir / "out_file.md"

    exec_input = ExecByIdInput(
        id=UUID("2b1b474f-ddf5-1f4d-fec4-17ef9122112b"),  # pass through multits
        wiring={
            "input_wirings": [
                {
                    "workflow_input_name": "input",
                    "adapter_id": "direct_provisioning",
                    "filters": {"value": "test"},
                }
            ],
            "output_wirings": [
                {
                    "workflow_output_name": "output",
                    "adapter_id": "component-adapter",
                    "ref_id": "c7fc3132-459c-4ede-8b06-59974b50eb17",
                    "filters": {"path": str(target_path)},
                }
            ],
        },
    )

    async with async_test_client as ac:
        resp = await ac.post("/api/transformations/execute", json=json.loads(exec_input.json()))

    assert resp.status_code == 200
    assert resp.json()["error"] is None
    assert len(resp.json()["output_results_by_output_name"]) == 0  # no outputs


@pytest.mark.asyncio
@pytest.mark.usefixtures("_plotly_to_html_file_sink_component", "_single_timeseries_plot_component")
async def test_component_sink_wiring_plotly_executes_correctly(tmpdir):
    """Execute a trafo wired with a plotlyjson component adapter sink"""

    target_path = tmpdir / "out_file.html"

    exec_input = ExecByIdInput(
        id=UUID("8fba9b51-a0f1-6c6c-a6d4-e224103b819c"),  # pass through multits
        wiring={
            "input_wirings": [
                {
                    "workflow_input_name": "series",
                    "adapter_id": "direct_provisioning",
                    "filters": {
                        "value": r"""{"2020-01-01T01:15:27.000Z": 42.2,
                                      "2020-01-03T08:20:03.000Z": 18.7,
                                      "2020-01-03T08:20:04.000Z": 25.9}"""
                    },
                }
            ],
            "output_wirings": [
                {
                    "workflow_output_name": "plot",
                    "adapter_id": "component-adapter",
                    "ref_id": "ce9dbeee-9e7d-4b7c-8384-9b280b2dc144",
                    "filters": {"path": str(target_path)},
                }
            ],
        },
        run_pure_plot_operators=True,  # we are running a pure plot component!
    )

    exec_result = await execute_transformation_revision(exec_input)
    assert exec_result.error is None
    assert len(exec_result.output_results_by_output_name) == 0

    with open(target_path) as f:
        content = f.read()

    assert "<html" in content
    assert "2020-01-01T01:15:27+00:00" in content

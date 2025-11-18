import json
import os

import pytest

from hetdesrun.models.execution import ExecByIdInput
from hetdesrun.models.wiring import WorkflowWiring
from hetdesrun.trafoutils.trafo_collection import TrafoCollection


@pytest.mark.asyncio
async def test_running_single_level_and_2_level_component_import(
    mocked_clean_test_db_session, async_test_client
):
    with TrafoCollection(save_to_db=True) as tc:
        comp_with_funcs = tc.add_from_py_file(  # noqa: F841
            os.path.join(
                "tests",
                "data",
                "components",
                "component_with_functions_for_importing.py",
            )
        )
        comp_importing_a_func = tc.add_from_py_file(
            os.path.join(
                "tests",
                "data",
                "components",
                "component_importing_func_from_other.py",
            )
        )
        comp_2_level_import = tc.add_from_py_file(
            os.path.join(
                "tests",
                "data",
                "components",
                "component_2_level_import.py",
            )
        )

    # execute:
    exec_input = ExecByIdInput(
        id=comp_importing_a_func.id,
        job_id="bbbbbbbb-3cdf-45a4-98ad-bbbbbbbbbbbb",
        wiring=WorkflowWiring(
            input_wirings=[
                {
                    "workflow_input_name": "inp",
                    "adapter_id": "direct_provisioning",
                    "filters": {"value": "2"},
                }
            ]
        ),
    )

    async with async_test_client as ac:
        resp = await ac.post(
            "/api/transformations/execute", json=json.loads(exec_input.model_dump_json())
        )
        assert resp.status_code == 200

        resp_json = resp.json()
        assert resp_json["output_results_by_output_name"]["outp"] == 7

        # 2 level nested import execute:
        exec_input = ExecByIdInput(
            id=comp_2_level_import.id,
            job_id="bbbbbbbb-3cdf-45a4-98ad-bbbbbbbbbbbb",
            wiring=WorkflowWiring(
                input_wirings=[
                    {
                        "workflow_input_name": "inp",
                        "adapter_id": "direct_provisioning",
                        "filters": {"value": "2"},
                    }
                ]
            ),
        )

        resp = await ac.post(
            "/api/transformations/execute", json=json.loads(exec_input.model_dump_json())
        )
        assert resp.status_code == 200

        resp_json = resp.json()
        assert resp_json["output_results_by_output_name"]["outp"] == 9


@pytest.mark.asyncio
async def test_detect_component_import_cycle(mocked_clean_test_db_session, async_test_client):
    """Detect component import cycles

    Are detected by the actual import process at runtime.
    """
    with TrafoCollection(save_to_db=True) as tc:
        comp_with_self_import = tc.add_from_py_file(
            os.path.join(
                "tests",
                "data",
                "components",
                "component_self_import.py",
            )
        )
        comp_a_imports_b = tc.add_from_py_file(
            os.path.join(
                "tests",
                "data",
                "components",
                "component_a_imports_b.py",
            )
        )
        comp_b_imports_a = tc.add_from_py_file(  # noqa: F841
            os.path.join(
                "tests",
                "data",
                "components",
                "component_b_imports_a.py",
            )
        )

    async with async_test_client as ac:
        # execute self-importing component:
        exec_input = ExecByIdInput(
            id=comp_with_self_import.id,
            job_id="bbbbbbbb-3cdf-45a4-98ad-bbbbbbbbbbbb",
            wiring=WorkflowWiring(
                input_wirings=[
                    {
                        "workflow_input_name": "inp",
                        "adapter_id": "direct_provisioning",
                        "filters": {"value": "2"},
                    }
                ]
            ),
        )
        resp = await ac.post(
            "/api/transformations/execute", json=json.loads(exec_input.model_dump_json())
        )
        assert resp.status_code == 200

        resp_json = resp.json()
        assert resp_json["error"] is not None
        assert "ComponentImportCycleError" in resp_json["traceback"]

        # execute a_imports_b (cycle because b_imports_a)
        exec_input = ExecByIdInput(
            id=comp_a_imports_b.id,
            job_id="bbbbbbbb-3cdf-45a4-98ad-bbbbbbbbbbbb",
            wiring=WorkflowWiring(
                input_wirings=[
                    {
                        "workflow_input_name": "inp",
                        "adapter_id": "direct_provisioning",
                        "filters": {"value": "2"},
                    }
                ]
            ),
        )
        resp = await ac.post(
            "/api/transformations/execute", json=json.loads(exec_input.model_dump_json())
        )
        assert resp.status_code == 200

        resp_json = resp.json()
        assert resp_json["error"] is not None
        assert "ComponentImportCycleError" in resp_json["traceback"]

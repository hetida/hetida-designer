"""Components used by the component adapter should be able to import other components"""

import json
import os
from unittest import mock

import pytest

from hetdesrun.models.execution import ExecByIdInput
from hetdesrun.models.wiring import WorkflowWiring
from hetdesrun.trafoutils.trafo_collection import TrafoCollection


@pytest.mark.asyncio
async def test_running_component_adapter_with_component_that_imports_other_components(
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
        comp_importing_a_func = tc.add_from_py_file(  # noqa: F841
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
        pass_trough_int = tc.add_from_json_file(
            os.path.join(
                "transformations",
                "components",
                "connectors",
                "pass-through-integer_100_57eea09f-d28e-89af-4e81-2027697a3f0f.json",
            )
        )

    # execute:
    exec_input = ExecByIdInput(
        id=pass_trough_int.id,
        job_id="bbbbbbbb-3cdf-45a4-98ad-bbbbbbbbbbbb",
        wiring=WorkflowWiring(
            input_wirings=[
                {
                    "workflow_input_name": "input",
                    "adapter_id": "component-adapter",
                    "ref_id": str(comp_2_level_import.id),
                    "filters": {"inp": "3"},
                }
            ]
        ),
    )
    with mock.patch(
        "hetdesrun.adapters.component_adapter.config.component_adapter_config.allow_draft_components",
        True,
    ):
        async with async_test_client as ac:
            resp = await ac.post(
                "/api/transformations/execute", json=json.loads(exec_input.model_dump_json())
            )
            assert resp.status_code == 200

            resp_json = resp.json()
            assert resp_json["output_results_by_output_name"]["output"] == 11

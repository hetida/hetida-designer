"""Test that plotly target settings set in Exec inputs reach plot components"""

import json
import os

import pytest

from hdhelpers.context import RuntimeExecutionContext
from hdhelpers.plot_target_settings import PlotTargetSettings
from hetdesrun.models.execution import ExecByIdInput
from hetdesrun.trafoutils.trafo_collection import TrafoCollection


@pytest.mark.asyncio
async def test_plot_target_settings_reach_component(
    mocked_clean_test_db_session, async_test_client
):
    with TrafoCollection(save_to_db=True) as tc:
        plot_settings_comp = tc.add_from_py_file(
            os.path.join(
                "tests",
                "data",
                "components",
                "plot_target_settings.py",
            )
        )

    exec_input = ExecByIdInput(
        id=plot_settings_comp.id,
        wiring=plot_settings_comp.test_wiring,
        runtime_execution_context=RuntimeExecutionContext(
            plot_target_settings=PlotTargetSettings(plot_target_locale="de")
        ),
    )

    async with async_test_client as ac:
        resp = await ac.post(
            "/api/transformations/execute", json=json.loads(exec_input.model_dump_json())
        )
        assert resp.status_code == 200
        resp_json = resp.json()
        assert resp_json["error"] is None

        context_info_output = resp_json["output_results_by_output_name"]["context_info"]

        assert isinstance(context_info_output, dict)
        assert context_info_output["plot_target_timezone"] is None
        assert context_info_output["plot_target_locale"] == "de"

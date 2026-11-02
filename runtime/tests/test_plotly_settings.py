"""Test that plotly target settings set in Exec inputs reach plot components"""

import json
import os

import pandas as pd
import plotly.graph_objects as go
import pytest

from hdutils import PlotTargetSettings, plotly_datetimes, plotly_fig_to_json_dict
from hetdesrun.models.execution import ExecByIdInput
from hetdesrun.runtime.context import RuntimeExecutionContext
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


def test_plotly_fig_to_json_dict_disables_send_to_cloud():
    plotly_json = plotly_fig_to_json_dict(go.Figure(go.Scatter(x=[1, 2], y=[3, 4])))

    assert plotly_json["config"]["showSendToCloud"] is False


def test_plotly_fig_to_json_dict_keeps_auto_ticks_for_overlaying_axes():
    fig = go.Figure(go.Scatter(x=[1, 2], y=[3, 4]))
    fig.update_layout(
        yaxis2={"overlaying": "y"},
        yaxis3={"overlaying": "y", "tickmode": "sync"},
        yaxis4={"overlaying": "y", "tickvals": [1, 2]},
        xaxis2={"overlaying": "x"},
    )

    layout = plotly_fig_to_json_dict(fig)["layout"]

    assert layout["yaxis2"]["tickmode"] == "auto"
    assert layout["xaxis2"]["tickmode"] == "auto"
    # explicitly configured tick placement is kept
    assert layout["yaxis3"]["tickmode"] == "sync"
    assert "tickmode" not in layout["yaxis4"]
    # axes which are not overlaying are left alone
    assert "tickmode" not in layout.get("yaxis", {})


def test_plotly_datetimes_keeps_wall_clock_times():
    index = pd.DatetimeIndex(["2024-10-27T00:30:00Z", "2024-10-27T01:30:00Z"]).tz_convert(
        "Europe/Berlin"
    )

    naive = plotly_datetimes(index)

    assert naive.tz is None
    assert list(naive) == [pd.Timestamp("2024-10-27T02:30"), pd.Timestamp("2024-10-27T02:30")]
    # plotly shows the same wall-clock times as for the timezone-aware index
    tz_aware_x = plotly_fig_to_json_dict(go.Figure(go.Scatter(x=index, y=[1, 2])))["data"][0]["x"]
    naive_x = plotly_fig_to_json_dict(go.Figure(go.Scatter(x=naive, y=[1, 2])))["data"][0]["x"]
    assert [x[:19] for x in tz_aware_x] == [x[:19] for x in naive_x]


def test_plotly_datetimes_leaves_other_values_unchanged():
    naive_index = pd.DatetimeIndex(["2024-01-01T00:00:00"])
    range_index = pd.RangeIndex(3)

    assert plotly_datetimes(naive_index) is naive_index
    assert plotly_datetimes(range_index) is range_index
    assert plotly_datetimes([1, 2]) == [1, 2]

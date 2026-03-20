import os

import pytest

from hetdesrun.trafoutils.trafo_collection import TrafoCollection

payload = {
    "id": "bfa27afc-dea8-b8aa-4b15-94402f0739b6",
    "run_pure_plot_operators": True,
    "wiring": {
        "dashboard_positionings": [],
        "input_wirings": [
            {
                "adapter_id": "direct_provisioning",
                "filters": {
                    "value": '{\n    "2020-01-01T01:15:27.000Z": 42.2,\n    "2020-01-03T08:20:03.000Z": 18.7,\n    "2020-01-03T08:20:04.000Z": 25.9\n}'  # noqa: E501
                },
                "use_default_value": False,
                "workflow_input_name": "input",
            }
        ],
        "output_wirings": [{"adapter_id": "plot", "filters": {}, "workflow_output_name": "output"}],
    },
}


@pytest.mark.asyncio
async def test_plot_wiring_payload(mocked_clean_test_db_session, async_test_client):
    with TrafoCollection(save_to_db=True) as tc:
        _pt_series = tc.add_from_json_file(
            os.path.join(
                "transformations",
                "components",
                "connectors",
                "pass-through-series_100_bfa27afc-dea8-b8aa-4b15-94402f0739b6.json",
            )
        )
    async with async_test_client as client:
        resp = await client.post("/api/transformations/execute", json=payload)

    assert resp.status_code == 200
    resp_json = resp.json()
    assert resp_json["error"] is None

    # output type was appropriately adapted:
    assert resp_json["output_types_by_output_name"]["output"] == "PLOTLYJSON"

    # result is a plotly json dict object
    plot_result = resp_json["output_results_by_output_name"]["output"]
    assert isinstance(plot_result, dict)
    assert "data" in plot_result

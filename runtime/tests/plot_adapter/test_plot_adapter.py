import os
from typing import Any
from uuid import UUID

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


def pt_payload(id: UUID, value_str: str) -> Any:  # noqa: A002
    payload = {
        "id": str(id),
        "run_pure_plot_operators": True,
        "wiring": {
            "dashboard_positionings": [],
            "input_wirings": [
                {
                    "adapter_id": "direct_provisioning",
                    "filters": {"value": value_str},
                    "use_default_value": False,
                    "workflow_input_name": "input",
                }
            ],
            "output_wirings": [
                {"adapter_id": "plot", "filters": {}, "workflow_output_name": "output"}
            ],
        },
    }
    return payload


def assert_resp_has_plot_output(resp):
    assert resp.status_code == 200
    resp_json = resp.json()
    assert resp_json["error"] is None

    # output type was appropriately adapted:
    assert resp_json["output_types_by_output_name"]["output"] == "PLOTLYJSON"

    # result is a plotly json dict object
    plot_result = resp_json["output_results_by_output_name"]["output"]
    assert isinstance(plot_result, dict)
    assert "data" in plot_result


@pytest.mark.asyncio
async def test_plot_wiring_payload(mocked_clean_test_db_session, async_test_client):
    with TrafoCollection(save_to_db=True) as tc:
        pt_series = tc.add_from_json_file(
            os.path.join(
                "transformations",
                "components",
                "connectors",
                "pass-through-series_100_bfa27afc-dea8-b8aa-4b15-94402f0739b6.json",
            )
        )
        pt_dataframe = tc.add_from_json_file(
            os.path.join(
                "transformations",
                "components",
                "connectors",
                "pass-through-dataframe_100_7a1a818f-fa89-6062-1e0e-fc80539bbe0a.json",
            )
        )
        pt_mtfs = tc.add_from_json_file(
            os.path.join(
                "transformations",
                "components",
                "connectors",
                "pass-through-multitsframe_100_78ee6b00-9239-4214-b9bf-a093647f33f5.json",
            )
        )
        pt_string = tc.add_from_json_file(
            os.path.join(
                "transformations",
                "components",
                "connectors",
                "pass-through-string_100_2b1b474f-ddf5-1f4d-fec4-17ef9122112b.json",
            )
        )

        pt_any = tc.add_from_json_file(
            os.path.join(
                "transformations",
                "components",
                "connectors",
                "pass-through_100_1946d5f8-44a8-724c-176f-16f3e49963af.json",
            )
        )

    async with async_test_client as client:
        resp = await client.post(
            "/api/transformations/execute",
            json=pt_payload(
                pt_series.id,
                '{\n    "2020-01-01T01:15:27.000Z": 42.2,\n    "2020-01-03T08:20:03.000Z": 18.7,\n    "2020-01-03T08:20:04.000Z": 25.9\n}',  # noqa: E501
            ),
        )

        assert_resp_has_plot_output(resp)

        resp = await client.post(
            "/api/transformations/execute",
            json=pt_payload(
                pt_string.id,
                "some string",  # noqa: E501
            ),
        )

        assert_resp_has_plot_output(resp)

        resp = await client.post(
            "/api/transformations/execute",
            json=pt_payload(
                pt_dataframe.id,
                '{    "column1": {        "2019-08-01T15:45:36.000Z": 1,        "2019-08-02T11:33:41.000Z": 2    },    "column2": {        "2019-08-01T15:45:36.000Z": 1.3,        "2019-08-02T11:33:41.000Z": 2.8    }}',  # noqa: E501
            ),
        )

        assert_resp_has_plot_output(resp)

        resp = await client.post(
            "/api/transformations/execute",
            json=pt_payload(
                pt_mtfs.id,
                '{    "value": [        1,        1.2,        0.5    ],    "metric": [        "a",        "b",        "c"    ],    "timestamp": [        "2019-08-01T15:45:36.000Z",        "2019-08-01T15:48:36.000Z",        "2019-08-01T15:42:36.000Z"    ]}',  # noqa: E501
            ),
        )

        assert_resp_has_plot_output(resp)

        resp = await client.post(
            "/api/transformations/execute",
            json=pt_payload(
                pt_any.id,
                '{"a": 42}',  # noqa: E501
            ),
        )

        assert_resp_has_plot_output(resp)

import json
import os

import pytest
import pytest_asyncio

from hetdesrun.models.execution import ExecByIdInput
from hetdesrun.models.wiring import WorkflowWiring
from hetdesrun.trafoutils.trafo_collection import TrafoCollection


@pytest_asyncio.fixture
async def open_async_test_client_with_sql_adapter(
    async_test_client_with_sql_adapter_with_timeseries_table,
):
    async with async_test_client_with_sql_adapter_with_timeseries_table as client:
        yield client


@pytest.mark.asyncio
async def test_sql_adapter_in_execution(
    open_async_test_client_with_sql_adapter, mocked_clean_test_db_session
) -> None:
    with TrafoCollection(save_to_db=True) as tc:
        comp_multits_pass_through = tc.add_from_json_file(  # noqa: F841
            os.path.join(
                "transformations",
                "components",
                "connectors",
                "pass-through-multitsframe_100_78ee6b00-9239-4214-b9bf-a093647f33f5.json",
            )
        )

    exec_input = ExecByIdInput(
        id=comp_multits_pass_through.id,
        job_id="bbbbbbbb-3cdf-45a4-98ad-bbbbbbbbbbbb",
        wiring=WorkflowWiring(
            input_wirings=[
                {
                    "ref_id": "read_only_timeseries_sqlite_database/ts_table/ro_ts_table",
                    "ref_id_type": "SOURCE",
                    "workflow_input_name": "input",
                    "adapter_id": "sql-adapter",
                    "filters": {
                        "metrics": "ALL",
                        "timestampFrom": "2023-08-01T11:58:02+00:00",
                        "timestampTo": "2023-08-29T23:58:02+00:00",
                    },
                }
            ]
        ),
    )

    resp = await open_async_test_client_with_sql_adapter.post(
        "/api/transformations/execute", json=json.loads(exec_input.model_dump_json())
    )
    assert resp.status_code == 200
    resp_json = resp.json()
    assert len(resp_json["output_results_by_output_name"]["output"]["__data__"]["value"]) == 4

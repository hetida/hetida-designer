import json
import os

import pytest

from hetdesrun.models.execution import ExecByIdInput
from hetdesrun.models.wiring import WorkflowWiring
from hetdesrun.trafoutils.trafo_collection import TrafoCollection
from hetdesrun.trafoutils.workflow_construction import WorkflowConstructor


@pytest.mark.asyncio
async def test_workflow_construction(async_test_client, mocked_clean_test_db_session):
    with TrafoCollection(save_to_db=True) as tc:
        name_series_component = tc.add_from_json_file(
            os.path.join(
                "tests",
                "data",
                "components",
                "name-series_100.json",
            )
        )
        with WorkflowConstructor(tc, autoarrange=True, name="Test WF") as wf:
            op_1 = wf.op(name_series_component)
            op_2 = wf.op(name_series_component)
            assert op_1.operator.id != op_2.operator.id

            wf.link(op_1.o.output, op_2.i.input)

            wf.output("second_op_output", op_2.o.output)
            wf.input("second_str_inp", op_2.i.name)
            wf.input("first_series_inp", op_1.i.input, optional=True, default_value=[1, 2, 3, 67])
            wf.constant(op_1.i.name, value="FIRST NAME")

    assert wf.result
    print(wf.result.json())

    # okay, check that it actually is runnable:

    exec_input = ExecByIdInput(
        id=wf.result.id,
        wiring=WorkflowWiring(
            input_wirings=[
                {
                    "workflow_input_name": "second_str_inp",
                    "adapter_id": "direct_provisioning",
                    "filters": {"value": "the real name"},
                }
            ]
        ),
    )

    async with async_test_client as ac:
        resp = await ac.post("/api/transformations/execute", json=json.loads(exec_input.json()))

    assert resp.status_code == 200

    series_output_data_dict = resp.json()["output_results_by_output_name"]["second_op_output"]
    assert series_output_data_dict["__data__"]["name"] == "the real name"

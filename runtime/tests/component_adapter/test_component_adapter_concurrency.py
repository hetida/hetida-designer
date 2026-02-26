import json
import os

import pytest

from hetdesrun.models.execution import ExecByIdInput
from hetdesrun.models.wiring import WorkflowWiring
from hetdesrun.trafoutils.trafo_collection import TrafoCollection
from hetdesrun.trafoutils.workflow_construction import WorkflowConstructor


@pytest.mark.asyncio
async def test_concurrent_component_adapter_loading(
    mocked_clean_test_db_session, async_test_client
):
    """Test concurrently component adapter loading behaves well with respect to execution context

    Since contexvars are provided as shallow copies to asyncio subtasks, the executed
    components may have wrong execution context information if the execution_context_filter
    is not properly resetted / filled. This tests evokes a concurrent execution which
    will lead to errors if this is the case.

    This test also ensures actual concurrency of execution by observing log message ordering.
    """
    with TrafoCollection(save_to_db=True) as tc:
        pt_string = tc.add_from_json_file(
            os.path.join(
                "transformations",
                "components",
                "connectors",
                "pass-through-string_100_2b1b474f-ddf5-1f4d-fec4-17ef9122112b.json",
            )
        )
        first_str_provider = tc.add_from_py_file(
            os.path.join(
                "tests",
                "data",
                "components",
                "first_provide_string_async_test.py",
            )
        )
        second_str_provider = tc.add_from_py_file(
            os.path.join(
                "tests",
                "data",
                "components",
                "second_provide_string_async_test.py",
            )
        )

        with WorkflowConstructor(
            trafo_collector=tc,
            name="Test concurrent component adapter loading",
            version_tag="0.1.0",
            id="2d28ace6-68c8-48ab-bbea-0415ab06714b",
            auto_release=True,
        ) as wf:
            first_pass_through_string_op = wf.op(pt_string, "first_string_pass_through")
            second_pass_through_string_op = wf.op(pt_string, "second_string_pass_through")
            wf.input("in1", first_pass_through_string_op.i["input"])
            wf.input("in2", second_pass_through_string_op.i["input"])
            wf.output("o1", first_pass_through_string_op.o["output"])
            wf.output("o2", second_pass_through_string_op.o["output"])

    async with async_test_client as ac:
        exec_input = ExecByIdInput(
            id=wf.id,
            job_id="1ce33819-6356-4a01-b0e7-28441d8c0f75",
            wiring=WorkflowWiring(
                input_wirings=[
                    {
                        "uri": f"hd://component-adapter/{first_str_provider.id}?inp=in1&first_wait=1.0&second_wait=1.0",
                        "workflow_input_name": "in1",
                    },
                    {
                        "uri": f"hd://component-adapter/{second_str_provider.id}?inp=in2&first_wait=1.2&second_wait=0.2",
                        "workflow_input_name": "in2",
                    },
                ]
            ),
        )
        resp = await ac.post(
            "/api/transformations/execute", json=json.loads(exec_input.model_dump_json())
        )
        assert resp.status_code == 200
        resp_json = resp.json()
        assert resp_json["output_results_by_output_name"]["o1"] == "in1"
        assert resp_json["output_results_by_output_name"]["o2"] == "in2"

        assert len(resp_json["gathered_component_code_logs"]) == 6

        for log_entry in resp_json["gathered_component_code_logs"]:
            if log_entry["message"].endswith("in1"):
                assert str(log_entry["tr_id"]) == str(first_str_provider.id)
            if log_entry["message"].endswith("in2"):
                assert str(log_entry["tr_id"]) == str(second_str_provider.id)

        # actually concurrent
        assert resp_json["gathered_component_code_logs"][2]["message"].endswith("in1")
        assert resp_json["gathered_component_code_logs"][3]["message"].endswith("in2")
        assert resp_json["gathered_component_code_logs"][4]["message"].endswith("in2")
        # yes:
        assert resp_json["gathered_component_code_logs"][5]["message"].endswith("in1")


@pytest.mark.asyncio
async def test_non_concurrent_operator_execution(mocked_clean_test_db_session, async_test_client):
    """Ensure that operator execution is not concurrent

    Even for components with async def main function!

    Operator's actions are typically cpu bound and not io bound. Data provisioning should
    happen via Adapter system and not as part of analytics.

    The test ensures that execution context is correct by observing log message attached
    information from the context.

    This test also ensures non-concurrency of operator execution by observing log message
    ordering.
    """
    with TrafoCollection(save_to_db=True) as tc:
        first_str_provider = tc.add_from_py_file(
            os.path.join(
                "tests",
                "data",
                "components",
                "first_provide_string_async_test.py",
            )
        )
        second_str_provider = tc.add_from_py_file(
            os.path.join(
                "tests",
                "data",
                "components",
                "second_provide_string_async_test.py",
            )
        )

        with WorkflowConstructor(
            trafo_collector=tc,
            name="Test concurrent component operator execution",
            version_tag="0.1.0",
            id="99a0cd7f-2066-4845-ac62-173d5a825dc3",
            auto_release=True,
        ) as wf:
            first_string_provider_op = wf.op(first_str_provider, "first_string_provider")
            second_string_provider_op = wf.op(second_str_provider, "second_string_provider")

            wf.input("in1", first_string_provider_op.i["inp"])
            wf.input("in1_first_wait", first_string_provider_op.i["first_wait"])
            wf.input("in1_second_wait", first_string_provider_op.i["second_wait"])
            wf.output("out1", first_string_provider_op.o["out"])

            wf.input("in2", second_string_provider_op.i["inp"])
            wf.input("in2_first_wait", second_string_provider_op.i["first_wait"])
            wf.input("in2_second_wait", second_string_provider_op.i["second_wait"])
            wf.output("out2", second_string_provider_op.o["out"])

    async with async_test_client as ac:
        exec_input = ExecByIdInput(
            id=wf.id,
            job_id="3c44cf6a-9cf1-42e9-873b-bc015148f04e",
            wiring=WorkflowWiring(
                input_wirings=[
                    {"workflow_input_name": "in1", "filters": {"value": "in1"}},
                    {"workflow_input_name": "in1_first_wait", "filters": {"value": "1.0"}},
                    {"workflow_input_name": "in1_second_wait", "filters": {"value": "1.0"}},
                    {"workflow_input_name": "in2", "filters": {"value": "in2"}},
                    {"workflow_input_name": "in2_first_wait", "filters": {"value": "1.2"}},
                    {"workflow_input_name": "in2_second_wait", "filters": {"value": "0.2"}},
                ]
            ),
        )
        resp = await ac.post(
            "/api/transformations/execute", json=json.loads(exec_input.model_dump_json())
        )
        assert resp.status_code == 200
        resp_json = resp.json()

        assert resp_json["output_results_by_output_name"]["out1"] == "in1"
        assert resp_json["output_results_by_output_name"]["out2"] == "in2"

        assert len(resp_json["gathered_component_code_logs"]) == 6

        for log_entry in resp_json["gathered_component_code_logs"]:
            if log_entry["message"].endswith("in1"):
                assert str(log_entry["tr_id"]) == str(first_str_provider.id)
            if log_entry["message"].endswith("in2"):
                assert str(log_entry["tr_id"]) == str(second_str_provider.id)

        # actually concurrent?
        assert resp_json["gathered_component_code_logs"][2]["message"].endswith("in1")
        assert resp_json["gathered_component_code_logs"][3]["message"].endswith("in2")
        assert resp_json["gathered_component_code_logs"][4]["message"].endswith("in2")
        # Actually no:
        assert resp_json["gathered_component_code_logs"][5]["message"].endswith("in2")

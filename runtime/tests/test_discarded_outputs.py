"""Test skipping unneeded outputs

See docs/user_guide/component_writing/discarded_outputs.md
"""

import json
import os
import sys

import pytest

from hdutils import plot_output_needed
from hetdesrun.models.execution import ExecByIdInput
from hetdesrun.models.run import ConfigurationInput, WorkflowExecutionInput
from hetdesrun.models.wiring import OutputWiring, WorkflowWiring
from hetdesrun.runtime.configuration import execution_config
from hetdesrun.runtime.context import discarded_outputs_context, output_is_discarded
from hetdesrun.runtime.engine.plain.parsing import parse_workflow_input
from hetdesrun.runtime.engine.plain.workflow import (
    ComputationNode,
    Workflow,
    mark_discarded_outputs,
    obtain_all_nodes,
)
from hetdesrun.runtime.service import discarded_wf_output_names
from hetdesrun.trafoutils.trafo_collection import TrafoCollection


def report_discarded_outputs():
    return {
        "data": 42,
        "plot": {"plot_discarded": output_is_discarded("plot")},
    }


def computation_node(name: str) -> ComputationNode:
    return ComputationNode(
        func=report_discarded_outputs,
        operator_hierarchical_id=name,
        output_names=["data", "plot"],
    )


def workflow(
    sub_nodes: list,
    output_mappings: dict,
    inputs: dict | None = None,
    input_mappings: dict | None = None,
) -> Workflow:
    return Workflow(
        sub_nodes=sub_nodes,
        input_mappings=input_mappings if input_mappings is not None else {},
        output_mappings=output_mappings,
        inputs=inputs,
        tr_id="UNKNOWN",
        tr_name="UNKNOWN",
        tr_tag="UNKNOWN",
    )


@pytest.mark.asyncio
async def test_dropped_workflow_output_is_discarded_in_component():
    node = computation_node("node")
    wf = workflow([node], {"data": (node, "data"), "plot": (node, "plot")})

    mark_discarded_outputs(wf, {"plot"})

    assert node.discarded_outputs == {"plot"}
    assert (await wf.result)["plot"] == {"plot_discarded": True}
    # only available during the execution of the component
    assert output_is_discarded("plot") is False


def test_not_exposed_output_is_discarded():
    node = computation_node("node")
    wf = workflow([node], {"data": (node, "data")})

    mark_discarded_outputs(wf, set())

    assert node.discarded_outputs == {"plot"}


def test_linked_output_is_not_discarded():
    node = computation_node("node")
    consuming_node = ComputationNode(func=lambda *, x: {"y": x}, inputs={"x": (node, "plot")})
    wf = workflow([node, consuming_node], {"data": (node, "data"), "plot": (node, "plot")})

    mark_discarded_outputs(wf, {"data", "plot"})

    assert node.discarded_outputs == {"data"}


def test_discarded_outputs_in_nested_workflows():
    inner_node = computation_node("inner")
    sub_wf = workflow(
        [inner_node], {"sub_data": (inner_node, "data"), "sub_plot": (inner_node, "plot")}
    )
    wf = workflow([sub_wf], {"data": (sub_wf, "sub_data"), "plot": (sub_wf, "sub_plot")})

    mark_discarded_outputs(wf, {"plot"})
    assert inner_node.discarded_outputs == {"plot"}

    mark_discarded_outputs(wf, set())
    assert inner_node.discarded_outputs == frozenset()


def test_output_linked_from_sub_workflow_is_not_discarded():
    inner_node = computation_node("inner")
    sub_wf = workflow([inner_node], {"sub_plot": (inner_node, "plot")})

    consuming_inner_node = ComputationNode(func=lambda *, x: {"y": x})
    consuming_sub_wf = workflow(
        [consuming_inner_node],
        {"y": (consuming_inner_node, "y")},
        inputs={"x": (sub_wf, "sub_plot")},
        input_mappings={"x": (consuming_inner_node, "x")},
    )
    wf = workflow([sub_wf, consuming_sub_wf], {"y": (consuming_sub_wf, "y")})

    mark_discarded_outputs(wf, {"y"})

    assert inner_node.discarded_outputs == {"data"}


@pytest.mark.asyncio
async def test_all_outputs_discarded_mixed_node_is_run():
    node = computation_node("node")
    wf = workflow([node], {"data": (node, "data"), "plot": (node, "plot")})

    mark_discarded_outputs(wf, {"data", "plot"})

    assert (await wf.result)["plot"] == {"plot_discarded": True}


def plot_workflow(run_nodes: list[str]) -> tuple[Workflow, ComputationNode]:
    def provide_data():
        run_nodes.append("data")
        return {"data": 42}

    def plot_data(*, data):
        run_nodes.append("plot")
        return {"plot": {"data": data}}

    data_node = ComputationNode(func=provide_data, output_names=["data"])
    plot_node = ComputationNode(
        func=plot_data,
        inputs={"data": (data_node, "data")},
        has_only_plot_outputs=True,
        output_names=["plot"],
    )
    wf = workflow([data_node, plot_node], {"plot": (plot_node, "plot")})
    return wf, plot_node


@pytest.mark.asyncio
async def test_pure_plot_node_with_discarded_outputs_is_not_run_but_gathers_inputs():
    run_nodes: list[str] = []
    wf, plot_node = plot_workflow(run_nodes)

    mark_discarded_outputs(wf, {"plot"})

    assert await plot_node.result == {"plot": {}}
    # the input providing node is run first as without discarded outputs
    assert run_nodes == ["data"]


@pytest.mark.asyncio
async def test_pure_plot_node_with_used_outputs_is_run():
    run_nodes: list[str] = []
    wf, plot_node = plot_workflow(run_nodes)

    mark_discarded_outputs(wf, set())

    assert await plot_node.result == {"plot": {"data": 42}}
    assert run_nodes == ["data", "plot"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("discarded_wf_outputs", "plot_node_run"),
    [({"plot_a"}, True), ({"plot_a", "plot_b"}, False)],
)
async def test_pure_plot_node_is_only_skipped_if_all_outputs_are_discarded(
    discarded_wf_outputs, plot_node_run
):
    run_nodes: list[str] = []

    def plot_twice():
        run_nodes.append("plot")
        return {"plot_a": {"data": []}, "plot_b": {"data": []}}

    plot_node = ComputationNode(
        func=plot_twice, has_only_plot_outputs=True, output_names=["plot_a", "plot_b"]
    )
    wf = workflow([plot_node], {"plot_a": (plot_node, "plot_a"), "plot_b": (plot_node, "plot_b")})

    mark_discarded_outputs(wf, discarded_wf_outputs)
    await wf.result

    assert (run_nodes == ["plot"]) is plot_node_run


@pytest.mark.asyncio
async def test_node_without_outputs_is_run():
    run_nodes: list[str] = []
    node = ComputationNode(
        func=lambda: run_nodes.append("node") or {},
        has_only_plot_outputs=True,
        output_names=[],
    )
    wf = workflow([node], {})

    mark_discarded_outputs(wf, set())

    assert node.has_only_discarded_plot_outputs is False
    await node.result
    assert run_nodes == ["node"]


def test_discarded_wf_output_names():
    wiring = WorkflowWiring(
        output_wirings=[
            OutputWiring(workflow_output_name="direct", adapter_id="direct_provisioning"),
            OutputWiring(workflow_output_name="dropped", adapter_id="drop"),
            OutputWiring(workflow_output_name="plotted", adapter_id="plot"),
        ]
    )

    assert discarded_wf_output_names(wiring, ConfigurationInput(run_pure_plot_operators=True)) == {
        "dropped"
    }
    assert discarded_wf_output_names(wiring, ConfigurationInput(run_pure_plot_operators=False)) == {
        "dropped",
        "plotted",
    }
    assert (
        discarded_wf_output_names(wiring, ConfigurationInput(return_individual_node_results=True))
        == set()
    )


def test_plot_output_needed():
    assert plot_output_needed("plot") is True

    with discarded_outputs_context(frozenset({"plot"})):
        assert plot_output_needed("plot") is False
        assert plot_output_needed("other_plot") is True

    token = execution_config.set(ConfigurationInput(run_pure_plot_operators=False))
    try:
        assert plot_output_needed("plot") is False
    finally:
        execution_config.reset(token)


def test_plot_output_needed_without_hetdesrun(monkeypatch):
    for module_name in [
        "hetdesrun.models.run",
        "hetdesrun.runtime.configuration",
        "hetdesrun.runtime.context",
    ]:
        # makes importing the module raise an ImportError
        monkeypatch.setitem(sys.modules, module_name, None)

    with discarded_outputs_context(frozenset({"plot"})):
        assert plot_output_needed("plot") is True


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("output_adapters", "run_pure_plot_operators", "expected_info"),
    [
        (
            {},
            True,
            {
                "info_discarded": False,
                "data_discarded": False,
                "plot_discarded": False,
                "plot_needed": True,
            },
        ),
        (
            {"data": "drop", "plot": "drop"},
            True,
            {
                "info_discarded": False,
                "data_discarded": True,
                "plot_discarded": True,
                "plot_needed": False,
            },
        ),
        (
            {},
            False,
            {
                "info_discarded": False,
                "data_discarded": False,
                "plot_discarded": False,
                "plot_needed": False,
            },
        ),
        (
            {"plot": "plot"},
            False,
            {
                "info_discarded": False,
                "data_discarded": False,
                "plot_discarded": True,
                "plot_needed": False,
            },
        ),
    ],
)
async def test_discarded_outputs_reach_component(
    mocked_clean_test_db_session,
    async_test_client,
    output_adapters,
    run_pure_plot_operators,
    expected_info,
):
    with TrafoCollection(save_to_db=True) as tc:
        component = tc.add_from_py_file(
            os.path.join("tests", "data", "components", "discarded_outputs_info.py")
        )

    exec_input = ExecByIdInput(
        id=component.id,
        wiring=WorkflowWiring(
            output_wirings=[
                OutputWiring(workflow_output_name=output_name, adapter_id=adapter_id)
                for output_name, adapter_id in output_adapters.items()
            ]
        ),
        run_pure_plot_operators=run_pure_plot_operators,
    )

    async with async_test_client as ac:
        resp = await ac.post(
            "/api/transformations/execute", json=json.loads(exec_input.model_dump_json())
        )
        assert resp.status_code == 200
        resp_json = resp.json()
        assert resp_json["error"] is None

        assert resp_json["output_results_by_output_name"]["info"] == expected_info


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("adapter_id", "plot_created"),
    [("direct_provisioning", True), ("drop", False)],
)
async def test_pure_plot_component_is_only_run_if_plot_is_used(
    mocked_clean_test_db_session, async_test_client, adapter_id, plot_created
):
    with TrafoCollection(save_to_db=True) as tc:
        component = tc.add_from_py_file(
            os.path.join("tests", "data", "components", "logging_plot.py")
        )

    exec_input = ExecByIdInput(
        id=component.id,
        wiring=WorkflowWiring(
            output_wirings=[OutputWiring(workflow_output_name="plot", adapter_id=adapter_id)]
        ),
        run_pure_plot_operators=True,
    )

    async with async_test_client as ac:
        resp = await ac.post(
            "/api/transformations/execute", json=json.loads(exec_input.model_dump_json())
        )
        assert resp.status_code == 200
        resp_json = resp.json()
        assert resp_json["error"] is None

        log_messages = [record["message"] for record in resp_json["gathered_component_code_logs"]]
        assert ("Creating plot" in log_messages) is plot_created


@pytest.mark.asyncio
@pytest.mark.parametrize("run_pure_plot_operators", [True, False])
async def test_component_without_outputs_is_run(
    mocked_clean_test_db_session, async_test_client, run_pure_plot_operators
):
    with TrafoCollection(save_to_db=True) as tc:
        component = tc.add_from_py_file(
            os.path.join("tests", "data", "components", "logging_without_outputs.py")
        )

    exec_input = ExecByIdInput(
        id=component.id,
        wiring=WorkflowWiring(),
        run_pure_plot_operators=run_pure_plot_operators,
    )

    async with async_test_client as ac:
        resp = await ac.post(
            "/api/transformations/execute", json=json.loads(exec_input.model_dump_json())
        )
        assert resp.status_code == 200
        resp_json = resp.json()
        assert resp_json["error"] is None

        log_messages = [record["message"] for record in resp_json["gathered_component_code_logs"]]
        assert "Running without outputs" in log_messages


def nested_wf_execution_input_with_dropped_plot() -> dict:
    """Nested workflow whose plot output from an operator of a sub workflow is dropped"""
    with open(
        os.path.join("tests", "data", "nested_wf_execution_input.json"), encoding="utf8"
    ) as f:
        execution_input = json.load(f)

    for output_wiring in execution_input["workflow_wiring"]["output_wirings"]:
        if output_wiring["workflow_output_name"] == "rul_regression_result_plot":
            output_wiring["adapter_id"] = "drop"

    return execution_input


def test_discarded_outputs_in_parsed_nested_workflow():
    execution_input = WorkflowExecutionInput(**nested_wf_execution_input_with_dropped_plot())
    parsed_wf = parse_workflow_input(
        execution_input.workflow, execution_input.components, execution_input.code_modules
    )

    mark_discarded_outputs(
        parsed_wf,
        discarded_wf_output_names(execution_input.workflow_wiring, execution_input.configuration),
    )

    nodes_with_discarded_outputs = [
        node for node in obtain_all_nodes(parsed_wf) if len(node.discarded_outputs) > 0
    ]
    assert len(nodes_with_discarded_outputs) == 1
    plot_node = nodes_with_discarded_outputs[0]
    assert plot_node.discarded_outputs == {"rul_regression_result_plot"}
    assert plot_node.has_only_discarded_plot_outputs is True
    # the plot operator is part of a sub workflow
    assert plot_node not in parsed_wf.sub_nodes


@pytest.mark.asyncio
async def test_nested_workflow_with_dropped_plot_is_executed(async_test_client):
    async with async_test_client as client:
        response = await client.post(
            "engine/runtime", json=nested_wf_execution_input_with_dropped_plot()
        )

    assert response.status_code == 200
    response_json = response.json()
    assert response_json["result"] == "ok"
    assert "rul_regression_result_plot" not in response_json["output_results_by_output_name"]
    assert response_json["output_results_by_output_name"]["limit_violation_timestamp"].startswith(
        "2020-05-28T20:16:41"
    )

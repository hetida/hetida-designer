import logging

import pytest

from hetdesrun.runtime.engine.plain.workflow import ComputationNode, Workflow
from hetdesrun.runtime.exceptions import (
    CircularDependency,
    MissingInputSource,
    MissingOutputException,
    RuntimeExecutionError,
)


@pytest.mark.asyncio
async def test_computation_nodes():
    def provide_two_values():
        return {"a": 1.2, "b": 2.5}

    def add_two_values(*, c, d):
        return {"sum": c + d}

    source_node = ComputationNode(func=provide_two_values)
    target_node = ComputationNode(
        func=add_two_values, inputs={"c": (source_node, "a"), "d": (source_node, "b")}
    )

    res = await target_node.result
    assert res["sum"] == 3.7


@pytest.mark.asyncio
async def test_computation_nodes_wrong_inputs():
    def provide_two_values():
        return {"a": 1.2, "wrong": 2.5}

    def add_two_values(*, c, d):
        return {"sum": c + d}

    source_node = ComputationNode(func=provide_two_values)
    target_node = ComputationNode(
        func=add_two_values,
        inputs={
            "c": (source_node, "a"),
            "d": (
                source_node,
                # b is not present in the output of source_node
                "b",
            ),
        },
    )

    with pytest.raises(MissingOutputException):
        res = await target_node.result


@pytest.mark.asyncio
async def test_computation_wrong_input_source():
    def provide_two_values():
        return {"a": 1.2, "b": 2.5}

    def add_two_values(*, c, d):
        return {"sum": c + d}

    source_node = ComputationNode(func=provide_two_values)
    target_node = ComputationNode(
        func=add_two_values,
        inputs={  # here something for d is missing
            "c": (source_node, "a"),
            "wrong": (source_node, "b"),
        },
    )

    with pytest.raises(MissingInputSource):
        res = await target_node.result


@pytest.mark.asyncio
async def test_computation_cycle_detection():
    def provide_two_values():
        return {"a": 1.2, "b": 2.5}

    def add_two_values(*, c, d):
        return {"sum": c + d}

    source_node = ComputationNode(func=provide_two_values)
    target_node = ComputationNode(
        func=add_two_values,
        inputs={  # here something for d is missing
            "c": (source_node, "a"),
            "d": (source_node, "b"),
        },
    )
    source_node.add_inputs({"some_input": (target_node, "sum")})

    with pytest.raises(CircularDependency):
        res = await target_node.result


@pytest.mark.asyncio
async def test_computation_nodes_user_raised_runtime_error_and_logging(caplog):
    def provide_two_values():
        return {"a": 1.2, "b": 2.5}

    def add_two_values(*, c, d):
        raise RuntimeExecutionError("Error in user code!")
        return {"sum": c + d}

    source_node = ComputationNode(
        func=provide_two_values,
        operator_hierarchical_id="SOURCE_ID",
        operator_hierarchical_name="TEST_SOURCE_OPERATOR",
    )
    target_node = ComputationNode(
        func=add_two_values,
        inputs={
            "c": (source_node, "a"),
            "d": (
                source_node,
                # b is not present in the output of source_node
                "b",
            ),
        },
    )

    with caplog.at_level(logging.INFO):
        caplog.clear()
        with pytest.raises(RuntimeExecutionError):
            res = await target_node.result

        assert "User raised" in caplog.text
        assert "UNKNOWN" in caplog.text
        assert "SOURCE_ID" in caplog.text
        assert "TEST_SOURCE_OPERATOR" in caplog.text


@pytest.mark.asyncio
async def test_basic_workflow_execution():
    def provide_two_values():
        return {"a": 1.2, "b": 2.5}

    def add_two_values(*, c, d):
        return {"sum": c + d}

    source_node = ComputationNode(func=provide_two_values)
    target_node = ComputationNode(
        func=add_two_values, inputs={"c": (source_node, "a"), "d": (source_node, "b")}
    )

    wf = Workflow(
        sub_nodes=[source_node, target_node],
        input_mappings={},
        output_mappings={"sum_result": (target_node, "sum")},
    )

    res = await wf.result
    assert res["sum_result"] == 3.7


@pytest.mark.asyncio
async def test_workflow_with_inputs_via_constant_node():
    def add_two_values(*, c, d):
        return {"sum": c + d}

    target_node = ComputationNode(
        func=add_two_values,
        operator_hierarchical_name="sum node",
        operator_hierarchical_id="sum node",
    )

    wf = Workflow(
        sub_nodes=[target_node],
        input_mappings={"first": (target_node, "c"), "second": (target_node, "d")},
        output_mappings={"sum_result": (target_node, "sum")},
        operator_hierarchical_name="Workflow",
        operator_hierarchical_id="Workflow",
    )

    wf.add_constant_providing_node(
        [
            {"name": "first", "value": 1.9, "type": "FLOAT"},
            {"name": "second", "value": 0.1, "type": "FLOAT"},
        ]
    )

    res = await wf.result
    assert res["sum_result"] == 2.0


@pytest.mark.asyncio
async def test_nested_workflow():
    def provide_two_values():
        return {"a": 1.2, "b": 2.5}

    def add_two_values(*, c, d):
        return {"sum": c + d}

    source_node = ComputationNode(func=provide_two_values)

    target_node_in_sub_wf = ComputationNode(
        func=add_two_values, inputs={"c": (source_node, "a"), "d": (source_node, "b")}
    )

    sub_wf = Workflow(
        sub_nodes=[target_node_in_sub_wf],
        input_mappings={
            "sub_wf_first_inp": (target_node_in_sub_wf, "c"),
            "sub_wf_second_inp": (target_node_in_sub_wf, "d"),
        },
        output_mappings={"sub_wf_sum_outp": (target_node_in_sub_wf, "sum")},
        inputs={
            "sub_wf_first_inp": (source_node, "a"),
            "sub_wf_second_inp": (source_node, "b"),
        },
    )

    wf = Workflow(
        sub_nodes=[source_node, sub_wf],
        input_mappings={},
        output_mappings={"sum_result": (sub_wf, "sub_wf_sum_outp")},
    )

    res = await wf.result
    assert res["sum_result"] == 3.7

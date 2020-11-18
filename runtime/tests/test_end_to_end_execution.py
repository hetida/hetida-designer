from copy import deepcopy

import json
import os
from uuid import uuid4

from unittest import mock

import pytest

from starlette.testclient import TestClient

from hetdesrun.utils import get_uuid_from_seed
from hetdesrun.service.webservice import app

from hetdesrun.models.code import CodeModule
from hetdesrun.models.component import (
    ComponentRevision,
    ComponentInput,
    ComponentOutput,
    ComponentNode,
)
from hetdesrun.models.workflow import (
    WorkflowNode,
    WorkflowConnection,
    WorkflowInput,
    WorkflowOutput,
)

from hetdesrun.models.wiring import OutputWiring, InputWiring, WorkflowWiring

from hetdesrun.models.run import (
    ConfigurationInput,
    ExecutionEngine,
    WorkflowExecutionInput,
    WorkflowExecutionResult,
)


from hetdesrun.runtime.context import execution_context

from hetdesrun.utils import load_data, file_pathes_from_component_json

client = TestClient(app)


def run_workflow_with_client(workflow_json):
    response = client.post("/runtime", json=workflow_json)
    return response.status_code, response.json()


def gen_execution_input_from_single_component(
    component_json_path, direct_provisioning_data_dict=None, wf_wiring=None
):
    """Wraps a single component into a workflow and generates the execution input json

    input data is provided directly
    """

    if (direct_provisioning_data_dict is None) == (wf_wiring is None):
        raise ValueError(
            "Excatly one of direct_provisioning_data_dict or wf_wiring must be provided"
        )

    # Load component stuff
    (
        base_name,
        path_to_component_json,
        component_doc_file,
        component_code_file,
    ) = file_pathes_from_component_json(component_json_path)

    info, doc, code = load_data(
        path_to_component_json, component_doc_file, component_code_file
    )

    # Build up execution input Json
    code_module_uuid = str(get_uuid_from_seed("code_module_uuid"))
    component_uuid = str(get_uuid_from_seed("component_uuid"))

    comp_inputs = [
        ComponentInput(id=str(uuid4()), name=inp["name"], type=inp["type"])
        for inp in info["inputs"]
    ]

    comp_outputs = [
        ComponentOutput(id=str(uuid4()), name=outp["name"], type=outp["type"])
        for outp in info["outputs"]
    ]

    component_node_id = "component_node_id"

    return WorkflowExecutionInput(
        code_modules=[CodeModule(code=code, uuid=code_module_uuid)],
        components=[
            ComponentRevision(
                uuid=component_uuid,
                name=info["name"],
                code_module_uuid=code_module_uuid,
                function_name="main",
                inputs=comp_inputs,
                outputs=comp_outputs,
            )
        ],
        workflow=WorkflowNode(
            id="root_node",
            sub_nodes=[
                ComponentNode(component_uuid=component_uuid, id=component_node_id)
            ],
            connections=[],
            inputs=[
                WorkflowInput(
                    id=str(get_uuid_from_seed(str(comp_input.id) + "_as_wf_input")),
                    id_of_sub_node=component_node_id,
                    name=comp_input.name,
                    name_in_subnode=comp_input.name,
                    type=comp_input.type,
                )
                for comp_input in comp_inputs
            ],
            outputs=[
                WorkflowOutput(
                    id=str(get_uuid_from_seed(str(comp_output.id) + "_as_wf_output")),
                    id_of_sub_node=component_node_id,
                    name=comp_output.name,
                    name_in_subnode=comp_output.name,
                    type=comp_output.type,
                )
                for comp_output in comp_outputs
            ],
            name="root node",
        ),
        configuration=ConfigurationInput(engine="plain", run_pure_plot_operators=True),
        workflow_wiring=WorkflowWiring(
            input_wirings=[
                InputWiring(
                    workflow_input_name=comp_input.name,
                    adapter_id="direct_provisioning",
                    filters={"value": direct_provisioning_data_dict[comp_input.name]},
                )
                for comp_input in comp_inputs
            ],
            output_wirings=[
                OutputWiring(
                    workflow_output_name=comp_output.name,
                    adapter_id="direct_provisioning",
                )
                for comp_output in comp_outputs
            ],
        )
        if wf_wiring is None
        else wf_wiring,
    )


def run_single_component(component_json_file_path, input_data_dict):
    response = client.post(
        "/runtime",
        data=gen_execution_input_from_single_component(
            component_json_file_path, input_data_dict,
        ).json(),
    )
    return WorkflowExecutionResult(**response.json())


def test_null_values_pass_any_pass_through():
    exec_result = run_single_component(
        "./components/Connectors/pass_through.json", {"input": {"a": 1.5, "b": None}}
    )
    assert exec_result.output_results_by_output_name["output"] == {"a": 1.5, "b": None}


def test_null_list_values_pass_any_pass_through():
    exec_result = run_single_component(
        "./components/Connectors/pass_through.json", {"input": [1.2, None]}
    )
    assert exec_result.output_results_by_output_name["output"] == [1.2, None]


def test_null_values_pass_series_pass_through():
    exec_result = run_single_component(
        "./components/Connectors/pass_through_series.json",
        {"input": {"2020-01-01T00:00:00Z": 1.5, "2020-01-02T00:00:00Z": None}},
    )
    assert exec_result.output_results_by_output_name["output"] == {
        "2020-01-01T00:00:00.000Z": 1.5,
        "2020-01-02T00:00:00.000Z": None,
    }

    exec_result = run_single_component(
        "./components/Connectors/pass_through_series.json", {"input": [1.2, 2.5, None]},
    )
    assert exec_result.output_results_by_output_name["output"] == {
        "0": 1.2,
        "1": 2.5,
        "2": None,
    }


def test_all_null_values_pass_series_pass_through():
    exec_result = run_single_component(
        "./components/Connectors/pass_through_series.json",
        {"input": {"2020-01-01T00:00:00Z": None, "2020-01-02T00:00:00Z": None}},
    )
    assert exec_result.output_results_by_output_name["output"] == {
        "2020-01-01T00:00:00.000Z": None,
        "2020-01-02T00:00:00.000Z": None,
    }


def test_nested_wf_execution():
    with open(os.path.join("tests", "data", "nested_wf_execution_input.json")) as f:
        loaded_workflow_exe_input = json.load(f)

    response_status_code, response_json = run_workflow_with_client(
        loaded_workflow_exe_input
    )

    assert response_status_code == 200
    assert response_json["result"] == "ok"
    assert response_json["output_results_by_output_name"][
        "limit_violation_timestamp"
    ].startswith("2020-05-28T20:16:41")

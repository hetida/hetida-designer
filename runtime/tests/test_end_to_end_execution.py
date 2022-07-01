import json
import os
from uuid import uuid4

import pytest

from hetdesrun.exportimport.importing import load_json
from hetdesrun.models.code import CodeModule
from hetdesrun.models.component import (
    ComponentInput,
    ComponentNode,
    ComponentOutput,
    ComponentRevision,
)
from hetdesrun.models.run import (
    ConfigurationInput,
    WorkflowExecutionInput,
    WorkflowExecutionResult,
)
from hetdesrun.models.wiring import InputWiring, OutputWiring, WorkflowWiring
from hetdesrun.models.workflow import WorkflowInput, WorkflowNode, WorkflowOutput
from hetdesrun.utils import get_uuid_from_seed


async def run_workflow_with_client(workflow_json, open_async_test_client):
    response = await open_async_test_client.post("engine/runtime", json=workflow_json)
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

    tr_component_json = load_json(component_json_path)
    code = tr_component_json["content"]

    # Build up execution input Json
    code_module_uuid = str(get_uuid_from_seed("code_module_uuid"))
    component_uuid = str(get_uuid_from_seed("component_uuid"))

    comp_inputs = [
        ComponentInput(id=str(uuid4()), name=inp["name"], type=inp["data_type"])
        for inp in tr_component_json["io_interface"]["inputs"]
    ]

    comp_outputs = [
        ComponentOutput(id=str(uuid4()), name=outp["name"], type=outp["data_type"])
        for outp in tr_component_json["io_interface"]["outputs"]
    ]

    component_node_id = "component_node_id"

    return WorkflowExecutionInput(
        code_modules=[CodeModule(code=code, uuid=code_module_uuid)],
        components=[
            ComponentRevision(
                uuid=component_uuid,
                name=tr_component_json["name"],
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
                    adapter_id=1,
                    filters={"value": direct_provisioning_data_dict[comp_input.name]},
                )
                for comp_input in comp_inputs
            ],
            output_wirings=[
                OutputWiring(
                    workflow_output_name=comp_output.name,
                    adapter_id=1,
                )
                for comp_output in comp_outputs
            ],
        )
        if wf_wiring is None
        else wf_wiring,
    )


async def run_single_component(
    component_json_file_path, input_data_dict, open_async_test_client
):

    response = await open_async_test_client.post(
        "engine/runtime",
        json=json.loads(
            gen_execution_input_from_single_component(
                component_json_file_path,
                input_data_dict,
            ).json()
        ),
    )

    return WorkflowExecutionResult(**response.json())


@pytest.mark.asyncio
async def test_null_values_pass_any_pass_through(async_test_client):
    async with async_test_client as client:

        exec_result = await run_single_component(
            (
                "./transformations/components/connectors/"
                "pass-through_100_1946d5f8-44a8-724c-176f-16f3e49963af.json"
            ),
            {"input": {"a": 1.5, "b": None}},
            client,
        )

        assert exec_result.output_results_by_output_name["output"] == {
            "a": 1.5,
            "b": None,
        }


@pytest.mark.asyncio
async def test_null_list_values_pass_any_pass_through(async_test_client):
    async with async_test_client as client:

        exec_result = await run_single_component(
            (
                "./transformations/components/connectors/"
                "pass-through_100_1946d5f8-44a8-724c-176f-16f3e49963af.json"
            ),
            {"input": [1.2, None]},
            client,
        )
        assert exec_result.output_results_by_output_name["output"] == [1.2, None]


@pytest.mark.asyncio
async def test_null_values_pass_series_pass_through(async_test_client):
    async with async_test_client as client:

        exec_result = await run_single_component(
            (
                "./transformations/components/connectors/"
                "pass-through_100_1946d5f8-44a8-724c-176f-16f3e49963af.json"
            ),
            {"input": {"2020-01-01T00:00:00Z": 1.5, "2020-01-02T00:00:00Z": None}},
            client,
        )
        assert exec_result.output_results_by_output_name["output"] == {
            "2020-01-01T00:00:00Z": 1.5,
            "2020-01-02T00:00:00Z": None,
        }

        exec_result = await run_single_component(
            (
                "./transformations/components/connectors/"
                "pass-through_100_1946d5f8-44a8-724c-176f-16f3e49963af.json"
            ),
            {"input": [1.2, 2.5, None]},
            client,
        )
        assert exec_result.output_results_by_output_name["output"] == [1.2, 2.5, None]


@pytest.mark.asyncio
async def test_all_null_values_pass_series_pass_through(async_test_client):
    async with async_test_client as client:

        exec_result = await run_single_component(
            (
                "./transformations/components/connectors/"
                "pass-through_100_1946d5f8-44a8-724c-176f-16f3e49963af.json"
            ),
            {"input": {"2020-01-01T00:00:00Z": None, "2020-01-02T00:00:00Z": None}},
            client,
        )
        assert exec_result.output_results_by_output_name["output"] == {
            "2020-01-01T00:00:00Z": None,
            "2020-01-02T00:00:00Z": None,
        }


@pytest.mark.asyncio
async def test_nested_wf_execution(async_test_client):
    async with async_test_client as client:

        with open(
            os.path.join("tests", "data", "nested_wf_execution_input.json"),
            encoding="utf8",
        ) as f:
            loaded_workflow_exe_input = json.load(f)
        response_status_code, response_json = await run_workflow_with_client(
            loaded_workflow_exe_input, client
        )

        assert response_status_code == 200
        assert response_json["result"] == "ok"
        assert response_json["output_results_by_output_name"][
            "limit_violation_timestamp"
        ].startswith("2020-05-28T20:16:41")

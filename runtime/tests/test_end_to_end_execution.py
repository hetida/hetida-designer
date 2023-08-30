import json
import os
from copy import deepcopy
from typing import Any
from uuid import uuid4

import pytest
from httpx import AsyncClient

from hetdesrun.models.run import (
    ConfigurationInput,
    WorkflowExecutionInput,
    WorkflowExecutionResult,
)
from hetdesrun.models.wiring import InputWiring, OutputWiring, WorkflowWiring
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.trafoutils.io.load import load_json


async def run_workflow_with_client(
    workflow_json: dict, open_async_test_client: AsyncClient
) -> tuple[int, Any]:
    response = await open_async_test_client.post("engine/runtime", json=workflow_json)
    return response.status_code, response.json()


def gen_execution_input_from_single_component(
    component_json_path: str,
    direct_provisioning_data_dict: dict | None = None,
    wf_wiring: WorkflowWiring | None = None,
) -> WorkflowExecutionInput:
    """Wraps a single component into a workflow and generates the execution input json

    input data is provided directly
    """

    if (direct_provisioning_data_dict is None) == (wf_wiring is None):
        raise ValueError(
            "Excatly one of direct_provisioning_data_dict or wf_wiring must be provided"
        )

    tr_component_json = load_json(component_json_path)
    tr_component = TransformationRevision(**tr_component_json)
    wrapping_wf = tr_component.wrap_component_in_tr_workflow()
    assert len(wrapping_wf.content.operators) != 0

    return WorkflowExecutionInput(
        code_modules=[tr_component.to_code_module()],
        components=[tr_component.to_component_revision()],
        workflow=wrapping_wf.to_workflow_node(
            operator_id=uuid4(),
            sub_nodes=[
                tr_component.to_component_node(
                    operator_id=wrapping_wf.content.operators[0].id,
                    operator_name=tr_component.name,
                )
            ],
        ),
        configuration=ConfigurationInput(engine="plain", run_pure_plot_operators=True),
        workflow_wiring=WorkflowWiring(
            input_wirings=[
                InputWiring(
                    workflow_input_name=comp_input.name,
                    adapter_id=1,
                    filters={"value": direct_provisioning_data_dict[comp_input.name]}
                    if direct_provisioning_data_dict is not None
                    else None,
                )
                for comp_input in tr_component.io_interface.inputs
            ],
            output_wirings=[
                OutputWiring(
                    workflow_output_name=comp_output.name,
                    adapter_id=1,
                )
                for comp_output in tr_component.io_interface.outputs
            ],
        )
        if wf_wiring is None
        else wf_wiring,
    )


async def execute_workflow_execution_input(
    workflow_execution_input: WorkflowExecutionInput,
    open_async_test_client: AsyncClient,
) -> WorkflowExecutionResult:
    response = await open_async_test_client.post(
        "engine/runtime", json=json.loads(workflow_execution_input.json())
    )

    return WorkflowExecutionResult(**response.json())


async def run_single_component(
    component_json_file_path: str,
    input_data_dict: dict,
    open_async_test_client: AsyncClient,
) -> WorkflowExecutionResult:
    return execute_workflow_execution_input(
        gen_execution_input_from_single_component(
            component_json_file_path,
            input_data_dict,
        ).json(),
        open_async_test_client,
    )


@pytest.mark.asyncio
async def test_null_values_pass_any_pass_through(
    async_test_client: AsyncClient,
) -> None:
    async with async_test_client as client:
        exec_result = await run_single_component(
            (
                "./transformations/components/connectors/"
                "pass-through_100_1946d5f8-44a8-724c-176f-16f3e49963af.json"
            ),
            {"input": '{"a": 1.5, "b": None}'},
            client,
        )

        assert exec_result.output_results_by_output_name["output"] == (
            '{"a": 1.5, "b": None}'
        )


@pytest.mark.asyncio
async def test_null_list_values_pass_any_pass_through(
    async_test_client: AsyncClient,
) -> None:
    async with async_test_client as client:
        exec_result = await run_single_component(
            (
                "./transformations/components/connectors/"
                "pass-through_100_1946d5f8-44a8-724c-176f-16f3e49963af.json"
            ),
            {"input": "[1.2, None]"},
            client,
        )
        assert exec_result.output_results_by_output_name["output"] == "[1.2, None]"


@pytest.mark.asyncio
async def test_null_values_pass_series_pass_through(
    async_test_client: AsyncClient,
) -> None:
    async with async_test_client as client:
        exec_result = await run_single_component(
            (
                "./transformations/components/connectors/"
                "pass-through_100_1946d5f8-44a8-724c-176f-16f3e49963af.json"
            ),
            {"input": '{"2020-01-01T00:00:00Z": 1.5, "2020-01-02T00:00:00Z": None}'},
            client,
        )
        assert exec_result.output_results_by_output_name["output"] == (
            '{"2020-01-01T00:00:00Z": 1.5, "2020-01-02T00:00:00Z": None}'
        )

        exec_result = await run_single_component(
            (
                "./transformations/components/connectors/"
                "pass-through_100_1946d5f8-44a8-724c-176f-16f3e49963af.json"
            ),
            {"input": "[1.2, 2.5, None]"},
            client,
        )
        assert exec_result.output_results_by_output_name["output"] == "[1.2, 2.5, None]"


@pytest.mark.asyncio
async def test_all_null_values_pass_series_pass_through(
    async_test_client: AsyncClient,
) -> None:
    async with async_test_client as client:
        exec_result = await run_single_component(
            (
                "./transformations/components/connectors/"
                "pass-through_100_1946d5f8-44a8-724c-176f-16f3e49963af.json"
            ),
            {"input": '{"2020-01-01T00:00:00Z": None, "2020-01-02T00:00:00Z": None}'},
            client,
        )
        assert exec_result.output_results_by_output_name["output"] == (
            '{"2020-01-01T00:00:00Z": None, "2020-01-02T00:00:00Z": None}'
        )


@pytest.mark.asyncio
async def test_structured_error_messages(
    async_test_client: AsyncClient,
) -> None:
    raise_exception_no_output_component = gen_execution_input_from_single_component(
        (
            "tests/data/components/"
            "raise-exception_010_c4dbcc42-eaec-4587-a362-ce6567f21d92.json"
        ),
        {"dividend": 1, "divisor": 0},
    )
    raise_exception_in_code_intentionally_component = deepcopy(raise_exception_no_output_component)
    raise_exception_in_code_intentionally_component.code_modules[
        0
    ].code = raise_exception_in_code_intentionally_component.code_modules[0].code.replace(
        "pass",
        (
            """if divisor == 0:
            raise ComponentException("The divisor must not equal zero!", error_code=404)
            return {"result": dividend/divisor}
            """
        ),
    )

    raise_exception_in_code_unintentionally_component = deepcopy(raise_exception_no_output_component)
    raise_exception_in_code_unintentionally_component.code_modules[
        0
    ].code = raise_exception_in_code_intentionally_component.code_modules[0].code.replace(
        "pass",
        'return {"result": dividend/divisor}',
    )

    raise_exception_in_sending_data_component = deepcopy(raise_exception_no_output_component)
    raise_exception_in_sending_data_component.code_modules[
        0
    ].code = raise_exception_in_sending_data_component.code_modules[0].code.replace(
        "pass",
        'return {"result": "string instead of series"}',
    )

    raise_exception_in_json_encoding_component = deepcopy(raise_exception_no_output_component)
    raise_exception_in_json_encoding_component.code_modules[
        0
    ].code = raise_exception_in_json_encoding_component.code_modules[0].code.replace(
        "pass",
        'return {"result": str}',
    )

    raise_exception_in_default_value_component = deepcopy(raise_exception_no_output_component)
    raise_exception_in_default_value_component.code_modules[
        0
    ].code = raise_exception_in_default_value_component.code_modules[0].code.replace(
        "def main(*, dividend, divisor):",
        "def main(*, divisor, dividend=asdf):"
    )

    async with async_test_client as client:
        raise_exception_in_code_intentionally_result = await execute_workflow_execution_input(
            raise_exception_in_code_intentionally_component, client
        )

        assert raise_exception_in_code_intentionally_result.error.error_code == 404
        assert raise_exception_in_code_intentionally_result.error.type == "ComponentException"
        assert (
            raise_exception_in_code_intentionally_result.error.operator_info.transformation_info.id
            == "c4dbcc42-eaec-4587-a362-ce6567f21d92"
        )


@pytest.mark.asyncio
async def test_nested_wf_execution(async_test_client: AsyncClient) -> None:
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


@pytest.mark.asyncio
async def test_multitsframe_wf_execution(async_test_client: AsyncClient) -> None:
    async with async_test_client as client:
        with open(
            os.path.join(
                "tests", "data", "timeseries_dataframe_wf_execution_input.json"
            ),
            encoding="utf8",
        ) as f:
            loaded_workflow_exe_input = json.load(f)
        response_status_code, response_json = await run_workflow_with_client(
            loaded_workflow_exe_input, client
        )

        assert response_status_code == 200
        assert response_json["result"] == "ok"
        assert response_json["output_results_by_output_name"]["multitsframe"] == {
            "value": {
                "0": 1,
                "1": 1.2,
                "2": 1.9,
                "3": 1.3,
                "4": 1.5,
                "5": 1.7,
                "6": 0.5,
                "7": 0.2,
                "8": 0.1,
            },
            "metric": {
                "0": "a",
                "1": "b",
                "2": "a",
                "3": "b",
                "4": "a",
                "5": "b",
                "6": "d",
                "7": "d",
                "8": "d",
            },
            "timestamp": {
                "0": "2019-08-01T15:45:36.000Z",
                "1": "2019-08-01T15:45:36.000Z",
                "2": "2019-08-02T15:45:36.000Z",
                "3": "2019-08-02T15:45:36.000Z",
                "4": "2019-08-03T15:45:36.000Z",
                "5": "2019-08-03T15:45:36.000Z",
                "6": "2019-08-01T15:45:36.000Z",
                "7": "2019-08-02T15:45:36.000Z",
                "8": "2019-08-03T15:45:36.000Z",
            },
        }


@pytest.mark.asyncio
async def test_nested_optional_inputs_wf_execution(
    async_test_client: AsyncClient,
) -> None:
    with open(
        os.path.join("tests", "data", "nested_optional_inputs_wf_execution_input.json"),
        encoding="utf8",
    ) as f:
        loaded_workflow_exe_input = json.load(f)

    async with async_test_client as client:
        response_status_code, response_json = await run_workflow_with_client(
            loaded_workflow_exe_input, client
        )

    assert response_status_code == 200
    assert response_json["result"] == "ok"
    assert (
        response_json["output_results_by_output_name"]["intercept"]
        == 2.8778442676301292
    )
    assert (
        response_json["output_results_by_output_name"]["limit_violation_timestamp"]
        == "2020-06-25T16:33:23.934348+00:00"
    )
    assert response_json["output_results_by_output_name"]["slope"] == [
        -3.700034733861136e-7
    ]

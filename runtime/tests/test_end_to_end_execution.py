import json
import os
from typing import Any
from uuid import uuid4

import pytest
from fastapi import HTTPException
from httpx import AsyncClient

from hetdesrun.models.run import (
    ConfigurationInput,
    ProcessStage,
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
    assert not isinstance(wrapping_wf.content, str)
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
        trafo_id=tr_component.id,
    )


async def execute_workflow_execution_input(
    workflow_execution_input: WorkflowExecutionInput,
    open_async_test_client: AsyncClient,
) -> WorkflowExecutionResult:
    response = await open_async_test_client.post(
        "engine/runtime", json=json.loads(workflow_execution_input.json())
    )
    if response.status_code != 200:
        raise HTTPException(response.status_code, detail=response.json()["detail"])
    return WorkflowExecutionResult(**response.json())


async def run_single_component(
    component_json_file_path: str,
    input_data_dict: dict,
    open_async_test_client: AsyncClient,
) -> WorkflowExecutionResult:
    return await execute_workflow_execution_input(
        gen_execution_input_from_single_component(
            component_json_file_path,
            input_data_dict,
        ),
        open_async_test_client,
    )


@pytest.mark.asyncio
async def test_direct_provisioning_series_metadata(
    async_test_client: AsyncClient,
) -> None:
    async with async_test_client as client:
        exec_result = await run_single_component(
            (
                "./transformations/components/connectors/"
                "extract-attributes-series_100_9b160d5b-f821-4b7a-b314-b2c94e54c983.json"
            ),
            {
                "series": (
                    '{"__hd_wrapped_data_object__": "SERIES",'
                    ' "__metadata__": {"test": 42},'
                    ' "__data__": [2.3, 2.4, 2.5] }'
                )
            },
            client,
        )

        assert exec_result.output_results_by_output_name["attributes"] == {"test": 42}

        exec_result = await run_single_component(
            (
                "./transformations/components/connectors/"
                "pass-through-series_100_bfa27afc-dea8-b8aa-4b15-94402f0739b6.json"
            ),
            {
                "input": (
                    '{"__hd_wrapped_data_object__": "SERIES",'
                    ' "__metadata__": {"test": 42},'
                    ' "__data__": [2.3, 2.4, 2.5] }'
                )
            },
            client,
        )

        assert exec_result.output_results_by_output_name["output"] == {
            "__hd_wrapped_data_object__": "SERIES",
            "__metadata__": {"test": 42},
            "__data__": {"name": None, "index": [0, 1, 2], "data": [2.3, 2.4, 2.5]},
            "__data_parsing_options__": {"orient": "split"},
        }


@pytest.mark.asyncio
async def test_direct_provisioning_dataframe_metadata(
    async_test_client: AsyncClient,
) -> None:
    async with async_test_client as client:
        exec_result = await run_single_component(
            (
                "./transformations/components/connectors/"
                "extract-attributes-dataframe_100_816436b2-f303-48af-857c-6c4d7c7a0f4b.json"
            ),
            {
                "dataframe": (
                    '{"__hd_wrapped_data_object__": "DATAFRAME",'
                    ' "__metadata__": {"test": 43},'
                    ' "__data__": {"a": [2.3, 2.4, 2.5], "b": ["t", "t", "k"]} }'
                )
            },
            client,
        )

        assert exec_result.output_results_by_output_name["attributes"] == {"test": 43}

        exec_result = await run_single_component(
            (
                "./transformations/components/connectors/"
                "pass-through-dataframe_100_7a1a818f-fa89-6062-1e0e-fc80539bbe0a.json"
            ),
            {
                "input": (
                    '{"__hd_wrapped_data_object__": "DATAFRAME",'
                    ' "__metadata__": {"test": 43},'
                    ' "__data__": {"a": [2.3, 2.4, 2.5], "b": ["t", "t", "k"]} }'
                )
            },
            client,
        )

        assert exec_result.output_results_by_output_name["output"] == {
            "__hd_wrapped_data_object__": "DATAFRAME",
            "__metadata__": {"test": 43},
            "__data__": {
                "a": {"0": 2.3, "1": 2.4, "2": 2.5},
                "b": {"0": "t", "1": "t", "2": "k"},
            },
        }


@pytest.mark.asyncio
async def test_direct_provisioning_multitsframe_metadata(
    async_test_client: AsyncClient,
) -> None:
    async with async_test_client as client:
        exec_result = await run_single_component(
            (
                "./transformations/components/connectors/"
                "extract-attributes-multitsframe_100_f711106f-3ee1-46a6-a70b-ba12d92fe5be.json"
            ),
            {
                "multitsframe": (
                    '{"__hd_wrapped_data_object__": "DATAFRAME",'
                    ' "__metadata__": {"test": 44},'
                    ' "__data__": {"timestamp": ["2023-01-01T00:00:00+00:00"],'
                    ' "metric": ["mymetric"], "value": [1.7]} }'
                )
            },
            client,
        )

        assert exec_result.output_results_by_output_name["attributes"] == {"test": 44}

        exec_result = await run_single_component(
            (
                "./transformations/components/connectors/"
                "pass-through-multitsframe_100_78ee6b00-9239-4214-b9bf-a093647f33f5.json"
            ),
            {
                "input": (
                    '{"__hd_wrapped_data_object__": "DATAFRAME",'
                    ' "__metadata__": {"test": 44},'
                    ' "__data__": {"timestamp": ["2023-01-01T00:00:00+00:00"],'
                    ' "metric": ["mymetric"], "value": [1.7]} }'
                )
            },
            client,
        )

        assert exec_result.output_results_by_output_name["output"] == {
            "__hd_wrapped_data_object__": "DATAFRAME",
            "__metadata__": {"test": 44},
            "__data__": {
                "metric": {"0": "mymetric"},
                "timestamp": {"0": "2023-01-01T00:00:00.000Z"},
                "value": {"0": 1.7},
            },
        }


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

        assert exec_result.output_results_by_output_name["output"] == ('{"a": 1.5, "b": None}')


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


def division_component_wf_exc_inp_replace(
    imports_and_definitions: str | None = None,
    function_code: str | None = None,
    function_header: str | None = None,
) -> WorkflowExecutionInput:
    division_component_wf_exc_inp = gen_execution_input_from_single_component(
        ("tests/data/components/" "raise-exception_010_c4dbcc42-eaec-4587-a362-ce6567f21d92.json"),
        {"dividend": 1, "divisor": 0},
    )

    if imports_and_definitions is not None:
        division_component_wf_exc_inp.code_modules[
            0
        ].code = division_component_wf_exc_inp.code_modules[0].code.replace(
            "from hdutils import ComponentException",
            imports_and_definitions,
        )

    if function_code is not None:
        division_component_wf_exc_inp.code_modules[
            0
        ].code = division_component_wf_exc_inp.code_modules[0].code.replace(
            "pass",
            function_code,
        )

    if function_header is not None:
        division_component_wf_exc_inp.code_modules[
            0
        ].code = division_component_wf_exc_inp.code_modules[0].code.replace(
            "def main(*, dividend, divisor):", function_header
        )

    return division_component_wf_exc_inp


@pytest.mark.asyncio
class TestSctructuredErrors:
    async def test_raise_missing_wiring_exception(
        self,
        async_test_client: AsyncClient,
    ) -> None:
        wf_exc_input = division_component_wf_exc_inp_replace()
        wf_exc_input.workflow_wiring.input_wirings = []
        async with async_test_client as client:
            with pytest.raises(HTTPException) as exc_info:
                await execute_workflow_execution_input(wf_exc_input, client)

        assert "Workflow Input 'dividend' has no wiring" in str(exc_info.value.detail)
        assert exc_info.value.status_code == 422

    async def test_raise_not_matching_wiring_exception(
        self,
        async_test_client: AsyncClient,
    ) -> None:
        wf_exc_input = division_component_wf_exc_inp_replace()
        wf_exc_input.workflow_wiring.input_wirings.append(
            InputWiring(
                workflow_input_name="result",
                adapter_id=1,
                filters={"value": 0},
            )
        )
        async with async_test_client as client:
            with pytest.raises(HTTPException) as exc_info:
                await execute_workflow_execution_input(wf_exc_input, client)

        assert "Wiring does not match: There is no workflow input" in str(exc_info.value.detail)
        assert exc_info.value.status_code == 422

    async def test_raise_default_exception(
        self,
        async_test_client: AsyncClient,
    ) -> None:
        wf_exc_input = division_component_wf_exc_inp_replace(
            function_header="def main(*, divisor, dividend=asdf):"
        )

        async with async_test_client as client:
            result = await execute_workflow_execution_input(wf_exc_input, client)

        assert result.error is not None
        assert result.error.process_stage == ProcessStage.PARSING_WORKFLOW
        assert result.error.type == "NodeFunctionLoadingError"  # cause: NameError
        assert result.error.error_code is None
        assert (
            result.error.message
            == (  # cause: "name 'asdf' is not defined"
                "Could not load node function "
                "(Code module uuid: c4dbcc42-eaec-4587-a362-ce6567f21d92, "
                "Component uuid: c4dbcc42-eaec-4587-a362-ce6567f21d92, function name: main)"
            )
        )
        assert result.error.extra_information is None
        assert result.error.location is not None
        assert result.error.location.file.endswith("/hetdesrun/runtime/engine/plain/parsing.py")
        assert result.error.location.function_name == "load_func"

    async def test_raise_wf_input_validation_exception(
        self,
        async_test_client: AsyncClient,
    ) -> None:
        with open(
            os.path.join("tests", "data", "workflows", "raise_exception_wf_dto.json"),
            encoding="utf8",
        ) as f:
            loaded_workflow_exe_input = json.load(f)

        wf_exc_input = WorkflowExecutionInput(**loaded_workflow_exe_input)

        async with async_test_client as client:
            result = await execute_workflow_execution_input(wf_exc_input, client)

        assert result.error is not None
        assert result.error.process_stage == ProcessStage.PARSING_WORKFLOW
        # cause of cause type: pydantic.error_wrappers.ValidationError
        assert result.error.type == "WorkflowInputDataValidationError"
        assert result.error.error_code is None
        # cause of cause message:
        # 1 validation error for DynamicyModel\ndividend\n
        #  value is not a valid integer (type=type_error.integer)
        assert result.error.message == (
            "Some default values could not be parsed into the respective workflow input datatypes."
        )
        assert result.error.extra_information is None
        assert result.error.location is not None
        assert result.error.location.file.endswith("/hetdesrun/runtime/engine/plain/parsing.py")
        assert result.error.location.function_name == "recursively_parse_workflow_node"

    async def test_raise_imported_component_exception_with_error_code(
        self,
        async_test_client: AsyncClient,
    ) -> None:
        wf_exc_input = division_component_wf_exc_inp_replace(
            function_code=(
                """if divisor == 0:
                    raise ComponentException(
                        "The divisor must not equal zero!",
                        error_code=404,
                        extra_information={"dividend": dividend}
                    )
                    return {"result": dividend/divisor}
                """
            )
        )

        async with async_test_client as client:
            result = await execute_workflow_execution_input(wf_exc_input, client)

        assert result.error is not None
        assert result.error.process_stage == ProcessStage.EXECUTING_COMPONENT_CODE
        assert result.error.message == "The divisor must not equal zero!"
        assert result.error.extra_information == {"dividend": 1}
        assert result.error.error_code == 404
        assert result.error.type == "ComponentException"
        assert result.error.operator_info is not None
        assert "c4dbcc" in result.error.operator_info.transformation_info.id
        assert result.error.location is not None
        assert result.error.location.file == "COMPONENT CODE"
        assert result.error.location.function_name == "main"
        assert result.error.location.line_number == 28

    async def test_raise_defined_component_exception_with_error_code(
        self,
        async_test_client: AsyncClient,
    ) -> None:
        wf_exc_input = division_component_wf_exc_inp_replace(
            imports_and_definitions=(
                """class ComponentException(Exception):
                    def __init__(self, msg, error_code, extra_information, **kwargs):
                        self.__is_hetida_designer_exception__ = True
                        self.error_code = error_code
                        if extra_information is not None:
                            self.extra_information = extra_information
                        super().__init__(msg, **kwargs)
                """
            ),
            function_code=(
                """if divisor == 0:
                    raise ComponentException(
                        "The divisor must not equal zero!",
                        error_code=404,
                        extra_information={"dividend": dividend}
                    )
                    return {"result": dividend/divisor}
                """
            ),
        )

        async with async_test_client as client:
            result = await execute_workflow_execution_input(wf_exc_input, client)

        assert result.error is not None
        assert result.error.process_stage == ProcessStage.EXECUTING_COMPONENT_CODE
        assert result.error.message == "The divisor must not equal zero!"
        assert result.error.extra_information == {"dividend": 1}
        assert result.error.error_code == 404
        assert result.error.type == "ComponentException"
        assert result.error.operator_info is not None
        assert "c4dbcc" in result.error.operator_info.transformation_info.id
        assert result.error.location is not None
        assert result.error.location.file == "COMPONENT CODE"
        assert result.error.location.function_name == "main"
        assert result.error.location.line_number == 35

    async def test_raise_imported_component_input_validation_exception(
        self,
        async_test_client: AsyncClient,
    ) -> None:
        wf_exc_input = division_component_wf_exc_inp_replace(
            imports_and_definitions=("from hdutils import ComponentInputValidationException"),
            function_code=(
                """if divisor == 0:
                    raise ComponentInputValidationException(
                        "The divisor must not equal zero!",
                        error_code=404,
                        invalid_component_inputs=["divisor"]
                    )
                    return {"result": dividend/divisor}
                """
            ),
        )
        print(wf_exc_input.code_modules[0].code)

        async with async_test_client as client:
            result = await execute_workflow_execution_input(wf_exc_input, client)

        assert result.error is not None
        assert result.error.process_stage == ProcessStage.EXECUTING_COMPONENT_CODE
        assert result.error.message == "The divisor must not equal zero!"
        assert result.error.extra_information == {"invalid_component_inputs": ["divisor"]}
        assert result.error.error_code == 404
        assert result.error.type == "ComponentInputValidationException"
        assert result.error.operator_info is not None
        assert "c4dbcc" in result.error.operator_info.transformation_info.id
        assert result.error.location is not None
        assert result.error.location.file == "COMPONENT CODE"
        assert result.error.location.function_name == "main"
        assert result.error.location.line_number == 28

    async def test_raise_explicit_value_error(
        self,
        async_test_client: AsyncClient,
    ) -> None:
        wf_exc_input = division_component_wf_exc_inp_replace(
            function_code=(
                """if divisor == 0:
                raise ValueError("The divisor must not equal zero!")
                return {"result": dividend/divisor}
                """
            )
        )

        async with async_test_client as client:
            result = await execute_workflow_execution_input(wf_exc_input, client)

        assert result.error is not None
        assert result.error.process_stage == ProcessStage.EXECUTING_COMPONENT_CODE
        assert result.error.type == "ValueError"
        assert result.error.error_code is None
        assert result.error.message == "The divisor must not equal zero!"
        assert result.error.extra_information is None
        assert result.error.operator_info is not None
        assert "c4dbcc" in result.error.operator_info.transformation_info.id
        assert result.error.location is not None
        assert result.error.location.file == "COMPONENT CODE"
        assert result.error.location.function_name == "main"
        assert result.error.location.line_number == 28

    async def test_raise_exception_implicitly(
        self,
        async_test_client: AsyncClient,
    ) -> None:
        wf_exc_input = division_component_wf_exc_inp_replace(
            function_code='return {"result": dividend/divisor}',
        )

        async with async_test_client as client:
            result = await execute_workflow_execution_input(wf_exc_input, client)

        assert result.error is not None
        assert result.error.process_stage == ProcessStage.EXECUTING_COMPONENT_CODE
        assert result.error.type == "ZeroDivisionError"
        assert result.error.error_code is None
        assert result.error.message == "division by zero"
        assert result.error.extra_information is None
        assert result.error.operator_info is not None
        assert "c4dbcc" in result.error.operator_info.transformation_info.id
        assert result.error.location is not None
        assert result.error.location.file == "COMPONENT CODE"
        assert result.error.location.function_name == "main"
        assert result.error.location.line_number == 27

    async def test_raise_no_output_dict_exception(
        self,
        async_test_client: AsyncClient,
    ) -> None:
        wf_exc_input = division_component_wf_exc_inp_replace(
            function_code="return dividend",
        )

        async with async_test_client as client:
            result = await execute_workflow_execution_input(wf_exc_input, client)

        assert result.error is not None
        assert result.error.process_stage == ProcessStage.EXECUTING_COMPONENT_CODE
        assert result.error.type == "RuntimeExecutionError"
        assert result.error.error_code is None
        assert result.error.message == "Component did not return an output dict."
        assert result.error.extra_information is None
        assert result.error.operator_info is not None
        assert "c4dbcc" in result.error.operator_info.transformation_info.id

        assert result.error.location.file.endswith("/hetdesrun/runtime/engine/plain/workflow.py")
        assert result.error.location.function_name == "_run_comp_func"

    async def test_raise_missing_outputs_exception(
        self,
        async_test_client: AsyncClient,
    ) -> None:
        wf_exc_input = division_component_wf_exc_inp_replace()

        async with async_test_client as client:
            result = await execute_workflow_execution_input(wf_exc_input, client)

        assert result.error is not None
        assert result.error.process_stage == ProcessStage.EXECUTING_COMPONENT_CODE
        assert result.error.type == "MissingOutputException"
        assert result.error.error_code is None
        assert (
            result.error.message == "Declared output 'result' not contained in returned dictionary."
        )
        assert result.error.extra_information is None
        assert result.error.operator_info is not None
        assert "c4dbcc" in result.error.operator_info.transformation_info.id
        assert result.error.location.file.endswith("/hetdesrun/runtime/engine/plain/workflow.py")
        assert result.error.location.function_name == "result"

    async def test_raise_parsing_metadata_output_exception(
        self,
        async_test_client: AsyncClient,
    ) -> None:
        wf_exc_input = division_component_wf_exc_inp_replace(
            function_code='return {"result": "string instead of boolean"}',
        )
        wf_exc_input.workflow_wiring.output_wirings = [
            OutputWiring(
                workflow_output_name="result",
                adapter_id="demo-adapter-python",
                ref_id="root.plantA.picklingUnit.influx.anomaly_score",
                ref_id_type="SINK",
                ref_key="Overshooting Allowed",
                type="metadata(boolean)",
                filters={},
            )
        ]

        async with async_test_client as client:
            result = await execute_workflow_execution_input(wf_exc_input, client)

        assert result.error is not None
        assert result.error.process_stage == ProcessStage.SENDING_DATA_TO_ADAPTERS
        assert result.error.type == "AdapterOutputDataError"
        assert result.error.error_code is None
        assert result.error.message == (
            "Received metadatum value 'string instead of boolean' cannot be parsed "
            "as the declared data type BOOLEAN."
        )
        assert result.error.extra_information is None
        assert result.error.operator_info is None
        assert result.error.location is not None
        assert result.error.location.file.endswith(
            "/hetdesrun/adapters/generic_rest/send_metadata.py"
        )
        assert result.error.location.function_name == "send_single_metadatum_to_adapter"

    async def test_raise_parsing_series_output_exception(
        self,
        async_test_client: AsyncClient,
    ) -> None:
        wf_exc_input = division_component_wf_exc_inp_replace(
            function_code='return {"result": "string instead of series"}',
        )
        wf_exc_input.workflow_wiring.output_wirings = [
            OutputWiring(
                adapter_id="demo-adapter-python",
                filters={"frequency": ""},
                ref_id="root.plantA.picklingUnit.influx.anomaly_score",
                ref_id_type="SINK",
                ref_key=None,
                type="timeseries(float)",
                workflow_output_name="result",
            )
        ]

        async with async_test_client as client:
            result = await execute_workflow_execution_input(wf_exc_input, client)

        assert result.error is not None
        assert result.error.process_stage == ProcessStage.SENDING_DATA_TO_ADAPTERS
        assert result.error.type == "AdapterOutputDataError"
        assert result.error.error_code is None
        assert result.error.message == (
            "Did not receive Pandas Series as expected from workflow output. "
            "Got <class 'str'> instead."
        )
        assert result.error.extra_information is None
        assert result.error.operator_info is None
        assert result.error.location is not None
        assert result.error.location.file.endswith(
            "/hetdesrun/adapters/generic_rest/send_ts_data.py"
        )
        assert result.error.location.function_name == "ts_to_list_of_dicts"

    async def test_raise_json_encoding_exception(
        self,
        async_test_client: AsyncClient,
    ) -> None:
        wf_exc_input = division_component_wf_exc_inp_replace(
            function_code='return {"result": str}',
        )

        async with async_test_client as client:
            result = await execute_workflow_execution_input(wf_exc_input, client)

        assert result.error is not None
        assert result.error.process_stage == ProcessStage.ENCODING_RESULTS_TO_JSON
        assert result.error.type == "ValueError"
        assert result.error.error_code is None
        assert result.error.message == (
            '[TypeError("'
            "'builtin_function_or_method'"
            ' object is not iterable"), '
            "TypeError('vars() argument must have __dict__ attribute')]"
        )
        assert result.error.extra_information is None
        assert result.error.location is not None
        assert result.error.location.file.endswith("fastapi/encoders.py")
        assert result.error.location.function_name == "jsonable_encoder"


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
            os.path.join("tests", "data", "timeseries_dataframe_wf_execution_input.json"),
            encoding="utf8",
        ) as f:
            loaded_workflow_exe_input = json.load(f)
        response_status_code, response_json = await run_workflow_with_client(
            loaded_workflow_exe_input, client
        )

        assert response_status_code == 200
        assert response_json["result"] == "ok"
        assert response_json["output_results_by_output_name"]["multitsframe"]["__data__"] == {
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
    assert response_json["output_results_by_output_name"]["intercept"] == 2.8778442676301292
    assert (
        response_json["output_results_by_output_name"]["limit_violation_timestamp"]
        == "2020-06-25T16:33:23.934348+00:00"
    )
    assert response_json["output_results_by_output_name"]["slope"] == [-3.700034733861136e-7]

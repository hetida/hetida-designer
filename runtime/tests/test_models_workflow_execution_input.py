from copy import deepcopy

import pytest

from hetdesrun.models.run import WorkflowExecutionInput


def test_workflow_execution_input_accepted(input_json_with_wiring) -> None:
    WorkflowExecutionInput(**input_json_with_wiring)


def test_workflow_execution_input_validator_components_unique(
    input_json_with_wiring,
) -> None:
    input_json_with_not_unique_components = deepcopy(input_json_with_wiring)
    input_json_with_not_unique_components["components"].append(
        input_json_with_not_unique_components["components"][0]
    )
    with pytest.raises(ValueError, match="Components not unique"):
        WorkflowExecutionInput(**input_json_with_not_unique_components)


def test_workflow_execution_input_validator_code_modules_unique(
    input_json_with_wiring,
) -> None:
    input_json_with_not_unique_code_modules = deepcopy(input_json_with_wiring)
    input_json_with_not_unique_code_modules["code_modules"].append(
        input_json_with_not_unique_code_modules["code_modules"][0]
    )
    with pytest.raises(ValueError, match="Code Modules not unique"):
        WorkflowExecutionInput(**input_json_with_not_unique_code_modules)


def test_workflow_execution_input_validator_check_wiring_complete(
    input_json_with_wiring_with_input,
) -> None:
    input_json_with_optional_input_wiring = deepcopy(input_json_with_wiring_with_input)
    input_json_with_optional_input_wiring["workflow"]["inputs"][0]["default"] = True
    WorkflowExecutionInput(**input_json_with_optional_input_wiring)

    input_json_without_optional_input_wiring = deepcopy(input_json_with_wiring_with_input)
    input_json_without_optional_input_wiring["workflow"]["inputs"][0]["default"] = True
    del input_json_without_optional_input_wiring["workflow_wiring"]["input_wirings"][0]
    WorkflowExecutionInput(**input_json_without_optional_input_wiring)

    input_json_with_incomplete_input_wiring = deepcopy(input_json_with_wiring_with_input)
    del input_json_with_incomplete_input_wiring["workflow_wiring"]["input_wirings"][0]
    with pytest.raises(ValueError, match="Wiring Incomplete"):
        WorkflowExecutionInput(**input_json_with_incomplete_input_wiring)

    input_json_with_too_many_input_wirings = deepcopy(input_json_with_wiring_with_input)
    input_json_with_too_many_input_wirings["workflow_wiring"]["input_wirings"].append(
        {
            "workflow_input_name": "another_inp",
            "adapter_id": 1,
            "ref_id": "TEST-ID",
            "filters": {"value": "23"},
        }
    )
    with pytest.raises(ValueError, match="Wiring does not match"):
        WorkflowExecutionInput(**input_json_with_too_many_input_wirings)

    input_json_with_too_many_output_wirings = deepcopy(input_json_with_wiring_with_input)
    input_json_with_too_many_output_wirings["workflow_wiring"]["output_wirings"].append(
        {
            "workflow_output_name": "another_outp",
            "adapter_id": 1,
            "ref_id": "TEST-ID",
        }
    )
    with pytest.raises(ValueError, match="Wiring does not match"):
        WorkflowExecutionInput(**input_json_with_too_many_output_wirings)

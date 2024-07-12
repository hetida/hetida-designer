from copy import deepcopy
from uuid import UUID

import pytest

from hetdesrun.models.component import ComponentInput, ComponentOutput
from hetdesrun.persistence.models.io import (
    InputType,
    IOInterface,
    OperatorInput,
    OperatorOutput,
    TransformationInput,
    TransformationOutput,
    WorkflowContentConstantInput,
    WorkflowContentDynamicInput,
    WorkflowContentOutput,
    WorkflowInput,
    WorkflowOutput,
)

required_trafo_input = {
    "data_type": "SERIES",
    "id": "1c3224e0-90e6-4d03-9160-3a9417c27841",
    "name": "y_vals",
    "type": "REQUIRED",
    "value": None,
}
optional_trafo_input = {
    "data_type": "INT",
    "id": "b817a8f6-764d-4003-96c4-b8ba52981fb1",
    "name": "n_grid",
    "type": "OPTIONAL",
    "value": None,
}
trafo_output = {
    "data_type": "PLOTLYJSON",
    "id": "5dcdf141-590f-42d6-86bd-460af86147a7",
    "name": "contour_plot",
}
required_workflow_input = {
    "connector_id": "5336c0a5-97ac-d436-ae5f-ee75fa8c8b40",
    "connector_name": "input",
    "data_type": "SERIES",
    "id": "1c3224e0-90e6-4d03-9160-3a9417c27841",
    "name": "y_vals",
    "operator_id": "1ecddb98-6ae1-48b0-b125-20d3b4e3118c",
    "operator_name": "Name Series (2)",
    "position": {"x": -50, "y": 370},
    "type": "REQUIRED",
    "value": None,
}
optional_workflow_input = {
    "connector_id": "64245bba-7e81-ef0a-941d-2f9b5b43d044",
    "connector_name": "n",
    "data_type": "INT",
    "id": "b817a8f6-764d-4003-96c4-b8ba52981fb1",
    "name": "n_grid",
    "operator_id": "74608f8a-d973-4add-9764-ad3348b3bb57",
    "operator_name": "2D Grid Generator",
    "position": {"x": -60, "y": 90},
    "type": "OPTIONAL",
    "value": 30,
}
constant_workflow_input = {
    "connector_id": "44d0fd6a-4f72-3ec1-d5dc-4f8df7029652",
    "connector_name": "name",
    "data_type": "STRING",
    "id": "088d81cf-caa3-4fd4-ab7a-e1538de3b559",
    "operator_id": "1ecddb98-6ae1-48b0-b125-20d3b4e3118c",
    "operator_name": "Name Series (2)",
    "position": {"x": -200, "y": 0},
    "value": "y",
}
workflow_output = {
    "connector_id": "53dff70b-364f-e5b7-fbb4-c293a5d2f339",
    "connector_name": "contour_plot",
    "data_type": "PLOTLYJSON",
    "id": "5dcdf141-590f-42d6-86bd-460af86147a7",
    "name": "contour_plot",
    "operator_id": "e362967a-fa2d-4d7c-8ef9-e58eceb45e2b",
    "operator_name": "Contour Plot",
    "position": {"x": 2010, "y": -100},
}
exposed_operator_input_connected_to_optional_workflow_input = {
    "data_type": "INT",
    "id": "64245bba-7e81-ef0a-941d-2f9b5b43d044",
    "name": "n",
    "type": "REQUIRED",
    "value": None,
    "position": {"x": 0, "y": 0},
    "exposed": True,
}
exposed_operator_input_connected_to_required_workflow_input = {
    "data_type": "SERIES",
    "id": "5336c0a5-97ac-d436-ae5f-ee75fa8c8b40",
    "name": "input",
    "type": "OPTIONAL",
    "value": None,
    "position": {"x": 0, "y": 0},
    "exposed": True,
}
exposed_operator_input_connected_to_constant_workflow_input = {
    "data_type": "STRING",
    "id": "44d0fd6a-4f72-3ec1-d5dc-4f8df7029652",
    "name": "name",
    "type": "OPTIONAL",
    "value": 23,
    "position": {"x": 0, "y": 0},
    "exposed": True,
}
unexposed_operator_input = {
    "data_type": "INT",
    "id": "9861c5a4-1e37-54af-70be-f4e7b81d1f64",
    "name": "n_estimators",
    "type": "OPTIONAL",
    "value": 100,
    "position": {"x": 0, "y": 0},
    "exposed": False,
}
operator_output = {
    "data_type": "PLOTLYJSON",
    "id": "53dff70b-364f-e5b7-fbb4-c293a5d2f339",
    "name": "contour_plot",
    "position": {"x": 0, "y": 0},
}


def test_transformation_output_accepted() -> None:
    TransformationOutput(**trafo_output)


def test_transformation_io_validator_name_python_identifier_identifies_keyword_name() -> None:
    trafo_output_with_keyword_name = deepcopy(trafo_output)
    trafo_output_with_keyword_name["name"] = "pass"

    with pytest.raises(ValueError) as exc:  # noqa: PT011
        TransformationOutput(**trafo_output_with_keyword_name)

    assert "not a valid Python identifier" in str(exc.value)


def test_transformation_io_validator_name_python_identifier_identifies_invalid_name() -> None:
    trafo_output_with_invalid_name = deepcopy(trafo_output)
    trafo_output_with_invalid_name["name"] = "1name"

    with pytest.raises(ValueError) as exc:  # noqa: PT011
        TransformationOutput(**trafo_output_with_invalid_name)

    assert "not a valid Python identifier" in str(exc.value)


def test_transformation_output_to_component_output() -> None:
    component_output = TransformationOutput(**trafo_output).to_component_output()
    assert component_output == ComponentOutput(
        id=trafo_output["id"], type=trafo_output["data_type"], name=trafo_output["name"]
    )


def test_transformation_input_accepted() -> None:
    TransformationInput(**required_trafo_input)
    TransformationInput(**optional_trafo_input)


def test_transformation_input_validator_value_only_set_for_optional_input() -> None:
    required_trafo_input_with_value = deepcopy(required_trafo_input)
    required_trafo_input_with_value["value"] = "test"

    with pytest.raises(ValueError, match=r"value.* must not be set"):
        TransformationInput(**required_trafo_input_with_value)


def test_transformation_input_to_component_input() -> None:
    required_component_input = TransformationInput(**required_trafo_input).to_component_input()
    assert required_component_input == ComponentInput(
        id=required_trafo_input["id"],
        type=required_trafo_input["data_type"],
        name=required_trafo_input["name"],
    )

    optional_component_input = TransformationInput(**optional_trafo_input).to_component_input()
    assert optional_component_input == ComponentInput(
        id=optional_trafo_input["id"],
        type=optional_trafo_input["data_type"],
        name=optional_trafo_input["name"],
        default=True,
    )


def test_io_interface_accepted() -> None:
    IOInterface(inputs=[required_trafo_input, optional_trafo_input], outputs=[trafo_output])


def test_io_interface_validator_io_names_unique() -> None:
    with pytest.raises(ValueError, match=r"duplicates.* not allowed"):
        IOInterface(inputs=[required_trafo_input], outputs=[trafo_output, trafo_output])

    with pytest.raises(ValueError, match=r"duplicates.* not allowed"):
        IOInterface(inputs=[required_trafo_input, required_trafo_input], outputs=[trafo_output])


def test_operator_output_accepted() -> None:
    OperatorOutput(**operator_output)


def test_operator_output_from_transformation_output() -> None:
    operator_output_from_transformation_output = OperatorOutput.from_transformation_output(
        transformation_output=TransformationOutput(**trafo_output),
        pos_x=23,
        pos_y=42,
    )

    assert str(operator_output_from_transformation_output.id) == trafo_output["id"]
    assert operator_output_from_transformation_output.name == trafo_output["name"]
    assert operator_output_from_transformation_output.data_type == trafo_output["data_type"]
    assert operator_output_from_transformation_output.position.x == 23
    assert operator_output_from_transformation_output.position.y == 42


def test_operator_input_accepted() -> None:
    OperatorInput(**exposed_operator_input_connected_to_required_workflow_input)
    OperatorInput(**exposed_operator_input_connected_to_optional_workflow_input)
    OperatorInput(**exposed_operator_input_connected_to_constant_workflow_input)
    OperatorInput(**unexposed_operator_input)


def test_operator_input_validator_required_inputs_exposed() -> None:
    operator_input_required_not_exposed_json = deepcopy(
        exposed_operator_input_connected_to_optional_workflow_input
    )
    operator_input_required_not_exposed_json["exposed"] = False
    operator_input_required_not_exposed_object = OperatorInput(
        **operator_input_required_not_exposed_json
    )
    assert operator_input_required_not_exposed_object.exposed is True

    unexposed_operator_input_object = OperatorInput(**unexposed_operator_input)
    assert unexposed_operator_input_object.exposed is False

    operator_input_type_and_exposed_not_set_json = deepcopy(
        exposed_operator_input_connected_to_optional_workflow_input
    )
    del operator_input_type_and_exposed_not_set_json["type"]
    del operator_input_type_and_exposed_not_set_json["exposed"]
    operator_input_type_and_exposed_not_set = OperatorInput(
        **operator_input_type_and_exposed_not_set_json
    )
    assert operator_input_type_and_exposed_not_set.type == InputType.REQUIRED
    assert operator_input_type_and_exposed_not_set.exposed is True

    operator_input_type_optional_exposed_not_set_json = deepcopy(
        exposed_operator_input_connected_to_optional_workflow_input
    )
    operator_input_type_optional_exposed_not_set_json["type"] = "OPTIONAL"
    del operator_input_type_optional_exposed_not_set_json["exposed"]
    operator_input_type_optional_exposed_not_set = OperatorInput(
        **operator_input_type_optional_exposed_not_set_json
    )
    assert operator_input_type_optional_exposed_not_set.type == InputType.OPTIONAL
    assert operator_input_type_optional_exposed_not_set.exposed is False


def test_operator_input_from_transformation_input() -> None:
    operator_input_connector_from_required_input = OperatorInput.from_transformation_input(
        input=TransformationInput(**required_trafo_input), pos_x=17, pos_y=19
    )
    assert str(operator_input_connector_from_required_input.id) == required_trafo_input["id"]
    assert operator_input_connector_from_required_input.name == required_trafo_input["name"]
    assert (
        operator_input_connector_from_required_input.data_type == required_trafo_input["data_type"]
    )
    assert operator_input_connector_from_required_input.type == required_trafo_input["type"]
    assert operator_input_connector_from_required_input.value == required_trafo_input["value"]
    assert operator_input_connector_from_required_input.position.x == 17
    assert operator_input_connector_from_required_input.position.y == 19

    operator_input_connector_from_optional_input = OperatorInput.from_transformation_input(
        input=TransformationInput(**optional_trafo_input), pos_x=19, pos_y=23
    )
    assert str(operator_input_connector_from_optional_input.id) == optional_trafo_input["id"]
    assert operator_input_connector_from_optional_input.name == optional_trafo_input["name"]
    assert (
        operator_input_connector_from_optional_input.data_type == optional_trafo_input["data_type"]
    )
    assert operator_input_connector_from_optional_input.type == optional_trafo_input["type"]
    assert operator_input_connector_from_optional_input.value == optional_trafo_input["value"]
    assert operator_input_connector_from_optional_input.position.x == 19
    assert operator_input_connector_from_optional_input.position.y == 23


def test_workflow_content_output_accepted() -> None:
    WorkflowContentOutput(**workflow_output)


def test_workflow_content_output_to_transformation_output() -> None:
    trafo_output_from_workflow_output = WorkflowContentOutput(
        **workflow_output
    ).to_transformation_output()
    assert trafo_output_from_workflow_output == TransformationOutput(**trafo_output)


def test_workflow_content_output_to_workflow_output() -> None:
    workflow_node_output: WorkflowOutput = WorkflowContentOutput(
        **workflow_output
    ).to_workflow_output()

    assert str(workflow_node_output.id) == workflow_output["id"]
    assert workflow_node_output.name == workflow_output["name"]
    assert workflow_node_output.type == workflow_output["data_type"]
    assert workflow_node_output.id_of_sub_node == workflow_output["operator_id"]
    assert workflow_node_output.name_in_subnode == workflow_output["connector_name"]


def test_workflow_content_output_from_operator_output() -> None:
    workflow_output_from_operator_output = WorkflowContentOutput.from_operator_output(
        operator_output=OperatorOutput(**operator_output),
        operator_id=UUID(workflow_output["operator_id"]),
        operator_name=workflow_output["operator_name"],
    )

    assert workflow_output_from_operator_output.id != operator_output["id"]
    assert workflow_output_from_operator_output.name == operator_output["name"]
    assert workflow_output_from_operator_output.data_type == operator_output["data_type"]
    assert str(workflow_output_from_operator_output.operator_id) == workflow_output["operator_id"]
    assert workflow_output_from_operator_output.operator_name == workflow_output["operator_name"]
    assert str(workflow_output_from_operator_output.connector_id) == operator_output["id"]
    assert workflow_output_from_operator_output.connector_name == operator_output["name"]


def test_workflow_content_dynamic_input_accepted() -> None:
    WorkflowContentDynamicInput(**required_workflow_input)
    WorkflowContentDynamicInput(**optional_workflow_input)


def test_workflow_content_dyanmic_input_to_transformation_input() -> None:
    required_trafo_input_from_workflow_input = WorkflowContentDynamicInput(
        **required_workflow_input
    ).to_transformation_input()
    assert required_trafo_input_from_workflow_input == TransformationInput(**required_trafo_input)


def test_workflow_content_dynamic_input_to_workflow_input() -> None:
    workflow_node_input: WorkflowInput = WorkflowContentDynamicInput(
        **required_workflow_input
    ).to_workflow_input()

    assert str(workflow_node_input.id) == required_workflow_input["id"]
    assert workflow_node_input.name == required_workflow_input["name"]
    assert workflow_node_input.type == required_workflow_input["data_type"]
    assert workflow_node_input.id_of_sub_node == required_workflow_input["operator_id"]
    assert workflow_node_input.name_in_subnode == required_workflow_input["connector_name"]


def test_workflow_content_dynamic_input_connector_from_operator_input() -> None:
    required_workflow_input_from_operator_input = WorkflowContentDynamicInput.from_operator_input(
        operator_input=OperatorInput(**exposed_operator_input_connected_to_required_workflow_input),
        operator_id=UUID(required_workflow_input["operator_id"]),
        operator_name=required_workflow_input["operator_name"],
    )

    assert (
        required_workflow_input_from_operator_input.id
        != exposed_operator_input_connected_to_required_workflow_input["id"]
    )
    assert (
        required_workflow_input_from_operator_input.name
        == exposed_operator_input_connected_to_required_workflow_input["name"]
    )
    assert (
        required_workflow_input_from_operator_input.data_type
        == exposed_operator_input_connected_to_required_workflow_input["data_type"]
    )
    assert (
        str(required_workflow_input_from_operator_input.operator_id)
        == required_workflow_input["operator_id"]
    )
    assert (
        required_workflow_input_from_operator_input.operator_name
        == required_workflow_input["operator_name"]
    )
    assert (
        str(required_workflow_input_from_operator_input.connector_id)
        == exposed_operator_input_connected_to_required_workflow_input["id"]
    )
    assert (
        required_workflow_input_from_operator_input.connector_name
        == exposed_operator_input_connected_to_required_workflow_input["name"]
    )


def test_workflow_content_constant_input_accepted() -> None:
    WorkflowContentConstantInput(**constant_workflow_input)


def test_workflow_content_constant_input_validator_name_none() -> None:
    constant_workflow_input_with_name = deepcopy(constant_workflow_input)
    constant_workflow_input_with_name["name"] = "test"

    with pytest.raises(ValueError, match=r"must have.* empty string"):
        WorkflowContentConstantInput(**constant_workflow_input_with_name)


def test_workflow_content_constant_input_to_workflow_input() -> None:
    workflow_node_input: WorkflowInput = WorkflowContentConstantInput(
        **constant_workflow_input
    ).to_workflow_input()

    assert str(workflow_node_input.id) == constant_workflow_input["id"]
    assert workflow_node_input.name is None
    assert workflow_node_input.type == constant_workflow_input["data_type"]
    assert workflow_node_input.id_of_sub_node == constant_workflow_input["operator_id"]
    assert workflow_node_input.name_in_subnode == constant_workflow_input["connector_name"]

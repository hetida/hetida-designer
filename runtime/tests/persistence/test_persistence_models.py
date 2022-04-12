from copy import deepcopy
from collections import namedtuple
from uuid import uuid4

import pytest

from pydantic import ValidationError

from hetdesrun.utils import State, Type, get_uuid_from_seed

from hetdesrun.backend.models.component import ComponentRevisionFrontendDto
from hetdesrun.backend.execution import nested_nodes

from hetdesrun.persistence.models.io import IOInterface, IOConnector
from hetdesrun.persistence.models.workflow import WorkflowContent
from hetdesrun.persistence.models.transformation import TransformationRevision

from hetdesrun.models.wiring import WorkflowWiring

from hetdesrun.exportimport.importing import load_json


tr_json_valid_released_example = load_json(
    "./transformations/workflows/examples/iso-forest-example_100_67c14cf2-cd4e-410e-9aca-6664273ccc3f.json"
)

valid_component_dto_dict = {
    "category": "Arithmetic",
    "code": "",
    "description": "Calculates the modulo to some given b",
    "groupId": "ebb5b2d1-7c25-94dd-ca81-6a9e5b21bc2f",
    "id": "ebb5b2d1-7c25-94dd-ca81-6a9e5b21bc2f",
    "inputs": [
        {
            "id": "1aa579e3-e568-326c-0768-72c725844828",
            "name": "a",
            "posX": 0,
            "posY": 0,
            "type": "ANY",
        },
        {
            "id": "6198074e-18fa-0ba1-13a7-8d77b7f2c8f3",
            "name": "b",
            "posX": 0,
            "posY": 0,
            "type": "INT",
        },
    ],
    "name": "Modulo",
    "outputs": [
        {
            "id": "f309d0e5-6f20-2edb-c7be-13f84882af93",
            "name": "modulo",
            "posX": 0,
            "posY": 0,
            "type": "ANY",
        }
    ],
    "state": "RELEASED",
    "tag": "1.0.0",
    "type": "COMPONENT",
    "wirings": [],
}


def test_tr_validators_accept_valid_released_tr():
    TransformationRevision(**tr_json_valid_released_example)


def test_tr_validator_content_type_correct():
    id = get_uuid_from_seed("test")

    combi = namedtuple("combi", "type content")
    incorrect_combis = (
        combi(type=Type.WORKFLOW, content="test"),
        combi(type=Type.COMPONENT, content=WorkflowContent()),
    )

    correct_combis = (
        combi(type=Type.WORKFLOW, content=WorkflowContent()),
        combi(type=Type.COMPONENT, content="test"),
    )

    for combi in incorrect_combis:
        with pytest.raises(ValidationError):
            TransformationRevision(
                id=id,
                revision_group_id=id,
                name="Test",
                description="Test description",
                version_tag="1.0.0",
                category="Test category",
                state=State.DRAFT,
                type=combi.type,
                content=combi.content,
                io_interface=IOInterface(),
                test_wiring=WorkflowWiring(),
                documentation="",
            )
    for combi in correct_combis:
        # no validation errors
        TransformationRevision(
            id=id,
            revision_group_id=id,
            name="Test",
            description="Test description",
            version_tag="1.0.0",
            category="Test category",
            state=State.DRAFT,
            type=combi.type,
            content=combi.content,
            io_interface=IOInterface(),
            test_wiring=WorkflowWiring(),
            documentation="",
        )


def test_tr_validator_version_tag_not_latest():
    id = get_uuid_from_seed("test")
    with pytest.raises(ValidationError):
        TransformationRevision(
            id=id,
            revision_group_id=id,
            name="Test",
            description="Test description",
            version_tag="latest",
            category="Test category",
            state=State.DRAFT,
            type=Type.COMPONENT,
            content="test",
            io_interface=IOInterface(),
            test_wiring=WorkflowWiring(),
            documentation="",
        )

def test_tr_nonemptyvalidstr_regex_validator_not_whitelisted_character():
    id = get_uuid_from_seed("test")
    with pytest.raises(ValidationError):
        TransformationRevision(
            id=id,
            revision_group_id=id,
            name="+",
            description="Test description",
            version_tag="1.0.0",
            category="Test category",
            state=State.DRAFT,
            type=Type.COMPONENT,
            content="test",
            io_interface=IOInterface(),
            test_wiring=WorkflowWiring(),
            documentation="",
        )

def test_tr_validstr_regex_validator_empty():
    id = get_uuid_from_seed("test")
    TransformationRevision(
        id=id,
        revision_group_id=id,
        name="Test",
        description="",
        version_tag="1.0.0",
        category="Test category",
        state=State.DRAFT,
        type=Type.COMPONENT,
        content="test",
        io_interface=IOInterface(),
        test_wiring=WorkflowWiring(),
        documentation="",
    )

def test_tr_nonemptyvalidstr_regex_validator_empty():
    id = get_uuid_from_seed("test")
    with pytest.raises(ValidationError):
        TransformationRevision(
            id=id,
            revision_group_id=id,
            name="",
            description="Test description",
            version_tag="1.0.0",
            category="Test category",
            state=State.DRAFT,
            type=Type.COMPONENT,
            content="test",
            io_interface=IOInterface(),
            test_wiring=WorkflowWiring(),
            documentation="",
        )

def test_tr_nonemptyvalidstr_validator_max_characters():
    id = get_uuid_from_seed("test")
    with pytest.raises(ValidationError):
        TransformationRevision(
            id=id,
            revision_group_id=id,
            name="Name Name Name Name Name Name Name Name Name Name Name Name Name",
            description="Test description",
            version_tag="1.0.0",
            category="Test category",
            state=State.DRAFT,
            type=Type.COMPONENT,
            content="test",
            io_interface=IOInterface(),
            test_wiring=WorkflowWiring(),
            documentation="",
        )

def test_tr_shortnonemptyvalidstr_validator_max_characters():
    id = get_uuid_from_seed("test")
    with pytest.raises(ValidationError):
        TransformationRevision(
            id=id,
            revision_group_id=id,
            name="Name",
            description="Test description",
            version_tag="1.0.0.0.0.0.0.0.0.0.0",
            category="Test category",
            state=State.DRAFT,
            type=Type.COMPONENT,
            content="test",
            io_interface=IOInterface(),
            test_wiring=WorkflowWiring(),
            documentation="",
        )

def test_tr_nonemptyvalidstr_regex_validator_fancy_characters():
    id = get_uuid_from_seed("test")
    TransformationRevision(
        id=id,
        revision_group_id=id,
        name="bößä",
        description="中文, español, Çok teşekkürler",
        version_tag="(-_-) /  =.=",
        category="ไทย",
        state=State.DRAFT,
        type=Type.COMPONENT,
        content="test",
        io_interface=IOInterface(),
        test_wiring=WorkflowWiring(),
        documentation="",
    )

def test_tr_validator_io_interface_fits_to_content():
    tr_json_empty_io_interface = deepcopy(tr_json_valid_released_example)
    tr_json_empty_io_interface["io_interface"]["inputs"] = []
    tr_json_empty_io_interface["io_interface"]["outputs"] = []
    tr_generated_io_interface = TransformationRevision(**tr_json_empty_io_interface)

    assert len(tr_generated_io_interface.content.inputs) == len(
        tr_json_valid_released_example["io_interface"]["inputs"]
    )


def test_wrap_component_in_tr_workflow():
    component_dto = ComponentRevisionFrontendDto(**valid_component_dto_dict)
    tr_component = component_dto.to_transformation_revision()

    tr_workflow = tr_component.wrap_component_in_tr_workflow()

    assert valid_component_dto_dict["name"] == tr_workflow.name
    assert valid_component_dto_dict["category"] == tr_workflow.category
    assert valid_component_dto_dict["tag"] == tr_workflow.version_tag
    assert valid_component_dto_dict["state"] == tr_workflow.state
    assert Type.WORKFLOW == tr_workflow.type
    assert 1 == len(tr_workflow.content.operators)
    assert valid_component_dto_dict["id"] == str(
        tr_workflow.content.operators[0].transformation_id
    )
    assert len(valid_component_dto_dict["inputs"]) == len(
        tr_workflow.content.operators[0].inputs
    )
    assert len(valid_component_dto_dict["outputs"]) == len(
        tr_workflow.content.operators[0].outputs
    )
    assert len(tr_component.io_interface.inputs) == len(tr_workflow.content.inputs)
    assert len(tr_component.io_interface.outputs) == len(tr_workflow.content.outputs)

    assert len(tr_component.io_interface.inputs) == len(tr_workflow.io_interface.inputs)
    assert len(tr_component.io_interface.outputs) == len(
        tr_workflow.io_interface.outputs
    )


def test_to_workflow_node():
    component_dto = ComponentRevisionFrontendDto(**valid_component_dto_dict)
    tr_component = component_dto.to_transformation_revision()
    tr_workflow = tr_component.wrap_component_in_tr_workflow()
    nested_transformations = {tr_workflow.content.operators[0].id: tr_component}

    workflow_node = tr_workflow.to_workflow_node(
        uuid4(), nested_nodes(tr_workflow, nested_transformations)
    )

    assert len(workflow_node.inputs) == len(valid_component_dto_dict["inputs"])
    assert len(workflow_node.outputs) == len(valid_component_dto_dict["outputs"])
    assert len(workflow_node.sub_nodes) == 1
    assert len(workflow_node.connections) == 0
    assert workflow_node.name == valid_component_dto_dict["name"]

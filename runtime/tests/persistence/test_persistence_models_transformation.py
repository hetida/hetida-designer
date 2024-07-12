import json
import os
from collections import namedtuple
from copy import deepcopy
from uuid import uuid4

import pytest
from pydantic import ValidationError

from hetdesrun.backend.execution import nested_nodes
from hetdesrun.models.wiring import WorkflowWiring
from hetdesrun.persistence.models.io import IOInterface
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.persistence.models.workflow import WorkflowContent
from hetdesrun.trafoutils.io.load import load_json
from hetdesrun.utils import State, Type, get_uuid_from_seed

tr_json_valid_released_example = load_json(
    "./transformations/workflows/examples/iso-forest-example_100_67c14cf2-cd4e-410e-9aca-6664273ccc3f.json"
)

valid_component_tr_dict = {
    "category": "Arithmetic",
    "content": "",
    "description": "Calculates the modulo to some given b",
    "revision_group_id": "ebb5b2d1-7c25-94dd-ca81-6a9e5b21bc2f",
    "id": "ebb5b2d1-7c25-94dd-ca81-6a9e5b21bc2f",
    "io_interface": {
        "inputs": [
            {
                "id": "1aa579e3-e568-326c-0768-72c725844828",
                "name": "a",
                "data_type": "ANY",
            },
            {
                "id": "6198074e-18fa-0ba1-13a7-8d77b7f2c8f3",
                "name": "b",
                "data_type": "INT",
            },
        ],
        "outputs": [
            {
                "id": "f309d0e5-6f20-2edb-c7be-13f84882af93",
                "name": "modulo",
                "data_type": "ANY",
            }
        ],
    },
    "name": "Modulo",
    "released_timestamp": "2022-02-09T17:33:29.361040+00:00",
    "state": "RELEASED",
    "version_tag": "1.0.0",
    "type": "COMPONENT",
    "test_wiring": {"input_wirings": [], "output_wirings": []},
}


def test_tr_validators_accept_valid_released_tr():
    TransformationRevision(**tr_json_valid_released_example)


def test_tr_validator_content_type_correct():
    id_ = get_uuid_from_seed("test")

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
                id=id_,
                revision_group_id=id_,
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
            id=id_,
            revision_group_id=id_,
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
    id_ = get_uuid_from_seed("test")
    with pytest.raises(ValidationError):
        TransformationRevision(
            id=id_,
            revision_group_id=id_,
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
    id_ = get_uuid_from_seed("test")
    with pytest.raises(ValidationError):
        TransformationRevision(
            id=id_,
            revision_group_id=id_,
            name="'",
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
    id_ = get_uuid_from_seed("test")
    TransformationRevision(
        id=id_,
        revision_group_id=id_,
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
    id_ = get_uuid_from_seed("test")
    with pytest.raises(ValidationError):
        TransformationRevision(
            id=id_,
            revision_group_id=id_,
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
    id_ = get_uuid_from_seed("test")
    with pytest.raises(ValidationError):
        TransformationRevision(
            id=id_,
            revision_group_id=id_,
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
    id_ = get_uuid_from_seed("test")
    with pytest.raises(ValidationError):
        TransformationRevision(
            id=id_,
            revision_group_id=id_,
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
    id_ = get_uuid_from_seed("test")
    TransformationRevision(
        id=id_,
        revision_group_id=id_,
        name="bößä",
        description="中文, español, Çok teşekkürler",
        version_tag="(-_-) /  =.= & +_+",
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


def test_tr_validator_disabled_requires_released_timestamp():
    tr_json_disabled_no_released_timestamp = deepcopy(tr_json_valid_released_example)
    tr_json_disabled_no_released_timestamp["disabled_timestamp"] = (
        tr_json_disabled_no_released_timestamp["released_timestamp"]
    )
    tr_json_disabled_no_released_timestamp["state"] = "DISABLED"
    tr_json_disabled_no_released_timestamp["released_timestamp"] = None
    tr_set_released_timestamp = TransformationRevision(**tr_json_disabled_no_released_timestamp)

    assert tr_set_released_timestamp.released_timestamp is not None
    assert (
        tr_set_released_timestamp.released_timestamp == tr_set_released_timestamp.disabled_timestamp
    )


def test_tr_validator_timestampsset_corresponding_to_state():
    tr_json_draft_with_released_timestamp = deepcopy(tr_json_valid_released_example)
    tr_json_draft_with_released_timestamp["state"] = "DRAFT"
    with pytest.raises(ValueError, match="released_timestamp must not be set"):
        TransformationRevision(**tr_json_draft_with_released_timestamp)

    tr_json_released_without_released_timestamp = deepcopy(tr_json_valid_released_example)
    tr_json_released_without_released_timestamp["released_timestamp"] = None

    with pytest.raises(ValueError, match="released_timestamp must be set"):
        TransformationRevision(**tr_json_released_without_released_timestamp)

    tr_json_released_with_disabled_timestamp = deepcopy(tr_json_valid_released_example)
    tr_json_released_with_disabled_timestamp["disabled_timestamp"] = (
        tr_json_released_with_disabled_timestamp["released_timestamp"]
    )

    with pytest.raises(ValueError, match="disabled_timestamp must not be set"):
        TransformationRevision(**tr_json_released_with_disabled_timestamp)

    tr_json_disabled_without_disabled_timestamp = deepcopy(tr_json_valid_released_example)
    tr_json_disabled_without_disabled_timestamp["state"] = "DISABLED"

    with pytest.raises(ValueError, match="disabled_timestamp must be set"):
        TransformationRevision(**tr_json_disabled_without_disabled_timestamp)


def test_wrap_component_in_tr_workflow():
    tr_component = TransformationRevision(**valid_component_tr_dict)

    tr_workflow = tr_component.wrap_component_in_tr_workflow()

    assert tr_workflow.name == "COMPONENT EXECUTION WRAPPER WORKFLOW"
    assert valid_component_tr_dict["category"] == tr_workflow.category
    assert valid_component_tr_dict["version_tag"] == tr_workflow.version_tag
    assert valid_component_tr_dict["state"] == tr_workflow.state
    assert tr_workflow.type == Type.WORKFLOW
    assert len(tr_workflow.content.operators) == 1
    assert valid_component_tr_dict["id"] == str(tr_workflow.content.operators[0].transformation_id)
    assert len(valid_component_tr_dict["io_interface"]["inputs"]) == len(
        tr_workflow.content.operators[0].inputs
    )
    assert len(valid_component_tr_dict["io_interface"]["outputs"]) == len(
        tr_workflow.content.operators[0].outputs
    )
    assert len(tr_component.io_interface.inputs) == len(tr_workflow.content.inputs)
    assert len(tr_component.io_interface.outputs) == len(tr_workflow.content.outputs)

    assert len(tr_component.io_interface.inputs) == len(tr_workflow.io_interface.inputs)
    assert len(tr_component.io_interface.outputs) == len(tr_workflow.io_interface.outputs)


def test_to_workflow_node():
    tr_component = TransformationRevision(**valid_component_tr_dict)
    tr_workflow = tr_component.wrap_component_in_tr_workflow()
    nested_transformations = {tr_workflow.content.operators[0].id: tr_component}

    workflow_node = tr_workflow.to_workflow_node(
        uuid4(), nested_nodes(tr_workflow, nested_transformations)
    )

    assert len(workflow_node.inputs) == len(valid_component_tr_dict["io_interface"]["inputs"])
    assert len(workflow_node.outputs) == len(valid_component_tr_dict["io_interface"]["outputs"])
    assert len(workflow_node.sub_nodes) == 1
    assert len(workflow_node.connections) == 0
    assert workflow_node.name == "COMPONENT EXECUTION WRAPPER WORKFLOW"
    assert workflow_node.tr_name == "COMPONENT EXECUTION WRAPPER WORKFLOW"


def test_transformation_validation_for_change_dynamic_input_to_constant(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with open(
        os.path.join(
            "transformations",
            "workflows",
            "connectors",
            "combine-two-series-into-dataframe_100_09b29726-4373-4652-82c8-7aa3e3f91676.json",
        ),
        encoding="utf8",
    ) as f:
        wf_tr = json.load(f)

    wf_tr_with_changed_dynamic_input_to_constant_dict = deepcopy(wf_tr)
    wf_tr_with_changed_dynamic_input_to_constant_dict["content"]["constants"] = [
        wf_tr_with_changed_dynamic_input_to_constant_dict["content"]["inputs"][0]
    ]
    del wf_tr_with_changed_dynamic_input_to_constant_dict["content"]["inputs"][0]
    del wf_tr_with_changed_dynamic_input_to_constant_dict["content"]["constants"][0]["name"]
    wf_tr_with_changed_dynamic_input_to_constant_dict["content"]["constants"][0]["value"] = ""
    # link from dynamic workflow input #0 b44 to operator #0 ea5 input 156
    del wf_tr_with_changed_dynamic_input_to_constant_dict["content"]["links"][3]["start"][
        "connector"
    ]["name"]
    assert len(wf_tr_with_changed_dynamic_input_to_constant_dict["io_interface"]["inputs"]) == 3
    resulting_tr = TransformationRevision(**wf_tr_with_changed_dynamic_input_to_constant_dict)
    # new link from constant workflow input b44 to operator #0 input 156
    assert "For the io interface input 'b44" in caplog.text
    assert "there is no workflow content input with the same id" in caplog.text
    assert "Thus, it will be removed from the io interface." in caplog.text
    assert "Input '9f4" not in caplog.text
    assert "is in the worklow content but not in the io interface." not in caplog.text
    assert "It will be added to the io interface." not in caplog.text
    assert len(resulting_tr.content.constants) == 1
    assert len(resulting_tr.content.inputs) == 2
    assert len(resulting_tr.io_interface.inputs) == 2

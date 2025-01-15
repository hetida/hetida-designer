import json

import pytest
from pydantic import ValidationError

from hetdesrun.persistence.structure_service_dbmodels import StructureServiceThingNodeDBModel
from hetdesrun.structure.db.structure_service import (
    update_structure,
)
from hetdesrun.structure.models import (
    CompleteStructure,
    Filter,
    StructureServiceElementType,
    StructureServiceSink,
    StructureServiceSource,
    StructureServiceThingNode,
)


def test_external_id_stakeholder_key_name_non_empty():
    with pytest.raises(ValueError, match="The field external_id cannot be empty"):
        StructureServiceElementType(external_id="", stakeholder_key="valid_key", name="TestElement")

    with pytest.raises(ValueError, match="The field stakeholder_key cannot be empty"):
        StructureServiceThingNode(
            external_id="valid_id", stakeholder_key="", name="TestStructureServiceThingNode"
        )

    with pytest.raises(ValueError, match="The field name cannot be empty"):
        StructureServiceSource(external_id="valid_id", stakeholder_key="valid_key", name="")


def test_complete_structure_initialization_from_json():
    file_path = "tests/structure/data/db_test_structure.json"
    with open(file_path) as file:
        structure_json = json.load(file)

    complete_structure = CompleteStructure(**structure_json)

    # Check the number of elements based on JSON content
    assert len(complete_structure.element_types) == len(structure_json["element_types"])
    assert len(complete_structure.thing_nodes) == len(structure_json["thing_nodes"])
    assert len(complete_structure.sources) == len(structure_json["sources"])
    assert len(complete_structure.sinks) == len(structure_json["sinks"])

    # Extract thing node names dynamically from the JSON file and validate
    expected_names = [tn["name"] for tn in structure_json["thing_nodes"]]
    thing_node_names = [tn.name for tn in complete_structure.thing_nodes]

    for name in expected_names:
        assert name in thing_node_names, f"Expected thing node name '{name}' not found."


def test_complete_structure_element_type_not_empty_validator():
    with pytest.raises(
        ValidationError,
        match=(
            "The structure must include at least one StructureServiceElementType object "
            "to be valid."
        ),
    ):
        CompleteStructure(element_types=[])


def test_complete_structure_duplicate_key_id_validator():
    file_path = "tests/structure/data/db_test_invalid_structure_no_duplicate_id.json"
    with open(file_path) as file:
        structure_json = json.load(file)

    with pytest.raises(
        ValidationError,
        match="The stakeholder key and external id pair",
    ):
        CompleteStructure(**structure_json)


def test_complete_structure_duplicate_thingnode_external_id_validator():
    file_path = "tests/structure/data/db_test_no_duplicate_tn_id.json"
    with open(file_path) as file:
        structure_json = json.load(file)

    with pytest.raises(
        ValidationError,
        match="The thing_node_external_ids attribute",
    ):
        CompleteStructure(**structure_json)


@pytest.fixture()
def filter_json():
    file_path = "tests/structure/data/test_filter_creation.json"
    with open(file_path) as file:
        f_json = json.load(file)
    return f_json


def test_filter_class_internal_name_field_creation(filter_json):
    # No value is provided for internal_name but name is provided
    filter_with_no_internal_name_provided = Filter(**filter_json["filter_without_internal_name"])
    assert filter_with_no_internal_name_provided.internal_name == "upper_threshold"

    # A valid value is provided for internal_name
    filter_with_internal_name_provided = Filter(**filter_json["filter_with_valid_internal_name"])
    assert filter_with_internal_name_provided.internal_name == "lower_threshold1"

    # An invalid value is provided for internal_name
    with pytest.raises(
        ValidationError,
        match="The internal_name of the filter can only contain "
        "alphanumeric characters and underscores.",
    ):
        Filter(**filter_json["filter_with_invalid_internal_name"])

    # A value with uncommon whitespace is provided for name
    # No internal_name provided
    filter_with_weird_name_provided = Filter(
        **filter_json["filter_without_internal_name_with_uncommon_whitespace"]
    )
    assert filter_with_weird_name_provided.internal_name == "min_max"


def test_filter_class_name_validation(filter_json):
    # Test with empty name
    with pytest.raises(
        ValidationError,
        match="The name of the filter must be set to a non-empty string, "
        "that only contains alphanumeric characters, underscores and spaces.",
    ):
        Filter(**filter_json["filter_with_empty_string_as_name"])

    # Test with invalid name
    with pytest.raises(
        ValidationError,
        match="The name of the filter must be set to a non-empty string, "
        "that only contains alphanumeric characters, underscores and spaces.",
    ):
        Filter(**filter_json["filter_with_invalid_string_as_name"])


def test_source_sink_passthrough_filters_no_duplicate_keys_validator(filter_json):
    example_source = {
        "external_id": "EnergyUsage_PumpSystem_StorageTank",
        "stakeholder_key": "GW",
        "name": "nf",
        "type": "multitsframe",
        "adapter_key": "sql-adapter",
        "source_id": "nf",
        "thing_node_external_ids": ["Waterworks1"],
        "passthrough_filters": [
            filter_json["filter_with_valid_internal_name"],
            filter_json["filter_with_valid_internal_name"],
        ],
    }

    with pytest.raises(
        ValidationError,
        match="is shared by atleast two filters, provided for this source, it must be unique.",
    ):
        StructureServiceSource(**example_source)

    example_sink = example_source
    example_sink["sink_id"] = example_sink.pop("source_id")

    with pytest.raises(
        ValidationError,
        match="is shared by atleast two filters, provided for this sink, it must be unique.",
    ):
        StructureServiceSink(**example_sink)


def test_validate_root_nodes_parent_ids_are_none(mocked_clean_test_db_session):
    file_path = "tests/structure/data/db_invalid_structure_root_nodes.json"
    with open(file_path) as file:
        invalid_structure = json.load(file)

    invalid_node = next(
        node
        for node in invalid_structure["thing_nodes"]
        if node["parent_external_node_id"] == "InvalidNodeID"
    )
    invalid_node_name = invalid_node["name"]
    invalid_parent_id = invalid_node["parent_external_node_id"]

    with pytest.raises(
        ValueError,
        match=(
            f"Root node '{invalid_node_name}' has an invalid "
            f"parent_external_node_id '{invalid_parent_id}'"
        ),
    ):
        CompleteStructure(**invalid_structure)


def test_circular_tn_relation(mocked_clean_test_db_session):
    file_path = "tests/structure/data/db_circular_structure.json"
    with open(file_path) as file:
        circular_data = json.load(file)

    with pytest.raises(ValueError, match="Circular reference detected in node"):
        CompleteStructure(**circular_data)


def test_stakeholder_key_consistency(mocked_clean_test_db_session):
    file_path = "tests/structure/data/db_conflicting_stakeholder_keys.json"
    with open(file_path) as file:
        conflicting_structure = json.load(file)

    with pytest.raises(ValueError, match="Inconsistent stakeholder_key at node"):
        CompleteStructure(**conflicting_structure)


# Verifies that the structure update can handle multiple root nodes
def test_update_structure_two_root_nodes(mocked_clean_test_db_session):
    file_path = "tests/structure/data/db_two_root_nodes_structure.json"
    with open(file_path) as file:
        structure_data = json.load(file)

    structure_with_two_root_nodes = CompleteStructure(**structure_data)
    root_nodes = [
        node
        for node in structure_with_two_root_nodes.thing_nodes
        if node.parent_external_node_id is None
    ]

    assert len(root_nodes) == 2, f"Expected 2 root nodes, found {len(root_nodes)}"

    update_structure(structure_with_two_root_nodes)

    with mocked_clean_test_db_session() as session:
        updated_nodes = session.query(StructureServiceThingNodeDBModel).all()
        assert len(updated_nodes) == len(
            structure_with_two_root_nodes.thing_nodes
        ), "Database update failed, node count does not match"


def test_validate_source_sink_references(mocked_clean_test_db_session):
    invalid_source_file_path = "tests/structure/data/db_invalid_source_structure.json"
    with open(invalid_source_file_path) as file:
        invalid_source_structure = json.load(file)

    with pytest.raises(
        ValueError,
        match="StructureServiceSource 'Source1' references non-existing "
        "StructureServiceThingNode 'NonExistentNode'\\.",
    ):
        CompleteStructure(**invalid_source_structure)

    invalid_sink_file_path = "tests/structure/data/db_invalid_sink_structure.json"
    with open(invalid_sink_file_path) as file:
        invalid_sink_structure = json.load(file)
    with pytest.raises(
        ValueError,
        match="StructureServiceSink 'Sink1' references non-existing"
        " StructureServiceThingNode 'NonExistentNode'\\.",
    ):
        CompleteStructure(**invalid_sink_structure)

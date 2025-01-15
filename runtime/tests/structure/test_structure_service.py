import json
import uuid

import pytest

from hetdesrun.persistence.db_engine_and_session import get_session
from hetdesrun.persistence.structure_service_dbmodels import (
    StructureServiceElementTypeDBModel,
    StructureServiceSinkDBModel,
    StructureServiceSourceDBModel,
    StructureServiceThingNodeDBModel,
    thingnode_sink_association,
    thingnode_source_association,
)
from hetdesrun.structure.db.element_type_service import (
    upsert_element_types,
)
from hetdesrun.structure.db.exceptions import (
    JsonParsingError,
)
from hetdesrun.structure.db.source_sink_service import (
    upsert_sinks,
    upsert_sources,
)
from hetdesrun.structure.db.structure_service import (
    are_structure_tables_empty,
    delete_structure,
    get_children,
    load_structure_from_json_file,
    sort_thing_nodes,
    update_structure,
)
from hetdesrun.structure.db.thing_node_service import (
    upsert_thing_nodes,
)
from hetdesrun.structure.models import (
    CompleteStructure,
    Filter,
    StructureServiceElementType,
    StructureServiceSink,
    StructureServiceSource,
    StructureServiceThingNode,
)
from tests.structure.utils import (
    fetch_element_types,
    fetch_sinks,
    fetch_sources,
    fetch_thing_nodes,
)

# Tests for Hierarchy and Relationships


@pytest.mark.usefixtures("_db_test_structure")
def test_thing_node_hierarchy(mocked_clean_test_db_session):  # noqa: PLR0915
    """Test the hierarchy and relationships in the database based on loaded data from JSON."""

    # Load expected data from the JSON file
    file_path = "tests/structure/data/db_test_structure.json"
    with open(file_path) as file:
        expected_data = json.load(file)

    expected_element_type_keys = {
        (et["stakeholder_key"], et["external_id"]) for et in expected_data["element_types"]
    }
    expected_thing_node_keys = {
        (tn["stakeholder_key"], tn["external_id"]) for tn in expected_data["thing_nodes"]
    }
    expected_source_keys = {
        (src["stakeholder_key"], src["external_id"]) for src in expected_data["sources"]
    }
    expected_sink_keys = {
        (snk["stakeholder_key"], snk["external_id"]) for snk in expected_data["sinks"]
    }

    with mocked_clean_test_db_session() as session:
        element_types_in_db = fetch_element_types(session, expected_element_type_keys)
        assert len(element_types_in_db) == len(
            expected_data["element_types"]
        ), "Mismatch in element types count"

        thing_nodes_in_db = fetch_thing_nodes(session, expected_thing_node_keys)
        assert len(thing_nodes_in_db) == len(
            expected_data["thing_nodes"]
        ), "Mismatch in thing nodes count"

        sources_in_db = fetch_sources(session, expected_source_keys)
        assert len(sources_in_db) == len(expected_data["sources"]), "Mismatch in sources count"

        sinks_in_db = fetch_sinks(session, expected_sink_keys)
        assert len(sinks_in_db) == len(expected_data["sinks"]), "Mismatch in sinks count"

        # Verify parent-child relationships in thing nodes
        for thing_node in expected_data["thing_nodes"]:
            key = (thing_node["stakeholder_key"], thing_node["external_id"])
            if thing_node.get("parent_external_node_id"):
                parent_key = (thing_node["stakeholder_key"], thing_node["parent_external_node_id"])
                assert parent_key in thing_nodes_in_db, f"Parent node {parent_key} not found in DB"
                assert (
                    thing_nodes_in_db[key].parent_node_id == thing_nodes_in_db[parent_key].id
                ), f"{key} has incorrect parent ID"

        # Verify associations for sources
        for source in expected_data["sources"]:
            source_key = (source["stakeholder_key"], source["external_id"])
            assert source_key in sources_in_db, f"Source {source_key} not found in DB"
            expected_associated_nodes = {
                (thing_node["stakeholder_key"], thing_node["external_id"])
                for tn_id in source["thing_node_external_ids"]
                for thing_node in expected_data["thing_nodes"]
                if thing_node["external_id"] == tn_id
            }
            actual_associated_nodes = {
                (tn.stakeholder_key, tn.external_id) for tn in sources_in_db[source_key].thing_nodes
            }
            assert (
                actual_associated_nodes == expected_associated_nodes
            ), f"Incorrect associations for source {source_key}"

        # Verify associations for sinks
        for sink in expected_data["sinks"]:
            sink_key = (sink["stakeholder_key"], sink["external_id"])
            assert sink_key in sinks_in_db, f"Sink {sink_key} not found in DB"
            expected_associated_nodes = {
                (thing_node["stakeholder_key"], thing_node["external_id"])
                for tn_id in sink["thing_node_external_ids"]
                for thing_node in expected_data["thing_nodes"]
                if thing_node["external_id"] == tn_id
            }
            actual_associated_nodes = {
                (tn.stakeholder_key, tn.external_id) for tn in sinks_in_db[sink_key].thing_nodes
            }
            assert (
                actual_associated_nodes == expected_associated_nodes
            ), f"Incorrect associations for sink {sink_key}"


### Structure Helper Functions


def test_complete_structure_object_creation():
    # Load the expected data from the JSON file
    file_path = "tests/structure/data/db_test_structure.json"
    with open(file_path) as file:
        data = json.load(file)

    # Create a CompleteStructure object from the loaded JSON data
    cs = CompleteStructure(**data)

    # Assert the lengths based on the JSON data
    assert len(cs.thing_nodes) == len(
        data["thing_nodes"]
    ), f"Expected {len(data['thing_nodes'])} Thing Nodes, found {len(cs.thing_nodes)}"
    assert len(cs.element_types) == len(
        data["element_types"]
    ), f"Expected {len(data['element_types'])} Element Types, found {len(cs.element_types)}"
    assert len(cs.sources) == len(
        data["sources"]
    ), f"Expected {len(data['sources'])} Sources, found {len(cs.sources)}"
    assert len(cs.sinks) == len(
        data["sinks"]
    ), f"Expected {len(data['sinks'])} Sinks, found {len(cs.sinks)}"

    # Check if all expected Thing Node names are present
    tn_names = {tn.name for tn in cs.thing_nodes}
    expected_tn_names = {tn["name"] for tn in data["thing_nodes"]}
    assert (
        tn_names == expected_tn_names
    ), f"Mismatch in Thing Node names. Expected: {expected_tn_names}, found: {tn_names}"


def test_load_structure_from_json_file(db_test_structure_file_path):
    # Load the structure from the JSON file using the load_structure_from_json_file function
    complete_structure = load_structure_from_json_file(db_test_structure_file_path)

    # Assert that the loaded structure is an instance of the CompleteStructure class
    assert isinstance(
        complete_structure, CompleteStructure
    ), "Loaded structure is not an instance of CompleteStructure"

    # Load the expected structure directly from the JSON file for comparison
    with open(db_test_structure_file_path) as file:
        expected_structure_json = json.load(file)

    # Convert the expected JSON structure into a CompleteStructure instance
    expected_structure = CompleteStructure(**expected_structure_json)

    # Pair corresponding lists from the complete_structure and expected_structure
    # (such as element_types, thing_nodes, sources, and sinks).
    # Ensure that UUIDs match by setting them to the same value for each pair.
    for complete_list, expected_list in [
        (complete_structure.element_types, expected_structure.element_types),
        (complete_structure.thing_nodes, expected_structure.thing_nodes),
        (complete_structure.sources, expected_structure.sources),
        (complete_structure.sinks, expected_structure.sinks),
    ]:
        for complete, expected in zip(complete_list, expected_list, strict=False):
            uniform_id = uuid.uuid4()
            complete.id = uniform_id
            expected.id = uniform_id

    # Ensure that element_type_id fields in StructureServiceThingNodes match
    for complete, expected in zip(
        complete_structure.thing_nodes, expected_structure.thing_nodes, strict=False
    ):
        uniform_id = uuid.uuid4()
        complete.element_type_id = uniform_id
        expected.element_type_id = uniform_id

    # Assert that the entire loaded structure matches the expected structure
    assert (
        complete_structure == expected_structure
    ), "Loaded structure does not match the expected structure"


def test_load_structure_from_invalid_json_file():
    with pytest.raises(FileNotFoundError):
        load_structure_from_json_file("non_existent_file.json")
    with pytest.raises(JsonParsingError):
        load_structure_from_json_file("tests/structure/data/db_test_structure_malformed.json")


def test_load_structure_from_json_with_invalid_data():
    invalid_structure_path = "tests/structure/data/db_test_structure_invalid_data.json"
    with pytest.raises(JsonParsingError) as exc_info:
        load_structure_from_json_file(invalid_structure_path)
    assert "Validation error" in str(exc_info.value)


@pytest.mark.usefixtures("_db_test_structure")
def test_delete_structure(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        # Verify that the database is initially populated
        assert session.query(StructureServiceElementTypeDBModel).count() > 0
        assert session.query(StructureServiceThingNodeDBModel).count() > 0
        assert session.query(StructureServiceSourceDBModel).count() > 0
        assert session.query(StructureServiceSinkDBModel).count() > 0
        assert session.query(thingnode_source_association).count() > 0
        assert session.query(thingnode_sink_association).count() > 0

    delete_structure()

    with mocked_clean_test_db_session() as session:
        # Verify that all tables are empty after purging
        assert session.query(StructureServiceElementTypeDBModel).count() == 0
        assert session.query(StructureServiceThingNodeDBModel).count() == 0
        assert session.query(StructureServiceSourceDBModel).count() == 0
        assert session.query(StructureServiceSinkDBModel).count() == 0
        assert session.query(thingnode_source_association).count() == 0
        assert session.query(thingnode_sink_association).count() == 0


@pytest.mark.usefixtures("_db_test_structure")
def test_update_structure_with_new_elements():
    # Load the initial and updated structure from JSON files
    initial_file_path = "tests/structure/data/db_test_structure.json"
    updated_file_path = "tests/structure/data/db_updated_test_structure.json"

    # Load structures from JSON files
    with open(initial_file_path) as file:
        initial_structure_data = json.load(file)

    with open(updated_file_path) as file:
        updated_structure_data = json.load(file)

    with get_session()() as session, session.begin():
        # Verify the initial structure in the database
        verify_structure(session, initial_structure_data)

        # Load and update the structure with new elements
        updated_structure = load_structure_from_json_file(updated_file_path)

        # Clear the existing entries
        delete_structure()  # Clears all relevant tables

        # Perform the structure update
        update_structure(updated_structure)

    with get_session()() as session, session.begin():
        # Verify that the updated structure is correct in the database
        verify_structure(session, updated_structure_data)


def verify_structure(session, structure_data):
    # Verify the count of entries for main models based on JSON data
    model_data_pairs = [
        (StructureServiceElementTypeDBModel, structure_data["element_types"]),
        (StructureServiceThingNodeDBModel, structure_data["thing_nodes"]),
        (StructureServiceSourceDBModel, structure_data["sources"]),
        (StructureServiceSinkDBModel, structure_data["sinks"]),
    ]

    for model, data in model_data_pairs:
        actual_count = session.query(model).count()
        expected_count = len(data)
        assert (
            actual_count == expected_count
        ), f"Expected {expected_count} entries for {model.__name__}, found {actual_count}"

    # Check specific attributes based on JSON data
    for thing_node in structure_data["thing_nodes"]:
        tn_db = (
            session.query(StructureServiceThingNodeDBModel)
            .filter_by(external_id=thing_node["external_id"])
            .one()
        )
        for key, value in thing_node.get("meta_data", {}).items():
            assert (
                tn_db.meta_data.get(key) == value
            ), f"Mismatch in {key} for ThingNode '{tn_db.external_id}'"


def test_update_structure(mocked_clean_test_db_session):
    # This test checks both the insert and update functionality of the update_structure function.
    # It starts with an empty database, loads a complete structure from a JSON file, and then
    # inserts it into the database. The test then verifies that the structure
    # has been correctly inserted/updated in the database.

    # Load test data from JSON file
    with open("tests/structure/data/db_test_structure.json") as file:
        data = json.load(file)
    # Create a CompleteStructure object from the loaded JSON data
    complete_structure = CompleteStructure(**data)

    # Perform the update, which in this case acts as an insert since the database is empty
    update_structure(complete_structure)

    # Open a new session to interact with the database
    with mocked_clean_test_db_session() as session:
        # Fetch all ThingNodes, Sources, Sinks, and ElementTypes from the database
        thing_nodes = session.query(StructureServiceThingNodeDBModel).all()
        sources = session.query(StructureServiceSourceDBModel).all()
        sinks = session.query(StructureServiceSinkDBModel).all()
        element_types = session.query(StructureServiceElementTypeDBModel).all()

        # Verify that the number of ThingNodes in the database
        # matches the number in the JSON structure
        assert len(thing_nodes) == len(
            complete_structure.thing_nodes
        ), "Mismatch in number of thing nodes"
        # Verify that the number of Sources in the database matches the number in the JSON structure
        assert len(sources) == len(complete_structure.sources), "Mismatch in number of sources"
        # Verify that the number of Sinks in the database matches the number in the JSON structure
        assert len(sinks) == len(complete_structure.sinks), "Mismatch in number of sinks"
        # Verify that the number of ElementTypes in the database
        # matches the number in the JSON structure
        assert len(element_types) == len(
            complete_structure.element_types
        ), "Mismatch in number of element types"

        # Validate that specific ThingNodes, Sources, and Sinks exist in the database
        # Check if the 'Waterworks 1' ThingNode was correctly inserted
        waterworks_node = next((tn for tn in thing_nodes if tn.name == "Waterworks 1"), None)
        assert waterworks_node is not None, "Expected 'Waterworks 1' node not found"

        # Check if the 'Energy consumption of a single pump in Storage Tank' Source
        # was correctly inserted
        source = next(
            (s for s in sources if s.name == "Energy consumption of a single pump in Storage Tank"),
            None,
        )
        assert (
            source is not None
        ), "Expected source 'Energy consumption of a single pump in Storage Tank' not found"

        # Check if the 'Anomaly Score for the energy usage of the pump system in
        # Storage Tank' Sink was correctly inserted
        sink = next(
            (
                s
                for s in sinks
                if s.name == "Anomaly Score for the energy usage of the pump system in Storage Tank"
            ),
            None,
        )
        assert sink is not None, (
            "Expected sink 'Anomaly Score for the energy usage"
            " of the pump system in Storage Tank' not found"
        )


def test_update_structure_from_file(mocked_clean_test_db_session):
    # This test checks the insert functionality of the update_structure function.
    # It starts with an empty database and verifies that the structure from the JSON file
    # is correctly inserted into the database.

    # Path to the JSON file containing the test structure
    file_path = "tests/structure/data/db_test_structure.json"

    # Load structure data from the file
    with open(file_path) as file:
        structure_data = json.load(file)

    # Ensure the database is empty at the beginning
    with get_session()() as session:
        model_data_pairs = [
            StructureServiceElementTypeDBModel,
            StructureServiceThingNodeDBModel,
            StructureServiceSourceDBModel,
            StructureServiceSinkDBModel,
        ]
        for model in model_data_pairs:
            assert session.query(model).count() == 0, f"Expected 0 entries for {model.__name__}"

    # Load and update the structure in the database with the loaded structure data
    complete_structure = CompleteStructure(**structure_data)
    update_structure(complete_structure)

    # Verify that the structure was correctly inserted
    with get_session()() as session:
        # Check each model based on structure data counts
        model_data_map = {
            StructureServiceElementTypeDBModel: structure_data["element_types"],
            StructureServiceThingNodeDBModel: structure_data["thing_nodes"],
            StructureServiceSourceDBModel: structure_data["sources"],
            StructureServiceSinkDBModel: structure_data["sinks"],
        }
        for model, data in model_data_map.items():
            actual_count = session.query(model).count()
            expected_count = len(data)
            assert (
                actual_count == expected_count
            ), f"Expected {expected_count} entries for {model.__name__}, found {actual_count}"

        # Verify attributes for each entry type
        for element_type in structure_data["element_types"]:
            db_element_type = (
                session.query(StructureServiceElementTypeDBModel)
                .filter_by(external_id=element_type["external_id"])
                .one()
            )
            assert db_element_type.name == element_type["name"]
            assert db_element_type.description == element_type.get("description", "")

        for thing_node in structure_data["thing_nodes"]:
            db_thing_node = (
                session.query(StructureServiceThingNodeDBModel)
                .filter_by(external_id=thing_node["external_id"])
                .one()
            )
            assert db_thing_node.name == thing_node["name"]
            for key, value in thing_node.get("meta_data", {}).items():
                assert (
                    db_thing_node.meta_data.get(key) == value
                ), f"Mismatch in {key} for ThingNode '{db_thing_node.external_id}'"

        for source in structure_data["sources"]:
            db_source = (
                session.query(StructureServiceSourceDBModel)
                .filter_by(external_id=source["external_id"])
                .one()
            )
            assert db_source.name == source["name"]
            for key, value in source.get("meta_data", {}).items():
                assert (
                    db_source.meta_data.get(key) == value
                ), f"Mismatch in {key} for Source '{db_source.external_id}'"

        for sink in structure_data["sinks"]:
            db_sink = (
                session.query(StructureServiceSinkDBModel)
                .filter_by(external_id=sink["external_id"])
                .one()
            )
            assert db_sink.name == sink["name"]
            for key, value in sink.get("meta_data", {}).items():
                assert (
                    db_sink.meta_data.get(key) == value
                ), f"Mismatch in {key} for Sink '{db_sink.external_id}'"


@pytest.mark.usefixtures("_db_test_structure")
def test_update_structure_no_elements_deleted():
    # This test ensures that no elements are deleted when updating the structure
    # with a new JSON file that omits some elements.

    # Define paths to the JSON files
    old_file_path = "tests/structure/data/db_test_structure.json"
    new_file_path = "tests/structure/data/db_test_incomplete_structure.json"

    # Load initial structure from JSON file
    initial_structure: CompleteStructure = load_structure_from_json_file(old_file_path)

    # Load updated structure from new JSON file
    updated_structure: CompleteStructure = load_structure_from_json_file(new_file_path)

    # Update the structure in the database with new structure
    update_structure(updated_structure)

    # Verify structure after update
    with get_session()() as session:
        # Check the total number of elements remains unchanged
        assert session.query(StructureServiceElementTypeDBModel).count() == len(
            initial_structure.element_types
        )
        assert session.query(StructureServiceThingNodeDBModel).count() == len(
            initial_structure.thing_nodes
        )
        assert session.query(StructureServiceSourceDBModel).count() == len(
            initial_structure.sources
        )
        assert session.query(StructureServiceSinkDBModel).count() == len(initial_structure.sinks)

        # Verify specific elements from the initial structure are still present
        for element_type in initial_structure.element_types:
            assert (
                session.query(StructureServiceElementTypeDBModel)
                .filter_by(external_id=element_type.external_id)
                .count()
                == 1
            )

        for thing_node in initial_structure.thing_nodes:
            assert (
                session.query(StructureServiceThingNodeDBModel)
                .filter_by(external_id=thing_node.external_id)
                .count()
                == 1
            )

        for source in initial_structure.sources:
            assert (
                session.query(StructureServiceSourceDBModel)
                .filter_by(external_id=source.external_id)
                .count()
                == 1
            )

        for sink in initial_structure.sinks:
            assert (
                session.query(StructureServiceSinkDBModel)
                .filter_by(external_id=sink.external_id)
                .count()
                == 1
            )


@pytest.mark.usefixtures("_db_test_structure")
def test_update_structure_modify_parent_child_relationship():
    # This test ensures that the modification of parent-child relationships
    # in thing nodes is correctly reflected after an update.

    # Define paths to the JSON files
    new_file_path = "tests/structure/data/db_test_incomplete_structure2.json"

    # Load updated structure from new JSON file
    updated_structure: CompleteStructure = load_structure_from_json_file(new_file_path)

    # Update the structure in the database with new structure
    update_structure(updated_structure)

    # Verify structure after update
    with get_session()() as session:
        # Check parent-child relationships
        root_node = (
            session.query(StructureServiceThingNodeDBModel)
            .filter_by(external_id="Waterworks1")
            .first()
        )
        storage_tank_node = (
            session.query(StructureServiceThingNodeDBModel)
            .filter_by(external_id="Waterworks1_Plant1_StorageTank1")
            .first()
        )

        # Ensure the parent node is now directly linked to the root node
        assert storage_tank_node.parent_node_id == root_node.id


@pytest.mark.usefixtures("_db_test_structure")
def test_update_structure_modified_source_thing_node_relation():
    """Updates the thing node relationship of one source and verifies that the update took effect"""

    # Verify structure before update
    with get_session()() as session:
        source_from_db_initial = (
            session.query(StructureServiceSourceDBModel)
            .filter_by(external_id="EnergyUsage_PumpSystem_StorageTank")
            .first()
        )
        print("\n---  DB structure before update:")
        print(f"Thing node IDs in DB: {[tn.id for tn in source_from_db_initial.thing_nodes]}")

        # The node to which the newly set relationship will point
        root_node_from_db_initial = (
            session.query(StructureServiceThingNodeDBModel)
            .filter_by(external_id="Waterworks1")
            .first()
        )

    # Update the structure
    file_path = "tests/structure/data/db_test_source_relationship_update.json"
    updated_structure = load_structure_from_json_file(file_path)
    update_structure(updated_structure)

    # Verify structure after update
    with get_session()() as session:
        source_from_db_updated = (
            session.query(StructureServiceSourceDBModel)
            .filter_by(external_id="EnergyUsage_PumpSystem_StorageTank")
            .first()
        )

        updated_source_relationship_id = source_from_db_updated.thing_nodes[0].id

        # Verify that the targeted source was updated
        assert source_from_db_updated.id == source_from_db_initial.id

        # Verify that thing nodes relationship was updated
        assert len(source_from_db_updated.thing_nodes) == 1
        assert updated_source_relationship_id == root_node_from_db_initial.id


@pytest.mark.skip(
    reason="This tests whether a partial update is possible. Currently it is not supported"
)
@pytest.mark.usefixtures("_db_test_structure")
def test_update_structure_modified_source_thing_node_relation_with_missing_thing_node():
    # Verify structure before update
    with get_session()() as session:
        source_from_db_initial = (
            session.query(StructureServiceSourceDBModel)
            .filter_by(external_id="EnergyUsage_PumpSystem_StorageTank")
            .first()
        )

        print("\n---  DB structure before update:")
        print(f"Source ID in DB: {source_from_db_initial.id}")
        print(f"Thing node external IDs in DB: {source_from_db_initial.thing_node_external_ids}")
        print(f"Thing nodes in DB: {source_from_db_initial.thing_nodes}")

    # Define paths to the JSON files
    file_path = "tests/structure/data/db_test_incomplete_structure3.json"

    # Load structure from new JSON file
    updated_structure = load_structure_from_json_file(file_path)
    source_from_structure = updated_structure.sources[0]

    print("\n--- New JSON partial structure before update:")
    print(
        f"Thing node external IDs in new structure: {source_from_structure.thing_node_external_ids}"
    )

    # Update the structure in the database with new structure
    # The new structure links a single source (EnergyUsage_PumpSystem_StorageTank)
    # to thing node 'Plant1' that is not contained in the new structure
    # but in the existing DB structure.
    update_structure(updated_structure)

    # Verify structure after update
    with get_session()() as session:
        source_from_db_updated = (
            session.query(StructureServiceSourceDBModel)
            .filter_by(external_id="EnergyUsage_PumpSystem_StorageTank")
            .first()
        )

        print("\n---  DB structure after update:")
        print(f"Updated Source ID in DB: {source_from_db_updated.id}")
        print(
            "Updated thing node external IDs in DB: "
            f"{source_from_db_updated.thing_node_external_ids}"
        )
        print(f"Thing nodes in DB: {source_from_db_updated.thing_nodes}")

        # Verify that the targeted source was updated
        assert source_from_db_updated.id == source_from_db_initial.id

        # Verify that thing nodes relationship was updated
        # TODO improve assertions
        assert source_from_db_updated.thing_nodes != []
        assert len(source_from_db_updated.thing_nodes) == 1


def test_are_structure_tables_empty_when_empty(mocked_clean_test_db_session):
    assert are_structure_tables_empty(), "Database should be empty but is not."


@pytest.mark.usefixtures("_db_test_structure")
def test_are_structure_tables_empty_when_not_empty(mocked_clean_test_db_session):
    assert not are_structure_tables_empty(), "Database should not be empty but it is."


@pytest.mark.usefixtures("_db_test_unordered_structure")
def test_sort_thing_nodes(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        # Fetch all thing node keys first to pass them to fetch_thing_nodes
        thing_node_keys = {
            (tn.stakeholder_key, tn.external_id)
            for tn in session.query(StructureServiceThingNodeDBModel).all()
        }

        # Fetch all thing nodes from the database
        thing_nodes_in_db = fetch_thing_nodes(session, thing_node_keys)
        thing_nodes_in_db = list(thing_nodes_in_db.values())

        # Run the sort function using the new sort_thing_nodes method
        sorted_nodes = sort_thing_nodes(thing_nodes_in_db)

        # Verify that the sorted_nodes is a list
        assert isinstance(sorted_nodes, list), "sorted_nodes should be a list"

        # Verify the order based on the structure hierarchy
        root_nodes = [node for node in sorted_nodes if node.parent_node_id is None]
        assert len(root_nodes) == 1, "There should be exactly one root node"

        # Generate expected order  based on sorted structure
        expected_order = [node.name for node in sorted_nodes]

        # Extract and compare actual order
        actual_order = [node.name for node in sorted_nodes]
        assert (
            actual_order == expected_order
        ), f"Expected node order {expected_order}, but got {actual_order}"

        # Check that nodes with the same parent are sorted by external_id
        grouped_nodes = {}
        for node in sorted_nodes:
            grouped_nodes.setdefault(node.parent_node_id, []).append(node)

        for group in grouped_nodes.values():
            group_names = [node.name for node in sorted(group, key=lambda x: x.external_id)]
            assert group_names == [
                node.name for node in group
            ], "Nodes should be sorted by external_id. "
            f"Expected {group_names}, got {[node.name for node in group]}"

        # Ensure the condition where a parent_node_id is not initially in existing_thing_nodes
        orphan_node = StructureServiceThingNodeDBModel(
            external_id="Orphan_StorageTank",
            name="Orphan Storage Tank",
            stakeholder_key="GW",
            parent_node_id=uuid.uuid4(),  # Ensure this UUID does not match any existing node
            parent_external_node_id="NonExistentParent",  # Set to a value not in thing_node_map
            element_type_id=uuid.uuid4(),
            element_type_external_id="StorageTank_Type",  # Required element_type_external_id
            meta_data={},
        )

        thing_nodes_in_db.append(orphan_node)

        # Re-run the sort function with the orphan node added
        sorted_nodes_with_orphan = sort_thing_nodes(thing_nodes_in_db)

        # Verify that the orphan node is not placed in the list
        assert (
            orphan_node not in sorted_nodes_with_orphan
        ), "Orphan node should not be included in the sorted list"


def test_upsert_element_types_success(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        # Create StructureServiceElementType objects to upsert
        elements = [
            StructureServiceElementType(
                id=uuid.uuid4(),
                external_id="type1",
                stakeholder_key="GW",
                name="Test StructureServiceElementType",
                description="Description",
            )
        ]

        # Call the function
        upsert_element_types(session, elements)
        session.commit()

        # Verify that the StructureServiceElementTypeDBModel was added to the database
        result = (
            session.query(StructureServiceElementTypeDBModel)
            .filter_by(external_id="type1")
            .one_or_none()
        )
        assert result is not None
        assert result.name == "Test StructureServiceElementType"


def test_upsert_sinks_success(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        existing_thing_nodes = {}

        # Create StructureServiceSink object to upsert
        sink = StructureServiceSink(
            id=uuid.uuid4(),
            stakeholder_key="GW",
            external_id="sink1",
            name="Test StructureServiceSink",
            type="timeseries(float)",
            visible=True,
            display_path="Path",
            adapter_key="Adapter",
            sink_id="StructureServiceSinkID",
            ref_key=None,
            ref_id="RefID",
            meta_data={},
            preset_filters={},
            passthrough_filters=[Filter(name="filter1", type="free_text", required=True)],
            thing_node_external_ids=[],
        )

        upsert_sinks(session, [sink], existing_thing_nodes)
        session.commit()

        # Verify that the StructureServiceSinkDBModel was added to the database
        result = (
            session.query(StructureServiceSinkDBModel).filter_by(external_id="sink1").one_or_none()
        )
        assert result is not None
        assert result.name == "Test StructureServiceSink"


def test_upsert_sources_success(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        existing_thing_nodes = {}

        # Create StructureServiceSource object to upsert
        source = StructureServiceSource(
            id=uuid.uuid4(),
            stakeholder_key="GW",
            external_id="source1",
            name="Test StructureServiceSource",
            type="timeseries(float)",
            visible=True,
            display_path="Path",
            adapter_key="Adapter",
            source_id="StructureServiceSourceID",
            ref_key=None,
            ref_id="RefID",
            meta_data={},
            preset_filters={},
            passthrough_filters=[Filter(name="filter1", type="free_text", required=True)],
            thing_node_external_ids=[],
        )

        # Call the function
        upsert_sources(session, [source], existing_thing_nodes)
        session.commit()

        # Verify that the StructureServiceSourceDBModel was added to the database
        result = (
            session.query(StructureServiceSourceDBModel)
            .filter_by(external_id="source1")
            .one_or_none()
        )
        assert result is not None
        assert result.name == "Test StructureServiceSource"


def test_upsert_thing_nodes_success(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        # Add an StructureServiceElementTypeDBModel to the session
        element_type_id = uuid.uuid4()
        element_type = StructureServiceElementTypeDBModel(
            id=element_type_id,
            external_id="type1",
            stakeholder_key="GW",
            name="Test StructureServiceElementType",
            description="Description",
        )
        session.add(element_type)
        session.commit()

        # Create StructureServiceThingNode object to upsert
        node = StructureServiceThingNode(
            id=uuid.uuid4(),
            stakeholder_key="GW",
            external_id="node1",
            name="Test Node",
            description="Description",
            parent_node_id=None,
            parent_external_node_id=None,
            element_type_external_id="type1",
            meta_data={},
        )

        # Create existing_element_types dictionary
        existing_element_types = {("GW", "type1"): element_type}

        # Call the function
        upsert_thing_nodes(session, [node], existing_element_types)
        session.commit()

        # Verify that the StructureServiceThingNodeDBModel was added to the database
        result = (
            session.query(StructureServiceThingNodeDBModel)
            .filter_by(external_id="node1")
            .one_or_none()
        )
        assert result is not None
        assert result.name == "Test Node"


@pytest.mark.usefixtures("_db_test_structure")
def test_get_children():
    with get_session()() as session, session.begin():
        # Fetch root and child nodes to avoid hardcoding
        root_node = (
            session.query(StructureServiceThingNodeDBModel).filter_by(parent_node_id=None).one()
        )
        root_children, root_sources, root_sinks = get_children(root_node.id)

        verify_children(root_children, {child.name for child in root_children}, len(root_children))
        verify_sources(root_sources, [source.name for source in root_sources], len(root_sources))
        verify_sinks(root_sinks, [sink.name for sink in root_sinks], len(root_sinks))

        # Verify each child node and its respective children, sources, and sinks
        for child in root_children:
            sub_children, sub_sources, sub_sinks = get_children(child.id)
            verify_children(sub_children, {sc.name for sc in sub_children}, len(sub_children))
            verify_sources(sub_sources, [src.name for src in sub_sources], len(sub_sources))
            verify_sinks(sub_sinks, [snk.name for snk in sub_sinks], len(sub_sinks))


def get_node_by_name(session, name: str) -> StructureServiceThingNodeDBModel:
    """Helper function to fetch a ThingNode by name."""
    node = (
        session.query(StructureServiceThingNodeDBModel)
        .filter(StructureServiceThingNodeDBModel.name == name)
        .one_or_none()
    )
    assert node is not None, f"Expected node '{name}' not found"
    return node


def verify_children(
    children: list[StructureServiceThingNode], expected_names: set, expected_count: int
):
    """Helper function to verify the children nodes."""
    assert (
        len(children) == expected_count
    ), f"Expected {expected_count} children, found {len(children)}"
    children_names = {child.name for child in children}
    assert children_names == expected_names, f"Unexpected child names: {children_names}"


def verify_sources(
    sources: list[StructureServiceSource], expected_names: list, expected_count: int
):
    """Helper function to verify the sources."""
    assert (
        len(sources) == expected_count
    ), f"Expected {expected_count} source(s), found {len(sources)}"
    actual_names = [source.name for source in sources]
    assert actual_names == expected_names, f"Unexpected source names: {actual_names}"


def verify_sinks(sinks: list[StructureServiceSink], expected_names: list, expected_count: int):
    """Helper function to verify the sinks."""
    assert len(sinks) == expected_count, f"Expected {expected_count} sink(s), found {len(sinks)}"
    actual_names = [sink.name for sink in sinks]
    assert actual_names == expected_names, f"Unexpected sink names: {actual_names}"

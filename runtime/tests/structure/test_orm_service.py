import json
import uuid
from sqlite3 import Connection as SQLite3Connection

import pytest
from sqlalchemy import event
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future.engine import Engine

from hetdesrun.persistence.db_engine_and_session import get_session
from hetdesrun.persistence.structure_service_dbmodels import (
    ElementTypeOrm,
    SinkOrm,
    SourceOrm,
    ThingNodeOrm,
    thingnode_sink_association,
    thingnode_source_association,
)
from hetdesrun.structure.db.orm_service import (
    fetch_all_element_types,
    fetch_all_sinks,
    fetch_all_sources,
    fetch_all_thing_nodes,
    fetch_existing_records,
    fill_source_sink_associations_db,
    load_structure_from_json_file,
    orm_delete_structure,
    orm_is_database_empty,
    orm_update_structure,
    sort_thing_nodes_from_db,
    update_existing_elements,
    update_structure_from_file,
)
from hetdesrun.structure.models import (
    CompleteStructure,
    Sink,
    Source,
    ThingNode,
)

# Enable Foreign Key Constraints for SQLite Connections


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection: SQLite3Connection, connection_record) -> None:  # type: ignore  # noqa: E501,
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# Tests for Hierarchy and Relationships


@pytest.mark.usefixtures("_db_test_structure")
def test_thing_node_hierarchy(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        # Fetch all elements from the database
        element_types_in_db = fetch_all_element_types(session)
        thing_nodes_in_db = fetch_all_thing_nodes(session)
        sources_in_db = fetch_all_sources(session)
        sinks_in_db = fetch_all_sinks(session)

        assert len(element_types_in_db) == 3, "Mismatch in element types count"
        assert len(thing_nodes_in_db) == 7, "Mismatch in thing nodes count"
        assert len(sources_in_db) == 3, "Mismatch in sources count"
        assert len(sinks_in_db) == 3, "Mismatch in sinks count"


### Fetch Functions


@pytest.mark.usefixtures("_db_test_structure")
def test_fetch_all_element_types(mocked_clean_test_db_session):
    # Start a session with the mocked clean test database
    with mocked_clean_test_db_session() as session:
        # Fetch all Element Types from the database
        element_types = fetch_all_element_types(session)

        # Assert that the correct number of Element Types were retrieved
        assert len(element_types) == 3, "Expected 3 Element Types in the database"

        # Define the expected Element Types based on the structure in the test database
        expected_element_types = [
            {"external_id": "Wasserwerk_Typ", "name": "Wasserwerk"},
            {"external_id": "Anlage_Typ", "name": "Anlage"},
            {"external_id": "Hochbehaelter_Typ", "name": "Hochbehälter"},
        ]

        # Loop over each expected Element Type and verify that it exists in the retrieved list
        for expected_et in expected_element_types:
            # Generator expression checks if any Element
            # Type matches the expected external_id and name.
            # any() returns True on the first match, making the check efficient.
            found = any(
                et.external_id == expected_et["external_id"] and et.name == expected_et["name"]
                for et in element_types
            )
            # Assert that the expected Element Type was found in the database
            assert found, (
                f"Expected Element Type with external_id {expected_et['external_id']} "
                f"and name {expected_et['name']} not found"
            )


@pytest.mark.usefixtures("_db_test_structure")
def test_fetch_all_thing_nodes(mocked_clean_test_db_session):
    # Start a session to interact with the database
    with mocked_clean_test_db_session() as session:
        # Fetch all ThingNodes from the database
        thing_nodes = fetch_all_thing_nodes(session)

        # Assert that the expected number of ThingNodes is in the database
        assert len(thing_nodes) == 7, "Expected 7 Thing Nodes in the database"

        # Define the expected ThingNodes with their external_id and name
        expected_thing_nodes = [
            {"external_id": "Wasserwerk1", "name": "Wasserwerk 1"},
            {"external_id": "Wasserwerk1_Anlage1", "name": "Anlage 1"},
            {"external_id": "Wasserwerk1_Anlage2", "name": "Anlage 2"},
            {
                "external_id": "Wasserwerk1_Anlage1_Hochbehaelter1",
                "name": "Hochbehälter 1 Anlage 1",
            },
            {
                "external_id": "Wasserwerk1_Anlage1_Hochbehaelter2",
                "name": "Hochbehälter 2 Anlage 1",
            },
            {
                "external_id": "Wasserwerk1_Anlage2_Hochbehaelter1",
                "name": "Hochbehälter 1 Anlage 2",
            },
            {
                "external_id": "Wasserwerk1_Anlage2_Hochbehaelter2",
                "name": "Hochbehälter 2 Anlage 2",
            },
        ]

        # Loop through each expected ThingNode and check if it exists in the fetched ThingNodes
        for expected_tn in expected_thing_nodes:
            # This generator checks if any ThingNode in the list
            # matches the expected external_id and name
            found = any(
                tn.external_id == expected_tn["external_id"] and tn.name == expected_tn["name"]
                for tn in thing_nodes
            )
            # Assert that the expected ThingNode was found in the database
            assert found, (
                f"Expected Thing Node with external_id {expected_tn['external_id']} "
                f"and name {expected_tn['name']} not found"
            )


@pytest.mark.usefixtures("_db_test_structure")
def test_fetch_all_sources(mocked_clean_test_db_session):
    # Start a session to interact with the database
    with mocked_clean_test_db_session() as session:
        # Fetch all Sources from the database
        sources = fetch_all_sources(session)

        # Assert that the expected number of Sources is in the database
        assert len(sources) == 3, "Expected 3 Sources in the database"

        # Define the expected Sources with their external_id and name
        expected_sources = [
            {
                "external_id": "Energieverbraeuche_Pumpensystem_Hochbehaelter",
                "name": "Energieverbräuche des Pumpensystems in Hochbehälter",
            },
            {
                "external_id": "Energieverbrauch_Einzelpumpe_Hochbehaelter",
                "name": "Energieverbrauch einer Einzelpumpe in Hochbehälter",
            },
        ]

        # Loop through each expected Source and check if it exists in the fetched Sources
        for expected_source in expected_sources:
            # This generator checks if any Source in the list
            # matches the expected external_id and name
            found = any(
                source.external_id == expected_source["external_id"]
                and source.name == expected_source["name"]
                for source in sources
            )
            # Assert that the expected Source was found in the database
            assert found, (
                f"Expected Source with external_id {expected_source['external_id']} "
                f"and name {expected_source['name']} not found"
            )


@pytest.mark.usefixtures("_db_test_structure")
def test_fetch_all_sinks(mocked_clean_test_db_session):
    # Start a session to interact with the database
    with mocked_clean_test_db_session() as session:
        # Fetch all Sinks from the database
        sinks = fetch_all_sinks(session)

        # Assert that the expected number of Sinks is in the database
        assert len(sinks) == 3, "Expected 3 Sinks in the database"

        # Define the expected Sinks with their external_id and name
        expected_sinks = [
            {
                "external_id": "Anomaly_Score_Energieverbraeuche_Pumpensystem_Hochbehaelter",
                "name": "Anomaly Score für die Energieverbräuche des Pumpensystems in Hochbehälter",
            },
            {
                "external_id": "Anomaly_Score_Energieverbrauch_Einzelpumpe_Hochbehaelter",
                "name": "Anomaly Score für den Energieverbrauch einer Einzelpumpe in Hochbehälter",
            },
        ]

        # Loop through each expected Sink and check if it exists in the fetched Sinks
        for expected_sink in expected_sinks:
            # This generator checks if any Sink in the list
            # matches the expected external_id and name
            found = any(
                sink.external_id == expected_sink["external_id"]
                and sink.name == expected_sink["name"]
                for sink in sinks
            )
            # Assert that the expected Sink was found in the database
            assert found, (
                f"Expected Sink with external_id {expected_sink['external_id']} "
                f"and name {expected_sink['name']} not found"
            )


### Structure Helper Functions


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
        # Iterate over pairs of corresponding elements (like individual ThingNodes or Sources)
        # from the complete_list and expected_list. This is necessary because the UUIDs (id fields)
        # in these elements are randomly generated and will differ between the loaded structure
        # (complete_structure) and the expected structure (expected_structure). To allow for a
        # meaningful comparison of these structures, we need to set the UUIDs to the same value.
        # The strict=False argument allows the loop to continue even if the two lists have
        # different lengths, which helps prevent unexpected errors in case of discrepancies
        # between the loaded and expected data.
        for complete, expected in zip(complete_list, expected_list, strict=False):
            uniform_id = uuid.uuid4()
            complete.id = uniform_id
            expected.id = uniform_id

    # Ensure that element_type_id fields in ThingNodes match
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
    # Use a non-existent file path to simulate a failure in loading JSON
    with pytest.raises(FileNotFoundError):
        load_structure_from_json_file("non_existent_file.json")


@pytest.mark.usefixtures("_db_test_structure")
def test_delete_structure(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        # Verify that the database is initially populated
        assert session.query(ElementTypeOrm).count() > 0
        assert session.query(ThingNodeOrm).count() > 0
        assert session.query(SourceOrm).count() > 0
        assert session.query(SinkOrm).count() > 0
        assert session.query(thingnode_source_association).count() > 0
        assert session.query(thingnode_sink_association).count() > 0

        orm_delete_structure(session)

        # Verify that all tables are empty after purging
        assert session.query(ElementTypeOrm).count() == 0
        assert session.query(ThingNodeOrm).count() == 0
        assert session.query(SourceOrm).count() == 0
        assert session.query(SinkOrm).count() == 0
        assert session.query(thingnode_source_association).count() == 0
        assert session.query(thingnode_sink_association).count() == 0


@pytest.mark.usefixtures("_db_test_structure")
def test_update_structure_with_new_elements():
    # This test checks the update functionality of the orm_update_structure function.
    # It starts with an existing structure in the database, then updates it with new elements
    # from a JSON file and verifies that the structure in the database reflects these updates.

    with get_session()() as session, session.begin():
        # Verify initial structure
        verify_initial_structure(session)

        # Load updated structure from JSON file
        file_path = "tests/structure/data/db_updated_test_structure.json"
        updated_structure = load_structure_from_json_file(file_path)

    # Update the structure in the database
    orm_update_structure(updated_structure)

    # Verify structure after update
    with get_session()() as session, session.begin():
        verify_updated_structure(session)


def verify_initial_structure(session):
    # Fetch all initial elements from the database
    initial_element_types = session.query(ElementTypeOrm).all()
    initial_thing_nodes = session.query(ThingNodeOrm).all()
    initial_sources = session.query(SourceOrm).all()
    initial_sinks = session.query(SinkOrm).all()

    # Verify that the initial structure contains the correct number of elements
    assert len(initial_element_types) == 3, "Expected 3 Element Types in the initial structure"
    assert len(initial_thing_nodes) == 7, "Expected 7 Thing Nodes in the initial structure"
    assert len(initial_sources) == 3, "Expected 3 Sources in the initial structure"
    assert len(initial_sinks) == 3, "Expected 3 Sinks in the initial structure"

    # Verify specific attributes of the ThingNodes before the update
    initial_tn = (
        session.query(ThingNodeOrm)
        .filter_by(external_id="Wasserwerk1_Anlage1_Hochbehaelter1")
        .one()
    )
    assert (
        initial_tn.meta_data["capacity"] == "5000"
    ), "Initial capacity of Hochbehälter 1 should be 5000"
    assert initial_tn.meta_data["description"] == ("Wasserspeicherungskapazität für Hochbehälter 1")

    initial_tn2 = (
        session.query(ThingNodeOrm)
        .filter_by(external_id="Wasserwerk1_Anlage1_Hochbehaelter2")
        .one()
    )
    assert (
        initial_tn2.meta_data["capacity"] == "6000"
    ), "Initial capacity of Hochbehälter 2 should be 6000"
    assert initial_tn2.meta_data["description"] == (
        "Wasserspeicherungskapazität für Hochbehälter 2"
    )


def verify_updated_structure(session):
    # Fetch all elements from the database after the update
    final_element_types = session.query(ElementTypeOrm).all()
    final_thing_nodes = session.query(ThingNodeOrm).all()
    final_sources = session.query(SourceOrm).all()
    final_sinks = session.query(SinkOrm).all()

    # Verify that the structure now contains the updated number of elements
    assert len(final_element_types) == 4, "Expected 4 Element Types after the update"
    assert len(final_thing_nodes) == 8, "Expected 8 Thing Nodes after the update"
    assert len(final_sources) == 4, "Expected 4 Sources after the update"
    assert len(final_sinks) == 3, "Expected 3 Sinks after the update"

    # Verify the new elements and updated nodes in the structure
    verify_new_elements_and_nodes(session, final_element_types, final_thing_nodes)
    # Verify the associations between ThingNodes, Sources, and Sinks
    verify_associations(session)


def verify_new_elements_and_nodes(session, final_element_types, final_thing_nodes):
    # Verify that a new ElementType was added
    new_element_type = next(
        et for et in final_element_types if et.external_id == "Filteranlage_Typ"
    )
    assert new_element_type.name == "Filteranlage", "Expected new Element Type 'Filteranlage'"
    assert new_element_type.description == "Elementtyp für Filteranlagen"

    # Verify that a new ThingNode was added
    new_tn = next(tn for tn in final_thing_nodes if tn.external_id == "Wasserwerk1_Filteranlage")
    assert new_tn.name == "Filteranlage 1", "Expected new Thing Node 'Filteranlage 1'"
    assert new_tn.description == "Neue Filteranlage im Wasserwerk 1"
    assert (
        new_tn.meta_data["location"] == "Zentral"
    ), "Expected location 'Zentral' for the new Thing Node"
    assert (
        new_tn.meta_data["technology"] == "Advanced Filtration"
    ), "Expected technology 'Advanced Filtration'"

    # Verify that the ThingNodes were updated correctly
    updated_tn1 = next(
        tn for tn in final_thing_nodes if tn.external_id == "Wasserwerk1_Anlage1_Hochbehaelter1"
    )
    assert (
        updated_tn1.meta_data["capacity"] == "5200"
    ), "Expected updated capacity 5200 for Hochbehälter 1"
    assert updated_tn1.meta_data["description"] == (
        "Erhöhte Wasserspeicherungskapazität für Hochbehälter 1"
    )

    updated_tn2 = next(
        tn for tn in final_thing_nodes if tn.external_id == "Wasserwerk1_Anlage1_Hochbehaelter2"
    )
    assert (
        updated_tn2.meta_data["capacity"] == "6100"
    ), "Expected updated capacity 6100 for Hochbehälter 2"
    assert updated_tn2.meta_data["description"] == (
        "Erhöhte Wasserspeicherungskapazität für Hochbehälter 2"
    )


def verify_associations(session):
    # Fetch all associations between ThingNodes and Sources/Sinks from the database
    source_associations = session.query(thingnode_source_association).all()
    sink_associations = session.query(thingnode_sink_association).all()

    # Define the expected associations between ThingNodes and Sources
    expected_source_associations = [
        ("Wasserwerk1_Anlage1_Hochbehaelter1", "Energieverbraeuche_Pumpensystem_Hochbehaelter"),
        ("Wasserwerk1_Filteranlage", "Energieverbraeuche_Pumpensystem_Hochbehaelter"),
        ("Wasserwerk1_Anlage2_Hochbehaelter1", "Energieverbrauch_Einzelpumpe_Hochbehaelter"),
        ("Wasserwerk1_Filteranlage", "Neue_Energiequelle_Filteranlage"),
    ]

    # Define the expected associations between ThingNodes and Sinks
    expected_sink_associations = [
        (
            "Wasserwerk1_Anlage1_Hochbehaelter1",
            "Anomaly_Score_Energieverbraeuche_Pumpensystem_Hochbehaelter",
        ),
        (
            "Wasserwerk1_Anlage1_Hochbehaelter2",
            "Anomaly_Score_Energieverbraeuche_Pumpensystem_Hochbehaelter",
        ),
        (
            "Wasserwerk1_Anlage2_Hochbehaelter1",
            "Anomaly_Score_Energieverbrauch_Einzelpumpe_Hochbehaelter",
        ),
        (
            "Wasserwerk1_Anlage2_Hochbehaelter2",
            "Anomaly_Score_Energieverbrauch_Einzelpumpe_Hochbehaelter",
        ),
        ("Wasserwerk1_Filteranlage", "Anomaly_Score_Energieverbrauch_Einzelpumpe_Hochbehaelter"),
    ]

    # Verify that each expected Source association exists in the database
    for tn_external_id, source_external_id in expected_source_associations:
        tn_id = (
            session.query(ThingNodeOrm.id)
            .filter(ThingNodeOrm.external_id == tn_external_id)
            .one()[0]
        )
        source_id = (
            session.query(SourceOrm.id).filter(SourceOrm.external_id == source_external_id).one()[0]
        )
        assert (tn_id, source_id) in [
            (assoc.thing_node_id, assoc.source_id) for assoc in source_associations
        ], (
            f"Expected association between ThingNode {tn_external_id}"
            " and Source {source_external_id} not found"
        )

    # Verify that each expected Sink association exists in the database
    for tn_external_id, sink_external_id in expected_sink_associations:
        tn_id = (
            session.query(ThingNodeOrm.id)
            .filter(ThingNodeOrm.external_id == tn_external_id)
            .one()[0]
        )
        sink_id = session.query(SinkOrm.id).filter(SinkOrm.external_id == sink_external_id).one()[0]
        assert (tn_id, sink_id) in [
            (assoc.thing_node_id, assoc.sink_id) for assoc in sink_associations
        ], (
            f"Expected association between ThingNode {tn_external_id}"
            f" and Sink {sink_external_id} not found"
        )


@pytest.mark.usefixtures("_db_empty_database")
def test_update_structure_from_file():
    # This test specifically checks the insert functionality of the update_structure function.
    # It starts with an empty database and verifies that the structure from the JSON file is
    # correctly inserted into the database.

    # Path to the JSON file containing the test structure
    file_path = "tests/structure/data/db_test_structure.json"

    # Ensure the database is empty at the beginning
    with get_session()() as session:
        assert session.query(ElementTypeOrm).count() == 0
        assert session.query(ThingNodeOrm).count() == 0
        assert session.query(SourceOrm).count() == 0
        assert session.query(SinkOrm).count() == 0

    # Load structure from the file and update the database
    update_structure_from_file(file_path)

    # Verify that the structure was correctly inserted
    with get_session()() as session:
        assert session.query(ElementTypeOrm).count() == 3
        assert session.query(ThingNodeOrm).count() == 7
        assert session.query(SourceOrm).count() == 3
        assert session.query(SinkOrm).count() == 3

        # Example check for a specific ElementType
        wasserwerk_typ = session.query(ElementTypeOrm).filter_by(external_id="Wasserwerk_Typ").one()
        assert wasserwerk_typ.name == "Wasserwerk"
        assert wasserwerk_typ.description == "Elementtyp für Wasserwerke"

        # Example check for a specific ThingNode
        wasserwerk1 = session.query(ThingNodeOrm).filter_by(external_id="Wasserwerk1").one()
        assert wasserwerk1.name == "Wasserwerk 1"
        assert wasserwerk1.meta_data["location"] == "Hauptstandort"

        # Example check for a specific Source
        source = (
            session.query(SourceOrm)
            .filter_by(external_id="Energieverbraeuche_Pumpensystem_Hochbehaelter")
            .one()
        )
        assert source.name == "Energieverbräuche des Pumpensystems in Hochbehälter"
        assert source.meta_data["1010001"]["unit"] == "kW/h"

        # Example check for a specific Sink
        sink = (
            session.query(SinkOrm)
            .filter_by(external_id="Anomaly_Score_Energieverbraeuche_Pumpensystem_Hochbehaelter")
            .one()
        )
        assert (
            sink.name == "Anomaly Score für die Energieverbräuche des Pumpensystems in Hochbehälter"
        )


@pytest.mark.usefixtures("_db_test_structure")
def test_update_structure_no_elements_deleted():
    # This test ensures that no elements are deleted when updating the structure
    # with a new JSON file that omits some elements. It verifies that the total number of elements
    # remains unchanged and that specific elements from the original structure are still present.

    # Define paths to the JSON files
    old_file_path = "tests/structure/data/db_test_structure.json"
    new_file_path = "tests/structure/data/db_test_incomplete_structure.json"

    # Load initial structure from JSON file
    initial_structure: CompleteStructure = load_structure_from_json_file(old_file_path)

    # Load updated structure from new JSON file
    updated_structure: CompleteStructure = load_structure_from_json_file(new_file_path)

    # Update the structure in the database with new structure
    orm_update_structure(updated_structure)

    # Verify structure after update
    with get_session()() as session:
        # Check the number of elements after update
        assert session.query(ElementTypeOrm).count() == len(initial_structure.element_types)
        assert session.query(ThingNodeOrm).count() == len(initial_structure.thing_nodes)
        assert session.query(SourceOrm).count() == len(initial_structure.sources)
        assert session.query(SinkOrm).count() == len(initial_structure.sinks)

        # Verify specific elements from the initial structure are still present
        # Element Types
        for element_type in initial_structure.element_types:
            assert (
                session.query(ElementTypeOrm)
                .filter_by(external_id=element_type.external_id)
                .count()
                == 1
            )

        # Thing Nodes
        for thing_node in initial_structure.thing_nodes:
            assert (
                session.query(ThingNodeOrm).filter_by(external_id=thing_node.external_id).count()
                == 1
            )

        # Sources
        for source in initial_structure.sources:
            assert session.query(SourceOrm).filter_by(external_id=source.external_id).count() == 1

        # Sinks
        for sink in initial_structure.sinks:
            assert session.query(SinkOrm).filter_by(external_id=sink.external_id).count() == 1


@pytest.mark.usefixtures("_db_empty_database")
def test_is_database_empty_when_empty(mocked_clean_test_db_session):
    assert orm_is_database_empty(), "Database should be empty but is not."


@pytest.mark.usefixtures("_db_test_structure")
def test_is_database_empty_when_not_empty(mocked_clean_test_db_session):
    assert not orm_is_database_empty(), "Database should not be empty but it is."


@pytest.mark.usefixtures("_db_test_unordered_structure")
def test_sort_thing_nodes_from_db(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        # Fetch all thing nodes from the database
        thing_nodes_in_db = fetch_all_thing_nodes(session)

        # Create a mapping of thing nodes for the sort function
        existing_thing_nodes = {tn.stakeholder_key + tn.external_id: tn for tn in thing_nodes_in_db}

        # Run the sort function
        sorted_nodes_by_level = sort_thing_nodes_from_db(thing_nodes_in_db, existing_thing_nodes)

        # Check that the nodes are sorted into the correct levels
        # Level 0 should contain the root node "Wasserwerk 1"
        assert len(sorted_nodes_by_level[0]) == 1
        assert sorted_nodes_by_level[0][0].name == "Wasserwerk 1"

        # Level 1 should contain "Anlage 1" and "Anlage 2"
        assert len(sorted_nodes_by_level[1]) == 2
        level_1_names = {node.name for node in sorted_nodes_by_level[1]}
        assert level_1_names == {"Anlage 1", "Anlage 2"}

        # Level 2 should contain the Hochbehälter nodes
        assert len(sorted_nodes_by_level[2]) == 4
        level_2_names = {node.name for node in sorted_nodes_by_level[2]}
        assert level_2_names == {
            "Hochbehälter 1 Anlage 1",
            "Hochbehälter 2 Anlage 1",
            "Hochbehälter 1 Anlage 2",
            "Hochbehälter 2 Anlage 2",
        }

        # Ensure the nodes are sorted within their levels by external_id
        expected_level_1_order = ["Anlage 1", "Anlage 2"]
        actual_level_1_order = [node.name for node in sorted_nodes_by_level[1]]
        assert actual_level_1_order == expected_level_1_order

        expected_level_2_order = [
            "Hochbehälter 1 Anlage 1",
            "Hochbehälter 2 Anlage 1",
            "Hochbehälter 1 Anlage 2",
            "Hochbehälter 2 Anlage 2",
        ]
        actual_level_2_order = [node.name for node in sorted_nodes_by_level[2]]
        assert actual_level_2_order == expected_level_2_order

        # Ensure the condition where a parent_node_id is not initially in children_by_node_id
        # Create a new node with a parent_node_id that isn't in children_by_node_id
        orphan_node = ThingNode(
            external_id="Orphan_Hochbehälter",
            name="Orphan Hochbehälter",
            stakeholder_key="GW",
            parent_node_id=uuid.uuid4(),  # Ensure this UUID does not match any existing node
            element_type_id=uuid.uuid4(),
            element_type_external_id="Hochbehaelter_Typ",  # Required element_type_external_id
            meta_data={},
        )

        thing_nodes_in_db.append(orphan_node)

        # Re-run the sort function with the orphan node added
        sorted_nodes_by_level_with_orphan = sort_thing_nodes_from_db(
            thing_nodes_in_db, existing_thing_nodes
        )

        # Verify that the orphan node is not placed in any level
        # (since it doesn't have a valid parent in the set)
        orphan_in_levels = any(
            orphan_node in level_nodes for level_nodes in sorted_nodes_by_level_with_orphan.values()
        )
        assert not orphan_in_levels, "Orphan node should not be placed in any level."


def test_fill_source_sink_associations_db(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        # Load a complete structure from JSON for testing
        complete_structure = load_structure_from_json_file(
            "tests/structure/data/db_test_structure.json"
        )

        # Add a Source with no associated ThingNodes to the structure
        orphan_source = Source(
            external_id="Orphan_Source",
            stakeholder_key="GW",
            name="Orphan Source",
            type="multitsframe",
            adapter_key="sql-adapter",
            source_id="improvt_timescale_db/ts_table/ts_values",
            meta_data={"unit": "kW/h", "description": "Orphan Source"},
            preset_filters={"metrics": "1010005"},
            passthrough_filters=[],
            thing_node_external_ids=[],  # No associated ThingNodes
        )
        complete_structure.sources.append(orphan_source)

        # Add a Sink with no associated ThingNodes to the structure
        orphan_sink = Sink(
            external_id="Orphan_Sink",
            stakeholder_key="GW",
            name="Orphan Sink",
            type="multitsframe",
            adapter_key="sql-adapter",
            sink_id="improvt_timescale_db/ts_table/ts_values",
            meta_data={"description": "Orphan Sink"},
            preset_filters={"metrics": "10010005"},
            passthrough_filters=[],
            thing_node_external_ids=[],  # No associated ThingNodes
        )
        complete_structure.sinks.append(orphan_sink)

        # Add an entity to CompleteStructure that doesn't exist in the database
        missing_source = Source(
            external_id="Missing_Source",
            stakeholder_key="GW",
            name="Missing Source",
            type="multitsframe",
            adapter_key="sql-adapter",
            source_id="improvt_timescale_db/ts_table/ts_values",
            meta_data={"unit": "kW/h", "description": "Missing Source"},
            preset_filters={"metrics": "1010006"},
            passthrough_filters=[],
            thing_node_external_ids=["Wasserwerk1"],  # Associated with an existing ThingNode
        )
        complete_structure.sources.append(missing_source)

        # Add orphan source and sink to the session
        session.add(orphan_source.to_orm_model())
        session.add(orphan_sink.to_orm_model())
        session.commit()

        # Fill the associations in the database
        fill_source_sink_associations_db(complete_structure, session)

        # Check that the Orphan Source and Sink were skipped during association processing
        orphan_source_in_db = (
            session.query(SourceOrm).filter_by(external_id="Orphan_Source").one_or_none()
        )
        orphan_sink_in_db = (
            session.query(SinkOrm).filter_by(external_id="Orphan_Sink").one_or_none()
        )

        assert orphan_source_in_db is not None, "Orphan Source should exist in the database."
        assert orphan_sink_in_db is not None, "Orphan Sink should exist in the database."

        # Verify that no associations exist for the Orphan Source and Sink
        orphan_source_associations = (
            session.query(thingnode_source_association)
            .filter_by(source_id=orphan_source_in_db.id)
            .all()
        )
        orphan_sink_associations = (
            session.query(thingnode_sink_association).filter_by(sink_id=orphan_sink_in_db.id).all()
        )

        assert len(orphan_source_associations) == 0, "Orphan Source should have no associations."
        assert len(orphan_sink_associations) == 0, "Orphan Sink should have no associations."

        # Verify that the "Missing Source" was not associated due to it not existing in the database
        missing_source_associations = (
            session.query(thingnode_source_association)
            .join(SourceOrm, thingnode_source_association.c.source_id == SourceOrm.id)
            .filter(SourceOrm.external_id == "Missing_Source")
            .all()
        )

        assert len(missing_source_associations) == 0, (
            "Missing Source should not create any associations"
            " because it doesn't exist in the database."
        )

        # Verify that the "Missing Source" was indeed skipped in processing
        missing_source_in_db = (
            session.query(SourceOrm).filter_by(external_id="Missing_Source").one_or_none()
        )
        assert missing_source_in_db is None, "Missing Source should not exist in the database."


def test_fetch_existing_records_exception_handling(mocked_clean_test_db_session):
    class InvalidModel:
        # This is a dummy class that does not correspond to any database model
        pass

    with pytest.raises(SQLAlchemyError), mocked_clean_test_db_session() as session:
        # Attempt to fetch records using an invalid model class,
        # which should raise an exception
        fetch_existing_records(session, InvalidModel)


def test_update_existing_elements_exception_handling(mocked_clean_test_db_session):
    class InvalidModel:
        # This is a dummy class that does not correspond to any database model
        pass

    existing_elements = {}

    with pytest.raises(SQLAlchemyError), mocked_clean_test_db_session() as session:
        # Attempt to update elements using an invalid model class,
        # which should raise an exception
        update_existing_elements(session, InvalidModel, existing_elements)

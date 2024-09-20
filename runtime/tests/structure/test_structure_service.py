import json
import uuid
from sqlite3 import Connection as SQLite3Connection

import pytest
from sqlalchemy import event
from sqlalchemy.future.engine import Engine

from hetdesrun.persistence.db_engine_and_session import get_session
from hetdesrun.persistence.structure_service_dbmodels import (
    SinkOrm,
    SourceOrm,
    ThingNodeOrm,
)
from hetdesrun.structure.db.exceptions import DBIntegrityError, DBNotFoundError
from hetdesrun.structure.db.orm_service import (
    fetch_all_element_types,
    fetch_all_sinks,
    fetch_all_sources,
    fetch_all_thing_nodes,
)
from hetdesrun.structure.models import CompleteStructure, Sink, Source, ThingNode
from hetdesrun.structure.structure_service import (
    delete_structure,
    get_all_sinks_from_db,
    get_all_sources_from_db,
    get_all_thing_nodes_from_db,
    get_children,
    get_collection_of_sinks_from_db,
    get_collection_of_sources_from_db,
    get_collection_of_thingnodes_from_db,
    get_single_sink_from_db,
    get_single_source_from_db,
    get_single_thingnode_from_db,
    is_database_empty,
    update_structure,
)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection: SQLite3Connection, connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@pytest.mark.usefixtures("_db_test_structure")
def test_get_children():
    with get_session()() as session, session.begin():
        # Test for root level
        root_node = get_node_by_name(session, "Waterworks 1")
        children, sources, sinks = get_children(root_node.id)
        verify_children(children, {"Plant 1", "Plant 2"}, 2)
        verify_sources(sources, ["Energy consumption of the waterworks"], 1)
        verify_sinks(sinks, ["Anomaly Score for the energy consumption of the waterworks"], 1)

        # Test for first child level under "Plant 1"
        parent_node = get_node_by_name(session, "Plant 1")
        children, sources, sinks = get_children(parent_node.id)
        verify_children(children, {"Storage Tank 1, Plant 1", "Storage Tank 2, Plant 1"}, 2)
        verify_sources(sources, [], 0)
        verify_sinks(sinks, [], 0)

        # Test for second child level under "Storage Tank 1, Plant 1"
        parent_node = get_node_by_name(session, "Storage Tank 1, Plant 1")
        children, sources, sinks = get_children(parent_node.id)
        verify_children(children, set(), 0)
        verify_sources(sources, ["Energy usage of the pump system in Storage Tank"], 1)
        verify_sinks(
            sinks, ["Anomaly Score for the energy usage of the pump system in Storage Tank"], 1
        )

        # Test for second child level under "Storage Tank 2, Plant 1"
        parent_node = get_node_by_name(session, "Storage Tank 2, Plant 1")
        children, sources, sinks = get_children(parent_node.id)
        verify_children(children, set(), 0)
        verify_sources(sources, ["Energy consumption of a single pump in Storage Tank"], 1)
        verify_sinks(
            sinks, ["Anomaly Score for the energy usage of the pump system in Storage Tank"], 1
        )

        # Test for second child level under "Storage Tank 1, Plant 2"
        parent_node = get_node_by_name(session, "Storage Tank 1, Plant 2")
        children, sources, sinks = get_children(parent_node.id)
        verify_children(children, set(), 0)
        verify_sources(sources, ["Energy consumption of a single pump in Storage Tank"], 1)
        verify_sinks(
            sinks, ["Anomaly Score for the energy consumption of a single pump in Storage Tank"], 1
        )

        # Test for second child level under "Storage Tank 2, Plant 2"
        parent_node = get_node_by_name(session, "Storage Tank 2, Plant 2")
        children, sources, sinks = get_children(parent_node.id)
        verify_children(children, set(), 0)
        verify_sources(sources, ["Energy usage of the pump system in Storage Tank"], 1)
        verify_sinks(
            sinks, ["Anomaly Score for the energy consumption of a single pump in Storage Tank"], 1
        )


def get_node_by_name(session, name: str) -> ThingNodeOrm:
    """Helper function to fetch a ThingNode by name."""
    all_nodes = fetch_all_thing_nodes(session)
    node = next((node for node in all_nodes if node.name == name), None)
    assert node is not None, f"Expected node '{name}' not found"
    return node


def verify_children(children: list[ThingNode], expected_names: set, expected_count: int):
    """Helper function to verify the children nodes."""
    assert (
        len(children) == expected_count
    ), f"Expected {expected_count} children, found {len(children)}"
    children_names = {child.name for child in children}
    assert children_names == expected_names, f"Unexpected child names: {children_names}"


def verify_sources(sources: list[Source], expected_names: list, expected_count: int):
    """Helper function to verify the sources."""
    assert (
        len(sources) == expected_count
    ), f"Expected {expected_count} source(s), found {len(sources)}"
    if expected_count > 0:
        assert [
            source.name for source in sources
        ] == expected_names, f"Unexpected source names: {[source.name for source in sources]}"


def verify_sinks(sinks: list[Sink], expected_names: list, expected_count: int):
    """Helper function to verify the sinks."""
    assert len(sinks) == expected_count, f"Expected {expected_count} sink(s), found {len(sinks)}"
    if expected_count > 0:
        assert [
            sink.name for sink in sinks
        ] == expected_names, f"Unexpected sink names: {[sink.name for sink in sinks]}"


def test_complete_structure_object_creation():
    with open("tests/structure/data/db_test_structure.json") as file:
        data = json.load(file)
    cs = CompleteStructure(**data)

    assert len(cs.thing_nodes) == 7
    assert len(cs.element_types) == 3
    assert len(cs.sources) == 3
    assert len(cs.sinks) == 3

    tn_names = [tn.name for tn in cs.thing_nodes]
    expected_tn_names = [tn["name"] for tn in data["thing_nodes"]]
    assert all(name in tn_names for name in expected_tn_names)


@pytest.mark.usefixtures("_db_empty_database")
def test_is_database_empty_when_empty(mocked_clean_test_db_session):
    assert is_database_empty(), "Database should be empty but is not."


@pytest.mark.usefixtures("_db_test_structure")
def test_is_database_empty_when_not_empty(mocked_clean_test_db_session):
    assert not is_database_empty(), "Database should not be empty but it is."


@pytest.mark.usefixtures("_db_test_structure")
def test_delete_structure(mocked_clean_test_db_session):
    # Ensure the structure exists before deletion
    with mocked_clean_test_db_session() as session:
        initial_thing_nodes = fetch_all_thing_nodes(session)
        initial_sources = fetch_all_sources(session)
        initial_sinks = fetch_all_sinks(session)
        initial_element_types = fetch_all_element_types(session)

        assert len(initial_thing_nodes) > 0, "Expected some thing nodes before deletion"
        assert len(initial_sources) > 0, "Expected some sources before deletion"
        assert len(initial_sinks) > 0, "Expected some sinks before deletion"
        assert len(initial_element_types) > 0, "Expected some element types before deletion"

        # Perform the deletion
        delete_structure()

        # Verify everything is deleted
        remaining_thing_nodes = fetch_all_thing_nodes(session)
        remaining_sources = fetch_all_sources(session)
        remaining_sinks = fetch_all_sinks(session)
        remaining_element_types = fetch_all_element_types(session)

        assert len(remaining_thing_nodes) == 0, "Expected no thing nodes after deletion"
        assert len(remaining_sources) == 0, "Expected no sources after deletion"
        assert len(remaining_sinks) == 0, "Expected no sinks after deletion"
        assert len(remaining_element_types) == 0, "Expected no element types after deletion"


@pytest.mark.usefixtures("_db_empty_database")
def test_update_structure(mocked_clean_test_db_session):
    # This test checks both the insert and update functionality of the update_structure function.
    # It starts with an empty database, loads a complete structure from a JSON file, and then
    # updates the database with this structure. The test then verifies that the structure
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
        thing_nodes = fetch_all_thing_nodes(session)
        sources = fetch_all_sources(session)
        sinks = fetch_all_sinks(session)
        element_types = fetch_all_element_types(session)

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
        # The `next` function retrieves the first matching ThingNode or returns None if not found
        waterworks_node = next((tn for tn in thing_nodes if tn.name == "Waterworks 1"), None)
        assert waterworks_node is not None, "Expected 'Waterworks 1' node not found"

        # Check if the 'Energy consumption of a single pump
        # in Storage Tank' Source was correctly inserted
        # The `next` function retrieves the first matching Source or returns None if not found
        source = next(
            (s for s in sources if s.name == "Energy consumption of a single pump in Storage Tank"),
            None,
        )
        assert (
            source is not None
        ), "Expected source 'Energy consumption of a single pump in Storage Tank' not found"

        # Check if the 'Anomaly Score for the energy usage of the pump system
        # in Storage Tank' Sink was correctly inserted
        # The `next` function retrieves the first matching Sink or returns None if not found
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


@pytest.mark.usefixtures("_db_test_structure")
def test_get_single_thingnode_from_db(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        # Fetch an existing ThingNode ID
        existing_tn = session.query(ThingNodeOrm).first()
        assert existing_tn is not None, "No ThingNode found in the test database."

        # Test retrieving the ThingNode by ID
        fetched_tn = get_single_thingnode_from_db(existing_tn.id)
        assert fetched_tn.id == existing_tn.id, "Fetched ThingNode ID does not match."

        # Test that a non-existent ThingNode raises a DBNotFoundError
        non_existent_id = uuid.uuid4()
        with pytest.raises(DBNotFoundError):
            get_single_thingnode_from_db(non_existent_id)


@pytest.mark.usefixtures("_db_test_structure")
def test_get_all_thing_nodes_from_db(mocked_clean_test_db_session):
    # Open a session to interact with the database
    with mocked_clean_test_db_session() as session:
        # Ensure the database is not empty and contains ThingNodes
        assert session.query(ThingNodeOrm).count() > 0, "Expected non-empty ThingNodes table"

        # Fetch all ThingNodes using the function
        thing_nodes = get_all_thing_nodes_from_db()

        # Verify that the number of ThingNodes fetched matches the number in the database
        assert (
            len(thing_nodes) == session.query(ThingNodeOrm).count()
        ), "Mismatch between number of ThingNodes fetched and number in the database"

        # Check that specific ThingNodes exist and have expected properties
        expected_thing_nodes = [
            {"external_id": "Waterworks1", "name": "Waterworks 1"},
            {"external_id": "Waterworks1_Plant1", "name": "Plant 1"},
            {"external_id": "Waterworks1_Plant2", "name": "Plant 2"},
        ]

        for expected_tn in expected_thing_nodes:
            found = any(
                tn.external_id == expected_tn["external_id"] and tn.name == expected_tn["name"]
                for tn in thing_nodes
            )
            assert found, (
                f"Expected ThingNode with external_id {expected_tn['external_id']} "
                f"and name {expected_tn['name']} not found"
            )


@pytest.mark.usefixtures("_db_test_structure")
def test_get_collection_of_thingnodes_from_db(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        # Fetch a list of existing ThingNode IDs
        existing_tns = session.query(ThingNodeOrm).limit(3).all()
        assert len(existing_tns) == 3, "Expected at least 3 ThingNodes in the test database."
        existing_tn_ids = [tn.id for tn in existing_tns]

        # Test retrieving a collection of ThingNodes by their IDs
        fetched_tns = get_collection_of_thingnodes_from_db(existing_tn_ids)
        assert len(fetched_tns) == 3, "Expected to fetch 3 ThingNodes."
        for tn_id in existing_tn_ids:
            assert (
                tn_id in fetched_tns
            ), f"ThingNode with ID {tn_id} not found in fetched collection."

        # Test that a non-existent ThingNode raises a DBNotFoundError
        non_existent_id = uuid.uuid4()
        with pytest.raises(DBNotFoundError):
            get_collection_of_thingnodes_from_db(existing_tn_ids + [non_existent_id])


@pytest.mark.usefixtures("_db_test_structure")
def test_get_single_source_from_db(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        # Fetch an existing Source ID from the database
        existing_source = session.query(SourceOrm).first()
        assert existing_source is not None, "Expected at least one Source in the test database."
        existing_source_id = existing_source.id

        # Test retrieving the Source by its ID
        fetched_source = get_single_source_from_db(existing_source_id)
        assert fetched_source.id == existing_source_id, f"Expected Source ID {existing_source_id}."

        # Test that a non-existent Source raises a DBNotFoundError
        non_existent_id = uuid.uuid4()
        with pytest.raises(DBNotFoundError):
            get_single_source_from_db(non_existent_id)


@pytest.mark.usefixtures("_db_test_structure")
def test_get_all_sources_from_db(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        # Fetch all sources directly from the database using the ORM for comparison
        expected_sources = session.query(SourceOrm).all()

    # Use the get_all_sources_from_db function to fetch all sources
    fetched_sources = get_all_sources_from_db()

    # Verify that the number of sources fetched matches the expected number
    assert len(fetched_sources) == len(expected_sources), (
        f"Expected {len(expected_sources)} sources, " f"but fetched {len(fetched_sources)} sources."
    )

    # Verify that all sources fetched match the expected sources
    for expected_source in expected_sources:
        matched_source = next(
            (source for source in fetched_sources if source.id == expected_source.id), None
        )
        assert (
            matched_source is not None
        ), f"Source with ID {expected_source.id} was expected but not found."


@pytest.mark.usefixtures("_db_test_structure")
def test_get_collection_of_sources_from_db(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        # Fetch some specific sources directly from the database
        expected_sources = session.query(SourceOrm).limit(2).all()
        expected_source_ids = [source.id for source in expected_sources]

    # Use the get_collection_of_sources_from_db function to fetch the sources
    fetched_sources = get_collection_of_sources_from_db(expected_source_ids)

    # Verify that the number of sources fetched matches the expected number
    assert len(fetched_sources) == len(expected_source_ids), (
        f"Expected {len(expected_source_ids)} sources, "
        f"but fetched {len(fetched_sources)} sources."
    )

    # Verify that each expected source is in the fetched sources dictionary
    for expected_source in expected_sources:
        assert (
            expected_source.id in fetched_sources
        ), f"Source with ID {expected_source.id} was expected but not found in the fetched sources."

        # Verify that the fetched source matches the expected source
        fetched_source = fetched_sources[expected_source.id]
        assert (
            fetched_source.external_id == expected_source.external_id
        ), f"Source with ID {expected_source.id} has mismatched external_id."
        assert (
            fetched_source.name == expected_source.name
        ), f"Source with ID {expected_source.id} has mismatched name."


@pytest.mark.usefixtures("_db_test_structure")
def test_get_single_sink_from_db(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        # Fetch a specific sink directly from the database
        expected_sink = session.query(SinkOrm).first()
        assert expected_sink is not None, "No sinks found in the test database."

    # Use the get_single_sink_from_db function to fetch the sink
    fetched_sink = get_single_sink_from_db(expected_sink.id)

    # Verify that the fetched sink matches the expected sink
    assert (
        fetched_sink.id == expected_sink.id
    ), f"Expected sink ID {expected_sink.id}, but got {fetched_sink.id}."
    assert (
        fetched_sink.external_id == expected_sink.external_id
    ), f"Expected external_id '{expected_sink.external_id}', but got '{fetched_sink.external_id}'."
    assert (
        fetched_sink.name == expected_sink.name
    ), f"Expected name '{expected_sink.name}', but got '{fetched_sink.name}'."

    # Test that fetching a non-existent sink raises DBNotFoundError
    non_existent_sink_id = uuid.UUID("00000000-0000-0000-0000-000000000000")
    with pytest.raises(DBNotFoundError, match=f"No Sink found for ID {non_existent_sink_id}"):
        get_single_sink_from_db(non_existent_sink_id)


@pytest.mark.usefixtures("_db_test_structure")
def test_get_all_sinks_from_db(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        # Fetch all sinks directly from the database
        expected_sinks = session.query(SinkOrm).all()
        assert len(expected_sinks) > 0, "No sinks found in the test database."

    # Use the get_all_sinks_from_db function to fetch all sinks
    fetched_sinks = get_all_sinks_from_db()

    # Verify that the number of fetched sinks matches the expected number
    assert len(fetched_sinks) == len(
        expected_sinks
    ), f"Expected {len(expected_sinks)} sinks, but got {len(fetched_sinks)}."

    # Verify that each fetched sink matches the expected sinks
    for expected_sink in expected_sinks:
        found_sink = next((sink for sink in fetched_sinks if sink.id == expected_sink.id), None)
        assert found_sink is not None, f"Expected sink with ID {expected_sink.id} not found."
        assert found_sink.external_id == expected_sink.external_id, (
            f"Expected external_id '{expected_sink.external_id}',"
            f" but got '{found_sink.external_id}'."
        )
        assert (
            found_sink.name == expected_sink.name
        ), f"Expected name '{expected_sink.name}', but got '{found_sink.name}'."


@pytest.mark.usefixtures("_db_test_structure")
def test_get_collection_of_sinks_from_db(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        # Fetch some sinks directly from the database
        sinks_in_db = session.query(SinkOrm).limit(2).all()
        sink_ids = [sink.id for sink in sinks_in_db]
        assert len(sink_ids) > 0, "No sinks found in the test database."

    # Use the get_collection_of_sinks_from_db function to fetch sinks by their IDs
    fetched_sinks = get_collection_of_sinks_from_db(sink_ids)

    # Verify that the number of fetched sinks matches the expected number
    assert len(fetched_sinks) == len(
        sink_ids
    ), f"Expected {len(sink_ids)} sinks, but got {len(fetched_sinks)}."

    # Verify that each fetched sink matches the expected sinks
    for expected_sink in sinks_in_db:
        fetched_sink = fetched_sinks.get(expected_sink.id)
        assert fetched_sink is not None, f"Expected sink with ID {expected_sink.id} not found."
        assert fetched_sink.external_id == expected_sink.external_id, (
            f"Expected external_id '{expected_sink.external_id}', "
            f"but got '{fetched_sink.external_id}'."
        )
        assert (
            fetched_sink.name == expected_sink.name
        ), f"Expected name '{expected_sink.name}', but got '{fetched_sink.name}'."


def test_circular_tn_relation(mocked_clean_test_db_session):
    circular_data = {
        "element_types": [
            {
                "external_id": "Type1",
                "stakeholder_key": "SK1",
                "name": "Type 1",
            }
        ],
        "thing_nodes": [
            {
                "external_id": "Node1",
                "stakeholder_key": "SK1",
                "name": "Node 1",
                "parent_external_node_id": "Node3",  # Circular reference
                "element_type_external_id": "Type1",
            },
            {
                "external_id": "Node2",
                "stakeholder_key": "SK1",
                "name": "Node 2",
                "parent_external_node_id": "Node1",
                "element_type_external_id": "Type1",
            },
            {
                "external_id": "Node3",
                "stakeholder_key": "SK1",
                "name": "Node 3",
                "parent_external_node_id": "Node2",
                "element_type_external_id": "Type1",
            },
        ],
    }

    with pytest.raises(ValueError, match="Circular reference detected in node"):
        CompleteStructure(**circular_data)


def test_update_with_conflicting_stakeholder_key(mocked_clean_test_db_session):
    # Initial Structure: A thing node with a specific external_id and stakeholder_key
    initial_structure = {
        "element_types": [
            {
                "external_id": "Type1",
                "stakeholder_key": "SK1",
                "name": "Type 1",
            }
        ],
        "thing_nodes": [
            {
                "external_id": "Node1",
                "stakeholder_key": "SK1",
                "name": "Node 1",
                "parent_external_node_id": None,
                "element_type_external_id": "Type1",
            }
        ],
    }

    # Updating Structure: Same external_id but with a different stakeholder_key
    conflicting_structure = {
        "element_types": [
            {
                "external_id": "Type1",
                "stakeholder_key": "SK2",
                "name": "Type 1",
            }
        ],
        "thing_nodes": [
            {
                "external_id": "Node1",
                "stakeholder_key": "SK2",
                "name": "Node 1 - Conflicting Stakeholder Key",
                "parent_external_node_id": None,
                "element_type_external_id": "Type1",
            }
        ],
    }

    update_structure(CompleteStructure(**initial_structure))  # Insert initial Structure

    # Verify initial structure is in the database
    thing_nodes = get_all_thing_nodes_from_db()
    assert len(thing_nodes) == 1
    assert thing_nodes[0].external_id == "Node1"
    assert thing_nodes[0].stakeholder_key == "SK1"

    # Attempt to create the conflicting structure with validation error check
    with pytest.raises(
        DBIntegrityError,
        match=(
            r"Integrity Error while updating or inserting the structure:.*"
            r"UNIQUE constraint failed.*element_type.name"
        ),
    ):
        update_structure(CompleteStructure(**conflicting_structure))


def test_stakeholder_key_consistency(mocked_clean_test_db_session):
    # Initial Structure with conflicting stakeholder keys
    conflicting_structure = {
        "element_types": [
            {
                "external_id": "Type1",
                "stakeholder_key": "SK1",
                "name": "Type 1",
            }
        ],
        "thing_nodes": [
            {
                "external_id": "Node1",
                "stakeholder_key": "SK1",
                "name": "Node 1",
                "parent_external_node_id": None,
                "element_type_external_id": "Type1",
            },
            {
                "external_id": "Node2",
                "stakeholder_key": "SK2",  # Inconsistent stakeholder_key
                "name": "Node 2",
                "parent_external_node_id": "Node1",
                "element_type_external_id": "Type1",
            },
        ],
    }

    with pytest.raises(
        ValueError,
        match=r"Inconsistent stakeholder keys found: \{('SK1', 'SK2'|'SK2', 'SK1')\}. "
        r"All stakeholder keys must be consistent across element_types and thing_nodes.",
    ):
        CompleteStructure(**conflicting_structure)


def test_unique_external_id_validation(mocked_clean_test_db_session):
    duplicate_element_types = {
        "element_types": [
            {
                "external_id": "Type1",
                "stakeholder_key": "SK1",
                "name": "Type 1",
            },
            {
                "external_id": "Type1",  # Duplicate
                "stakeholder_key": "SK1",
                "name": "Duplicate Type 1",
            },
        ],
        "thing_nodes": [
            {
                "external_id": "Node1",
                "stakeholder_key": "SK1",
                "name": "Node 1",
                "parent_external_node_id": None,
                "element_type_external_id": "Type1",
            }
        ],
        "sources": [
            {
                "external_id": "Source1",
                "stakeholder_key": "SK1",
                "name": "Source 1",
                "type": "multitsframe",
                "adapter_key": "sql-adapter",
                "source_id": "some_id",
            }
        ],
        "sinks": [
            {
                "external_id": "Sink1",
                "stakeholder_key": "SK1",
                "name": "Sink 1",
                "type": "multitsframe",
                "adapter_key": "sql-adapter",
                "sink_id": "some_id",
            }
        ],
    }

    with pytest.raises(ValueError, match="Duplicate external_id 'Type1' found in element_types"):
        CompleteStructure(**duplicate_element_types)

    duplicate_thing_nodes = {
        "element_types": [
            {
                "external_id": "Type1",
                "stakeholder_key": "SK1",
                "name": "Type 1",
            }
        ],
        "thing_nodes": [
            {
                "external_id": "Node1",
                "stakeholder_key": "SK1",
                "name": "Node 1",
                "parent_external_node_id": None,
                "element_type_external_id": "Type1",
            },
            {
                "external_id": "Node1",  # Duplicate
                "stakeholder_key": "SK1",
                "name": "Duplicate Node 1",
                "parent_external_node_id": None,
                "element_type_external_id": "Type1",
            },
        ],
        "sources": [
            {
                "external_id": "Source1",
                "stakeholder_key": "SK1",
                "name": "Source 1",
                "type": "multitsframe",
                "adapter_key": "sql-adapter",
                "source_id": "some_id",
            }
        ],
        "sinks": [
            {
                "external_id": "Sink1",
                "stakeholder_key": "SK1",
                "name": "Sink 1",
                "type": "multitsframe",
                "adapter_key": "sql-adapter",
                "sink_id": "some_id",
            }
        ],
    }

    with pytest.raises(ValueError, match="Duplicate external_id 'Node1' found in thing_nodes"):
        CompleteStructure(**duplicate_thing_nodes)

    duplicate_sources = {
        "element_types": [
            {
                "external_id": "Type1",
                "stakeholder_key": "SK1",
                "name": "Type 1",
            }
        ],
        "thing_nodes": [
            {
                "external_id": "Node1",
                "stakeholder_key": "SK1",
                "name": "Node 1",
                "parent_external_node_id": None,
                "element_type_external_id": "Type1",
            }
        ],
        "sources": [
            {
                "external_id": "Source1",
                "stakeholder_key": "SK1",
                "name": "Source 1",
                "type": "multitsframe",
                "adapter_key": "sql-adapter",
                "source_id": "some_id",
            },
            {
                "external_id": "Source1",  # Duplicate
                "stakeholder_key": "SK1",
                "name": "Duplicate Source 1",
                "type": "multitsframe",
                "adapter_key": "sql-adapter",
                "source_id": "some_other_id",
            },
        ],
        "sinks": [
            {
                "external_id": "Sink1",
                "stakeholder_key": "SK1",
                "name": "Sink 1",
                "type": "multitsframe",
                "adapter_key": "sql-adapter",
                "sink_id": "some_id",
            }
        ],
    }

    with pytest.raises(ValueError, match="Duplicate external_id 'Source1' found in sources"):
        CompleteStructure(**duplicate_sources)

    duplicate_sinks = {
        "element_types": [
            {
                "external_id": "Type1",
                "stakeholder_key": "SK1",
                "name": "Type 1",
            }
        ],
        "thing_nodes": [
            {
                "external_id": "Node1",
                "stakeholder_key": "SK1",
                "name": "Node 1",
                "parent_external_node_id": None,
                "element_type_external_id": "Type1",
            }
        ],
        "sources": [
            {
                "external_id": "Source1",
                "stakeholder_key": "SK1",
                "name": "Source 1",
                "type": "multitsframe",
                "adapter_key": "sql-adapter",
                "source_id": "some_id",
            }
        ],
        "sinks": [
            {
                "external_id": "Sink1",
                "stakeholder_key": "SK1",
                "name": "Sink 1",
                "type": "multitsframe",
                "adapter_key": "sql-adapter",
                "sink_id": "some_id",
            },
            {
                "external_id": "Sink1",  # Duplicate
                "stakeholder_key": "SK1",
                "name": "Duplicate Sink 1",
                "type": "multitsframe",
                "adapter_key": "sql-adapter",
                "sink_id": "some_other_id",
            },
        ],
    }
    with pytest.raises(ValueError, match="Duplicate external_id 'Sink1' found in sinks"):
        CompleteStructure(**duplicate_sinks)


def test_validate_source_sink_references(mocked_clean_test_db_session):
    invalid_source_structure = {
        "element_types": [
            {
                "external_id": "Type1",
                "stakeholder_key": "SK1",
                "name": "Type 1",
            }
        ],
        "thing_nodes": [
            {
                "external_id": "Node1",
                "stakeholder_key": "SK1",
                "name": "Node 1",
                "parent_external_node_id": None,
                "element_type_external_id": "Type1",
            }
        ],
        "sources": [
            {
                "external_id": "Source1",
                "stakeholder_key": "SK1",
                "name": "Source 1",
                "type": "multitsframe",
                "adapter_key": "sql-adapter",
                "source_id": "some_id",
                "thing_node_external_ids": ["NonExistentNode"],  # invalid reference
            }
        ],
        "sinks": [
            {
                "external_id": "Sink1",
                "stakeholder_key": "SK1",
                "name": "Sink 1",
                "type": "multitsframe",
                "adapter_key": "sql-adapter",
                "sink_id": "some_id",
                "thing_node_external_ids": ["Node1"],  # valid reference
            }
        ],
    }

    with pytest.raises(
        ValueError, match="Source 'Source1' references non-existing ThingNode 'NonExistentNode'"
    ):
        CompleteStructure(**invalid_source_structure)

    invalid_sink_structure = {
        "element_types": [
            {
                "external_id": "Type1",
                "stakeholder_key": "SK1",
                "name": "Type 1",
            }
        ],
        "thing_nodes": [
            {
                "external_id": "Node1",
                "stakeholder_key": "SK1",
                "name": "Node 1",
                "parent_external_node_id": None,
                "element_type_external_id": "Type1",
            }
        ],
        "sources": [
            {
                "external_id": "Source1",
                "stakeholder_key": "SK1",
                "name": "Source 1",
                "type": "multitsframe",
                "adapter_key": "sql-adapter",
                "source_id": "some_id",
                "thing_node_external_ids": ["Node1"],  # valid reference
            }
        ],
        "sinks": [
            {
                "external_id": "Sink1",
                "stakeholder_key": "SK1",
                "name": "Sink 1",
                "type": "multitsframe",
                "adapter_key": "sql-adapter",
                "sink_id": "some_id",
                "thing_node_external_ids": ["NonExistentNode"],  # invalid reference
            }
        ],
    }

    with pytest.raises(
        ValueError, match="Sink 'Sink1' references non-existing ThingNode 'NonExistentNode'"
    ):
        CompleteStructure(**invalid_sink_structure)


def test_validate_passthrough_filters():
    valid_structure = {
        "element_types": [
            {
                "external_id": "Type1",
                "stakeholder_key": "SK1",
                "name": "Type 1",
            }
        ],
        "thing_nodes": [
            {
                "external_id": "Node1",
                "stakeholder_key": "SK1",
                "name": "Node 1",
                "parent_external_node_id": None,
                "element_type_external_id": "Type1",
            }
        ],
        "sources": [
            {
                "external_id": "Source1",
                "stakeholder_key": "SK1",
                "name": "Source 1",
                "type": "multitsframe",
                "adapter_key": "sql-adapter",
                "source_id": "some_id",
                "thing_node_external_ids": ["Node1"],
                "passthrough_filters": [
                    {"name": "timestampFrom", "type": "free_text", "required": True},
                    {"name": "sensorID", "type": "free_text", "required": False},
                ],
            }
        ],
        "sinks": [
            {
                "external_id": "Sink1",
                "stakeholder_key": "SK1",
                "name": "Sink 1",
                "type": "multitsframe",
                "adapter_key": "sql-adapter",
                "sink_id": "some_id",
                "thing_node_external_ids": ["Node1"],
                "passthrough_filters": [
                    {"name": "threshold", "type": "free_text", "required": True}
                ],
            }
        ],
    }

    CompleteStructure(**valid_structure)

    invalid_name_structure = {
        "element_types": [
            {
                "external_id": "Type1",
                "stakeholder_key": "SK1",
                "name": "Type 1",
            }
        ],
        "thing_nodes": [
            {
                "external_id": "Node1",
                "stakeholder_key": "SK1",
                "name": "Node 1",
                "parent_external_node_id": None,
                "element_type_external_id": "Type1",
            }
        ],
        "sources": [
            {
                "external_id": "Source1",
                "stakeholder_key": "SK1",
                "name": "Source 1",
                "type": "multitsframe",
                "adapter_key": "sql-adapter",
                "source_id": "some_id",
                "thing_node_external_ids": ["Node1"],
                "passthrough_filters": [
                    {"type": "free_text", "required": True}  # missing 'name' field
                ],
            }
        ],
        "sinks": [
            {
                "external_id": "Sink1",
                "stakeholder_key": "SK1",
                "name": "Sink 1",
                "type": "multitsframe",
                "adapter_key": "sql-adapter",
                "sink_id": "some_id",
                "thing_node_external_ids": ["Node1"],
                "passthrough_filters": [
                    {"name": "threshold", "type": "free_text", "required": True}
                ],
            }
        ],
    }

    with pytest.raises(ValueError, match="Each passthrough filter must have a 'name' of type str."):
        CompleteStructure(**invalid_name_structure)

    invalid_type_structure = {
        "element_types": [
            {
                "external_id": "Type1",
                "stakeholder_key": "SK1",
                "name": "Type 1",
            }
        ],
        "thing_nodes": [
            {
                "external_id": "Node1",
                "stakeholder_key": "SK1",
                "name": "Node 1",
                "parent_external_node_id": None,
                "element_type_external_id": "Type1",
            }
        ],
        "sources": [
            {
                "external_id": "Source1",
                "stakeholder_key": "SK1",
                "name": "Source 1",
                "type": "multitsframe",
                "adapter_key": "sql-adapter",
                "source_id": "some_id",
                "thing_node_external_ids": ["Node1"],
                "passthrough_filters": [
                    {"name": "timestampFrom", "type": "free_text", "required": True}
                ],
            }
        ],
        "sinks": [
            {
                "external_id": "Sink1",
                "stakeholder_key": "SK1",
                "name": "Sink 1",
                "type": "multitsframe",
                "adapter_key": "sql-adapter",
                "sink_id": "some_id",
                "thing_node_external_ids": ["Node1"],
                "passthrough_filters": [
                    {"name": "threshold", "type": "invalid_type", "required": True}  # invalid type
                ],
            }
        ],
    }

    with pytest.raises(ValueError, match="Each passthrough filter must have a valid 'type'."):
        CompleteStructure(**invalid_type_structure)

    invalid_required_structure = {
        "element_types": [
            {
                "external_id": "Type1",
                "stakeholder_key": "SK1",
                "name": "Type 1",
            }
        ],
        "thing_nodes": [
            {
                "external_id": "Node1",
                "stakeholder_key": "SK1",
                "name": "Node 1",
                "parent_external_node_id": None,
                "element_type_external_id": "Type1",
            }
        ],
        "sources": [
            {
                "external_id": "Source1",
                "stakeholder_key": "SK1",
                "name": "Source 1",
                "type": "multitsframe",
                "adapter_key": "sql-adapter",
                "source_id": "some_id",
                "thing_node_external_ids": ["Node1"],
                "passthrough_filters": [
                    {"name": "timestampFrom", "type": "free_text"}  # missing 'required' field
                ],
            }
        ],
        "sinks": [
            {
                "external_id": "Sink1",
                "stakeholder_key": "SK1",
                "name": "Sink 1",
                "type": "multitsframe",
                "adapter_key": "sql-adapter",
                "sink_id": "some_id",
                "thing_node_external_ids": ["Node1"],
                "passthrough_filters": [
                    {"name": "threshold", "type": "free_text", "required": True}
                ],
            }
        ],
    }

    with pytest.raises(
        ValueError, match="Each passthrough filter must have a 'required' boolean field."
    ):
        CompleteStructure(**invalid_required_structure)

import json
from sqlite3 import Connection as SQLite3Connection

import pytest
from sqlalchemy import event
from sqlalchemy.future.engine import Engine

from hetdesrun.persistence.db_engine_and_session import get_session
from hetdesrun.persistence.structure_service_dbmodels import (
    ThingNodeOrm,
)
from hetdesrun.structure.db.orm_service import (
    fetch_all_element_types,
    fetch_all_sinks,
    fetch_all_sources,
    fetch_all_thing_nodes,
)
from hetdesrun.structure.models import (
    CompleteStructure,
    Sink,
    Source,
    ThingNode,
)
from hetdesrun.structure.structure_service import (
    delete_structure,
    get_children,
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
        root_node = get_node_by_name(session, "Wasserwerk 1")
        children, sources, sinks = get_children(root_node.id)
        verify_children(children, {"Anlage 1", "Anlage 2"}, 2)
        verify_sources(sources, ["Energieverbrauch des Wasserwerks"], 1)
        verify_sinks(sinks, ["Anomaly Score für den Energieverbrauch des Wasserwerks"], 1)

        # Test for first child level under "Anlage 1"
        parent_node = get_node_by_name(session, "Anlage 1")
        children, sources, sinks = get_children(parent_node.id)
        verify_children(children, {"Hochbehälter 1 Anlage 1", "Hochbehälter 2 Anlage 1"}, 2)
        verify_sources(sources, [], 0)
        verify_sinks(sinks, [], 0)

        # Test for second child level under "Hochbehälter 1 Anlage 1"
        parent_node = get_node_by_name(session, "Hochbehälter 1 Anlage 1")
        children, sources, sinks = get_children(parent_node.id)
        verify_children(children, set(), 0)
        verify_sources(sources, ["Energieverbräuche des Pumpensystems in Hochbehälter"], 1)
        verify_sinks(
            sinks, ["Anomaly Score für die Energieverbräuche des Pumpensystems in Hochbehälter"], 1
        )

        # Test for second child level under "Hochbehälter 2 Anlage 1"
        parent_node = get_node_by_name(session, "Hochbehälter 2 Anlage 1")
        children, sources, sinks = get_children(parent_node.id)
        verify_children(children, set(), 0)
        verify_sources(sources, ["Energieverbrauch einer Einzelpumpe in Hochbehälter"], 1)
        verify_sinks(
            sinks, ["Anomaly Score für die Energieverbräuche des Pumpensystems in Hochbehälter"], 1
        )

        # Test for second child level under "Hochbehälter 1 Anlage 2"
        parent_node = get_node_by_name(session, "Hochbehälter 1 Anlage 2")
        children, sources, sinks = get_children(parent_node.id)
        verify_children(children, set(), 0)
        verify_sources(sources, ["Energieverbrauch einer Einzelpumpe in Hochbehälter"], 1)
        verify_sinks(
            sinks, ["Anomaly Score für den Energieverbrauch einer Einzelpumpe in Hochbehälter"], 1
        )

        # Test for second child level under "Hochbehälter 2 Anlage 2"
        parent_node = get_node_by_name(session, "Hochbehälter 2 Anlage 2")
        children, sources, sinks = get_children(parent_node.id)
        verify_children(children, set(), 0)
        verify_sources(sources, ["Energieverbräuche des Pumpensystems in Hochbehälter"], 1)
        verify_sinks(
            sinks, ["Anomaly Score für den Energieverbrauch einer Einzelpumpe in Hochbehälter"], 1
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


@pytest.mark.usefixtures("_db_test_structure")
def test_delete_structure_root(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        delete_structure()

        remaining_thing_nodes = fetch_all_thing_nodes(session)
        assert len(remaining_thing_nodes) == 0

        remaining_sources = fetch_all_sources(session)
        assert len(remaining_sources) == 0

        remaining_sinks = fetch_all_sinks(session)
        assert len(remaining_sinks) == 0

        remaining_element_types = fetch_all_element_types(session)
        assert len(remaining_element_types) == 0


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
    complete_structure = CompleteStructure(**data)

    # Perform the update, which in this case acts as an insert since the database is empty
    update_structure(complete_structure)

    with mocked_clean_test_db_session() as session:
        # Verify the structure was inserted/updated correctly
        thing_nodes = fetch_all_thing_nodes(session)
        sources = fetch_all_sources(session)
        sinks = fetch_all_sinks(session)
        element_types = fetch_all_element_types(session)

        assert len(thing_nodes) == len(
            complete_structure.thing_nodes
        ), "Mismatch in number of thing nodes"
        assert len(sources) == len(complete_structure.sources), "Mismatch in number of sources"
        assert len(sinks) == len(complete_structure.sinks), "Mismatch in number of sinks"
        assert len(element_types) == len(
            complete_structure.element_types
        ), "Mismatch in number of element types"

        # Validate that specific nodes and associations exist
        wasserwerk_node = next((tn for tn in thing_nodes if tn.name == "Wasserwerk 1"), None)
        assert wasserwerk_node is not None, "Expected 'Wasserwerk 1' node not found"

        source = next(
            (s for s in sources if s.name == "Energieverbrauch einer Einzelpumpe in Hochbehälter"),
            None,
        )
        assert (
            source is not None
        ), "Expected source 'Energieverbrauch einer Einzelpumpe in Hochbehälter' not found"

        sink = next(
            (
                s
                for s in sinks
                if s.name
                == "Anomaly Score für die Energieverbräuche des Pumpensystems in Hochbehälter"
            ),
            None,
        )
        assert sink is not None, (
            "Expected sink 'Anomaly Score für die Energieverbräuche"
            " des Pumpensystems in Hochbehälter' not found"
        )

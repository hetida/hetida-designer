import json
from sqlite3 import Connection as SQLite3Connection

import pytest
from sqlalchemy import event
from sqlalchemy.future.engine import Engine

from hetdesrun.persistence.db_engine_and_session import get_session
from hetdesrun.persistence.structure_service_dbmodels import (
    thingnode_sink_association,
    thingnode_source_association,
)
from hetdesrun.structure.db.orm_service import (
    fetch_all_element_types,
    fetch_all_sinks,
    fetch_all_sources,
    fetch_all_thing_nodes,
    insert_structure_from_file,
)
from hetdesrun.structure.models import CompleteStructure
from hetdesrun.structure.structure_service import delete_structure, get_children, is_database_empty


@pytest.fixture()
def _db_test_get_children(mocked_clean_test_db_session):
    file_path = "tests/structure/data/db_test_structure.json"
    insert_structure_from_file(file_path)


@pytest.fixture()
def _db_empty_database(mocked_clean_test_db_session):
    file_path = "tests/structure/data/db_empty_structure.json"
    insert_structure_from_file(file_path)


@pytest.fixture()
def _db_test_structure(mocked_clean_test_db_session):
    file_path = "tests/structure/data/db_test_structure.json"
    insert_structure_from_file(file_path)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection: SQLite3Connection, connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@pytest.mark.usefixtures("_db_test_get_children")
def test_get_children_root(mocked_clean_test_db_session):
    children, sources, sinks = get_children(None)

    assert isinstance(children, list)
    assert isinstance(sources, list)
    assert isinstance(sinks, list)

    wasserwerk = next((child for child in children if child.name == "Wasserwerk 1"), None)
    assert wasserwerk is not None

    assert len(sources) == 0
    assert len(sinks) == 0


@pytest.mark.usefixtures("_db_test_get_children")
def test_get_children_level1():
    with get_session()() as session, session.begin():
        all_nodes = fetch_all_thing_nodes(session)
        root_node = next((node for node in all_nodes if node.name == "Wasserwerk 1"), None)
        assert root_node is not None, "Expected root node 'Wasserwerk 1' not found"

        children, sources, sinks = get_children(root_node.id)

    assert isinstance(children, list)
    assert isinstance(sources, list)
    assert isinstance(sinks, list)

    assert len(children) == 2

    expected_children_names = {"Anlage 1", "Anlage 2"}
    children_names = {child.name for child in children}
    assert children_names == expected_children_names

    assert len(sources) == 0
    assert len(sinks) == 0


@pytest.mark.usefixtures("_db_test_get_children")
def test_get_children_level2(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        all_nodes = fetch_all_thing_nodes(session)
        parent_node = next((node for node in all_nodes if node.name == "Anlage 1"), None)
        assert parent_node is not None, "Expected parent node 'Anlage 1' not found"

        children, sources, sinks = get_children(parent_node.id)

    assert isinstance(children, list)
    assert isinstance(sources, list)
    assert isinstance(sinks, list)

    assert len(children) == 2

    expected_children_names = {"Hochbehälter 1 Anlage 1", "Hochbehälter 2 Anlage 1"}
    children_names = {child.name for child in children}
    assert children_names == expected_children_names

    assert len(sources) == 0
    assert len(sinks) == 0


@pytest.mark.usefixtures("_db_test_get_children")
def test_get_children_leaves(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        all_nodes = fetch_all_thing_nodes(session)
        parent_node = next(
            (node for node in all_nodes if node.name == "Hochbehälter 1 Anlage 1"), None
        )

        assert parent_node is not None, "Expected parent node 'Hochbehälter 1 Anlage 1' not found"

        source_associations = session.query(thingnode_source_association).all()
        print(" ############## Contents of thingnode_source_associations:")
        for row in source_associations:
            print(row)

        sink_associations = session.query(thingnode_sink_association).all()
        print(" ############## Contents of thingnode_sink_associations:")
        for row in sink_associations:
            print(row)

        children, sources, sinks = get_children(parent_node.id)

        print(sources)
        print(sinks)

        assert isinstance(children, list), "Children is not a list"
        assert isinstance(sources, list), "Sources is not a list"
        assert isinstance(sinks, list), "Sinks is not a list"

        assert len(children) == 0, f"Expected no children, but found {len(children)}"

        assert len(sinks) == 1, f"Expected 1 sink, but found {len(sinks)}"
        assert (
            sinks[0].name
            == "Anomaly Score für die Energieverbräuche des Pumpensystems in Hochbehälter"
        ), f"Unexpected sink name: {sinks[0].name}"


@pytest.mark.usefixtures("_db_test_get_children")
def test_get_children_leaf_with_sources_and_sinks(mocked_clean_test_db_session):
    parent_id = fetch_all_thing_nodes(mocked_clean_test_db_session())[4].id
    result = get_children(parent_id)
    assert isinstance(result, tuple)
    assert len(result) == 3
    assert len(result[0]) == 0
    assert len(result[1]) == 1
    assert len(result[2]) == 1
    assert result[1][0].name == "Energieverbrauch einer Einzelpumpe in Hochbehälter"
    assert (
        result[2][0].name
        == "Anomaly Score für die Energieverbräuche des Pumpensystems in Hochbehälter"
    )


def test_complete_structure_object_creation():
    with open("tests/structure/data/db_test_structure.json") as file:
        data = json.load(file)
    cs = CompleteStructure(**data)

    assert len(cs.thing_nodes) == 7
    assert len(cs.element_types) == 3
    assert len(cs.sources) == 2
    assert len(cs.sinks) == 2

    tn_names = [tn.name for tn in cs.thing_nodes]
    expected_tn_names = [tn["name"] for tn in data["thing_nodes"]]
    assert all(name in tn_names for name in expected_tn_names)


@pytest.mark.usefixtures("_db_test_get_children")
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

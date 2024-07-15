import json
from sqlite3 import Connection as SQLite3Connection

import pytest
from sqlalchemy import event
from sqlalchemy.future.engine import Engine

from hetdesrun.structure.db.exceptions import DBNotFoundError
from hetdesrun.structure.db.orm_service import (
    fetch_all_element_types,
    fetch_all_sinks,
    fetch_all_sources,
    fetch_all_thing_nodes,
    update_structure_from_file,
)
from hetdesrun.structure.models import CompleteStructure
from hetdesrun.structure.structure_service import get_children


@pytest.fixture()
def _db_test_get_children(mocked_clean_test_db_session):
    file_path = (
        "tests/structure/data/"
        "db_test_load_structure_from_json_file_with_unordered_thingnodes_many2many.json"
    )
    update_structure_from_file(file_path)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection: SQLite3Connection, connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@pytest.mark.usefixtures("_db_test_get_children")
def test_get_children_root(mocked_clean_test_db_session):
    result = get_children(None)
    assert isinstance(result, tuple)
    assert len(result) == 3
    assert len(result[0]) == 1
    assert result[0][0].name == "RootNode"
    assert len(result[1]) == 0
    assert len(result[2]) == 0


@pytest.mark.usefixtures("_db_test_get_children")
def test_get_children_level1(mocked_clean_test_db_session):
    root_id = "00000000-0000-0000-0000-000000000004"
    result = get_children(root_id)
    assert isinstance(result, tuple)
    assert len(result) == 3
    assert len(result[0]) == 1
    assert result[0][0].name == "ChildNode1"
    assert len(result[1]) == 0
    assert len(result[2]) == 0


@pytest.mark.usefixtures("_db_test_get_children")
def test_get_children_level2(mocked_clean_test_db_session):
    child1_id = "11111111-1111-1111-1111-111111111111"
    result = get_children(child1_id)
    assert isinstance(result, tuple)
    assert len(result) == 3
    assert len(result[0]) == 1
    assert result[0][0].name == "ChildNode2"
    assert len(result[1]) == 0
    assert len(result[2]) == 0


@pytest.mark.usefixtures("_db_test_get_children")
def test_get_children_level3(mocked_clean_test_db_session):
    child2_id = "22222222-2222-2222-2222-222222222222"
    result = get_children(child2_id)
    assert isinstance(result, tuple)
    assert len(result) == 3
    assert len(result[0]) == 3
    child_names = [node.name for node in result[0]]
    assert "ChildNode3" in child_names
    assert "ChildNode2_Child1" in child_names
    assert "ChildNode2_Child2" in child_names
    assert len(result[1]) == 0
    assert len(result[2]) == 0


@pytest.mark.usefixtures("_db_test_get_children")
def test_get_children_leaves(mocked_clean_test_db_session):
    child3_id = "33333333-3333-3333-3333-333333333333"
    result = get_children(child3_id)
    assert isinstance(result, tuple)
    assert len(result) == 3
    assert len(result[0]) == 2
    assert len(result[1]) == 0
    assert len(result[2]) == 0
    leaf_names = [node.name for node in result[0]]
    assert "LeafNodeWith2Sources1Sink" in leaf_names
    assert "LeafNodeWith1Source2Sinks" in leaf_names


@pytest.mark.usefixtures("_db_test_get_children")
def test_get_children_leaf_with_sources_and_sinks(mocked_clean_test_db_session):
    parent_id = "33333333-3333-3333-3333-333333333333"  # ID für ChildNode3
    result = get_children(parent_id)
    assert isinstance(result, tuple)
    assert len(result) == 3
    assert len(result[0]) == 2  # Zwei Kinder
    assert len(result[1]) == 0  # Keine Quellen direkt unter diesem Knoten
    assert len(result[2]) == 0  # Keine Senken direkt unter diesem Knoten
    children = result[0]
    child_names = [child.name for child in children]
    assert "LeafNodeWith2Sources1Sink" in child_names
    assert "LeafNodeWith1Source2Sinks" in child_names


@pytest.mark.usefixtures("_db_test_get_children")
def test_get_children_non_existent(mocked_clean_test_db_session):
    with pytest.raises(DBNotFoundError):
        get_children("99999999-9999-9999-9999-999999999999")


def test_complete_structure_object_creation():
    with open(
        "tests/structure/data/db_test_load_structure_from_json_file_with_unordered_thingnodes_many2many.json"
    ) as file:
        data = json.load(file)
    cs = CompleteStructure(**data)

    assert len(cs.thing_nodes) == 10
    assert len(cs.element_types) == 3
    assert len(cs.sources) == 7
    assert len(cs.sinks) == 7

    tn_names = [tn.name for tn in cs.thing_nodes]
    expected_tn_names = [tn["name"] for tn in data["thing_nodes"]]
    assert all(name in tn_names for name in expected_tn_names)


# @pytest.mark.usefixtures("_db_test_get_children")
# def test_delete_structure_root(mocked_clean_test_db_session):
#     with mocked_clean_test_db_session() as session:
#         delete_structure()

#         remaining_thing_nodes = fetch_all_thing_nodes(session)
#         assert len(remaining_thing_nodes) == 0

#         remaining_sources = fetch_all_sources(session)
#         assert len(remaining_sources) == 0

#         remaining_sinks = fetch_all_sinks(session)
#         assert len(remaining_sinks) == 0

#         remaining_element_types = fetch_all_element_types(session)
#         assert len(remaining_element_types) == 0

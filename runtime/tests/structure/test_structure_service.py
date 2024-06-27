from sqlite3 import Connection as SQLite3Connection

import pytest
from sqlalchemy import event
from sqlalchemy.future.engine import Engine

from hetdesrun.structure.db.exceptions import DBNotFoundError
from hetdesrun.structure.db.orm_service import update_structure
from hetdesrun.structure.models import Sink, Source, ThingNode
from hetdesrun.structure.structure_service import get_children, get_item


@pytest.fixture()
def _db_test_get_children(mocked_clean_test_db_session):
    file_path = "tests/structure/data/db_test_get_children.json"
    update_structure(file_path)


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
    assert len(result[0]) == 1
    assert result[0][0].name == "ChildNode3"
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
    leaf1_id = "44444444-4444-4444-4444-444444444444"
    result = get_children(leaf1_id)
    assert isinstance(result, tuple)
    assert len(result) == 3
    assert len(result[0]) == 0
    assert len(result[1]) == 2
    assert len(result[2]) == 1
    sources = result[1]
    sinks = result[2]
    assert sources[0].name == "Source1"
    assert sources[1].name == "Source2"
    assert sinks[0].name == "Sink3"


@pytest.mark.usefixtures("_db_test_get_children")
def test_get_children_non_existent(mocked_clean_test_db_session):
    with pytest.raises(DBNotFoundError):
        get_children("99999999-9999-9999-9999-999999999999")


@pytest.mark.usefixtures("_db_test_get_children")
def test_get_item_thing_node(mocked_clean_test_db_session):
    item_id = "00000000-0000-0000-0000-000000000004"
    result = get_item(item_id)
    assert isinstance(result, ThingNode)
    assert result.name == "RootNode"


@pytest.mark.usefixtures("_db_test_get_children")
def test_get_item_source(mocked_clean_test_db_session):
    item_id = "11111111-1111-1111-1111-111111111114"
    result = get_item(item_id)
    assert isinstance(result, Source)
    assert result.name == "Source1"


@pytest.mark.usefixtures("_db_test_get_children")
def test_get_item_sink(mocked_clean_test_db_session):
    item_id = "66666666-6666-6666-6666-666666666669"
    result = get_item(item_id)
    assert isinstance(result, Sink)
    assert result.name == "Sink1"


@pytest.mark.usefixtures("_db_test_get_children")
def test_get_item_non_existent(mocked_clean_test_db_session):
    with pytest.raises(DBNotFoundError):
        get_item("99999999-9999-9999-9999-999999999999")

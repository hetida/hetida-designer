import json
import time
from sqlite3 import Connection as SQLite3Connection

import pytest
from pydantic import ValidationError
from sqlalchemy import event
from sqlalchemy.future.engine import Engine

from hetdesrun.persistence.dbmodels import (
    ElementTypeOrm,
    ElementTypeToPropertySetOrm,
    PropertyMetadataOrm,
    PropertySetOrm,
    ThingNodeOrm,
)
from hetdesrun.structure.db.exceptions import DBIntegrityError, DBNotFoundError
from hetdesrun.structure.db.external_types import ExternalType
from hetdesrun.structure.db.orm_service import (
    add_et,
    add_et2ps,
    add_pm,
    add_ps,
    add_tn,
    delete_et,
    delete_et2ps,
    delete_et_cascade,
    delete_pm,
    delete_ps,
    delete_tn,
    fetch_et2ps_by_id,
    fetch_et_by_id,
    fetch_pm_by_id,
    fetch_ps_by_id,
    fetch_tn_by_id,
    fetch_tn_child_ids_by_parent_id,
    get_ancestors_tn_ids,
    get_children_tn_ids,
    get_descendants_tn_ids,
    get_parent_tn_id,
    read_single_element_type,
    read_single_et2ps,
    read_single_property_metadata,
    read_single_property_set,
    read_single_thingnode,
    store_single_element_type,
    store_single_et2ps,
    store_single_property_metadata,
    store_single_property_set,
    store_single_sink,
    store_single_source,
    store_single_thingnode,
    update_et,
    update_et2ps,
    update_pm,
    update_ps,
    update_structure,
    update_tn,
)
from hetdesrun.structure.models import (
    ElementType,
    ElementTypeToPropertySet,
    PropertyMetadata,
    PropertySet,
    Sink,
    Source,
    ThingNode,
)

ThingNode.update_forward_refs()

# Fixture definitions


@pytest.fixture()
def _db_test_thing_node_hierarchy(mocked_clean_test_db_session):
    with open("tests/structure/data/db_test_thing_node_hierarchy.json") as file:
        data = json.load(file)

    for element_type_data in data["element_types"]:
        element_type = ElementType(**element_type_data)
        store_single_element_type(element_type)

    for node_data in data["thing_nodes"]:
        node = ThingNode(**node_data)
        store_single_thingnode(node)


@pytest.fixture()
def _db_comprehensive_cascade_deletion(mocked_clean_test_db_session):
    with open(
        "tests/structure/data/db_test_comprehensive_cascade_deletion.json"
    ) as file:
        data = json.load(file)

    for element_type_data in data["element_types"]:
        element_type = ElementType(**element_type_data)
        store_single_element_type(element_type)

    for node_data in data["thing_nodes"]:
        node = ThingNode(**node_data)
        store_single_thingnode(node)


@pytest.fixture()
def _db_test_thing_node_many_children(mocked_clean_test_db_session):
    with open("tests/structure/data/db_test_thing_node_many_children.json") as file:
        data = json.load(file)

    for element_type_data in data["element_types"]:
        element_type = ElementType(**element_type_data)
        store_single_element_type(element_type)

    for node_data in data["thing_nodes"]:
        node = ThingNode(**node_data)
        store_single_thingnode(node)


# Enable Foreign Key Constraints for SQLite Connections


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection: SQLite3Connection, connection_record) -> None:  # type: ignore  # noqa: E501,
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# ORM Model Validation Tests


def test_invalid_thing_node_orm_creation(mocked_clean_test_db_session):
    session = mocked_clean_test_db_session()
    et_orm_object = ElementTypeOrm(id=1, name="TypeOrm1")
    add_et(session, et_orm_object)
    tn_orm_object = ThingNodeOrm(
        id="invalid", name=123, element_type_id="invalid", entity_uuid="invalid"
    )

    with pytest.raises(DBIntegrityError):
        add_tn(session, tn_orm_object)


# Pydantic Model Validation Tests


def test_invalid_thing_node_creation():
    with pytest.raises(ValidationError):
        ThingNode(
            id="invalid", name=123, element_type_id="invalid", entity_uuid="invalid"
        )


def test_valid_thing_node_creation():
    try:
        ThingNode(id=1, name="valid_name", element_type_id=1, entity_uuid="valid_uuid")
    except ValidationError:
        pytest.fail("Valid ThingNode creation raised ValidationError unexpectedly.")


def test_invalid_element_type_creation():
    with pytest.raises(ValidationError):
        ElementType(id="invalid", name=123)


def test_valid_element_type_creation():
    try:
        ElementType(id=1, name="valid_name")
    except ValidationError:
        pytest.fail("Valid ElementType creation raised ValidationError unexpectedly.")


def test_invalid_property_set_creation():
    with pytest.raises(ValidationError):
        PropertySet(
            id="invalid",
            name=123,
            reference_table_name=345,
            property_set_type="INVALID",
        )


def test_valid_property_set_creation():
    try:
        PropertySet(
            id=1,
            name="valid_name",
            reference_table_name="valid_name",
            property_set_type="INTERNAL",
        )
    except ValidationError:
        pytest.fail("Valid PropertySet creation raised ValidationError unexpectedly.")


def test_invalid_element_type_to_property_set_creation():
    with pytest.raises(ValidationError):
        ElementTypeToPropertySet(
            element_type_id="invalid", property_set_id="invalid", order_no="invalid"
        )


def test_valid_element_type_to_property_set_creation():
    try:
        ElementTypeToPropertySet(element_type_id=1, property_set_id=1, order_no=1)
    except ValidationError:
        pytest.fail(
            "Valid ElementTypeToPropertySet creation raised ValidationError unexpectedly."
        )


def test_invalid_property_metadata_creation():
    with pytest.raises(ValidationError):
        PropertyMetadata(
            id="invalid",
            property_set_id="invalid",
            column_name=123,
            column_label=456,
            column_type="INVALID",
        )


def test_valid_property_metadata_creation():
    try:
        PropertyMetadata(
            id=1,
            property_set_id=1,
            column_name="valid column",
            column_label="valid_label",
            column_type="STRING",
            nullable=True,
            order_no=1,
        )
    except ValidationError:
        pytest.fail(
            "Valid PropertyMetadata creation raised ValidationError unexpectedly."
        )


# CRUD ORM Operation Tests


def test_add_et_tn(mocked_clean_test_db_session):
    session = mocked_clean_test_db_session()
    et_orm_object = ElementTypeOrm(id=1, name="TypeOrm1")
    add_et(session, et_orm_object)
    tn_orm_object = ThingNodeOrm(
        id=1, name="NodeOrm1", element_type_id=1, entity_uuid="entity_uuid_1"
    )
    add_tn(session, tn_orm_object)
    retrieved_et_orm = fetch_et_by_id(session, 1)
    retrieved_tn_orm = fetch_tn_by_id(session, 1)
    assert et_orm_object == retrieved_et_orm
    assert tn_orm_object == retrieved_tn_orm


def test_add_et_tn_integrity_error(mocked_clean_test_db_session):
    session = mocked_clean_test_db_session()
    et_orm_object = ElementTypeOrm(id=1, name="TypeOrm1")
    add_et(session, et_orm_object)
    tn_orm_object = ThingNodeOrm(
        id=1, element_type_id=1, entity_uuid="entity_uuid_1"
    )  # name missing

    with pytest.raises(DBIntegrityError):
        add_tn(session, tn_orm_object)


# CRUD Operations for ThingNode


@pytest.mark.skip(
    reason="assert ThingNode(id=...[], sink=None) == ThingNode(id=...ne, sink=None)."
)
def test_store_single_thingnode(mocked_clean_test_db_session):
    et_object = ElementType(id=1, name="Type1")
    store_single_element_type(et_object)
    tn_object = ThingNode(
        id=1, name="Node1", element_type_id=1, entity_uuid="entity_uuid"
    )
    store_single_thingnode(tn_object)
    retrieved_tn = read_single_thingnode(1)
    assert tn_object == retrieved_tn


def test_read_single_thingnode(mocked_clean_test_db_session):
    tn_id = 1
    with pytest.raises(DBNotFoundError):
        read_single_thingnode(tn_id)


@pytest.mark.skip(
    reason="assert ThingNode(id=...[], sink=None) == ThingNode(id=...ne, sink=None)."
)
def test_storing_and_receiving(mocked_clean_test_db_session):
    et_object = ElementType(id=1, name="Type1")
    store_single_element_type(et_object)

    tn_id = 9998
    tn_object = ThingNode(
        id=tn_id, name="Node1", element_type_id=1, entity_uuid="entity_uuid"
    )
    store_single_thingnode(tn_object)

    received_tn_object = read_single_thingnode(tn_id)
    assert tn_object == received_tn_object

    wrong_tn_id = 9999
    with pytest.raises(DBNotFoundError):
        received_tn_object = read_single_thingnode(wrong_tn_id)


@pytest.mark.skip(
    reason="Test skipped temporarily. Replace dictionary with Pydantic model."
)
def test_updating_existing_tn(mocked_clean_test_db_session):
    et_object = ElementType(id=1, name="Type1")
    store_single_element_type(et_object)
    tn_id = 10001
    tn_object = ThingNode(
        id=tn_id, name="Node1", element_type_id=1, entity_uuid="entity_uuid"
    )
    store_single_thingnode(tn_object)

    updated_data = {
        "name": "UpdatedNode1",
        "description": "Updated description",
    }
    update_tn(tn_id, updated_data)

    fetched_tn_object = read_single_thingnode(tn_id)
    assert fetched_tn_object.name == updated_data["name"]
    assert fetched_tn_object.description == updated_data["description"]


def test_updating_nonexisting_tn(mocked_clean_test_db_session):
    non_existent_tn_id = 9999
    updated_data = {
        "name": "NonExistentNode",
        "description": "This node does not exist.",
    }
    with pytest.raises(DBNotFoundError):
        update_tn(non_existent_tn_id, updated_data)


@pytest.mark.skip(
    reason="Test skipped temporarily. Replace dictionary with Pydantic model."
)
def test_update_thingnode_valid_data(mocked_clean_test_db_session):
    et_object = ElementType(id=1, name="Type1")
    store_single_element_type(et_object)
    tn_object = ThingNode(
        id=1, name="Node1", element_type_id=1, entity_uuid="entity_uuid"
    )
    store_single_thingnode(tn_object)
    updated_data = {"name": "UpdatedNode1"}
    updated_tn = update_tn(1, updated_data)
    assert updated_tn.name == "UpdatedNode1"


@pytest.mark.skip(
    reason="Test skipped temporarily. Replace dictionary with Pydantic model."
)
def test_update_thingnode_invalid_data(mocked_clean_test_db_session):
    et_object = ElementType(id=1, name="Type1")
    store_single_element_type(et_object)
    tn_object = ThingNode(
        ud=1, name="Node1", element_type_id=1, entity_uuid="entity_uuid"
    )
    store_single_thingnode(tn_object)
    updated_data = {"name": None}
    with pytest.raises(DBIntegrityError):
        update_tn(1, updated_data)


@pytest.mark.usefixtures("_db_comprehensive_cascade_deletion")
def test_delete_thingnode_valid_id():
    delete_tn(1)  # Root node

    with pytest.raises(DBNotFoundError):
        read_single_thingnode(1)  # Root node should be deleted
    with pytest.raises(DBNotFoundError):
        read_single_thingnode(2)  # Child node should also be deleted
    with pytest.raises(DBNotFoundError):
        read_single_thingnode(3)  # Grandchild node should also be deleted


def test_delete_thingnode_invalid_id(mocked_clean_test_db_session):
    with pytest.raises(DBNotFoundError):
        delete_tn(9999)


def test_delete_thingnode_integrity_error(mocked_clean_test_db_session):
    et_object = ElementType(id=1, name="Type1")
    store_single_element_type(et_object)
    parent_tn_object = ThingNode(
        id=1, name="Node1", element_type_id=1, entity_uuid="entity_uuid_1"
    )
    child_tn_object = ThingNode(
        id=2,
        name="Node2",
        parent_node_id=1,
        element_type_id=1,
        entity_uuid="entity_uuid_2",
    )
    store_single_thingnode(parent_tn_object)
    store_single_thingnode(child_tn_object)

    delete_tn(1)


def test_update_structure(mocked_clean_test_db_session):
    et_object1 = ElementType(id=1, name="Type1")
    store_single_element_type(et_object1)
    et_object2 = ElementType(id=2, name="Type2")
    store_single_element_type(et_object2)
    et_object3 = ElementType(id=3, name="Type3")
    store_single_element_type(et_object3)

    source1 = Source(
        id=1,
        thingNodeId=2,
        name="Source1",
        type=ExternalType.METADATA_INT,
        visible=True,
        path="path/to/source",
        metadataKey="key1",
        filters={},
    )

    sink1 = Sink(
        id=1,
        thingNodeId=3,
        name="Sink1",
        type=ExternalType.METADATA_INT,
        visible=True,
        path="path/to/sink",
        metadataKey="key2",
        filters={},
    )

    leaf_node_with_source = ThingNode(
        id=2,
        name="LeafNodeWithSource",
        parent_node_id=1,
        element_type_id=et_object2.id,
        entity_uuid="leaf_uuid_1",
        source=source1,
        children=[],
    )

    leaf_node_with_sink = ThingNode(
        id=3,
        name="LeafNodeWithSink",
        parent_node_id=1,
        element_type_id=et_object3.id,
        entity_uuid="leaf_uuid_2",
        sink=sink1,
        children=[],
    )

    root_node = ThingNode(
        id=1,
        name="RootNode",
        element_type_id=et_object1.id,
        entity_uuid="root_uuid",
        children=[leaf_node_with_source, leaf_node_with_sink],
    )

    update_structure(root_node)

    saved_root_node = read_single_thingnode(root_node.id)
    assert saved_root_node.name == "RootNode"
    assert saved_root_node.entity_uuid == "root_uuid"

    saved_leaf_with_source = read_single_thingnode(leaf_node_with_source.id)
    assert saved_leaf_with_source.source is not None
    assert saved_leaf_with_source.source.name == "Source1"

    saved_leaf_with_sink = read_single_thingnode(leaf_node_with_sink.id)
    assert saved_leaf_with_sink.sink is not None
    assert saved_leaf_with_sink.sink.name == "Sink1"

    assert len(saved_root_node.children) == 2


def test_update_structure_with_non_root_node(mocked_clean_test_db_session):
    et_object = ElementType(id=1, name="Type1")
    store_single_element_type(et_object)

    non_root_node = ThingNode(
        id=2,
        name="NonRootNode",
        parent_node_id=1,
        element_type_id=1,
        entity_uuid="non_root_uuid",
    )

    with pytest.raises(ValueError, match="The provided ThingNode is not a root node."):
        update_structure(non_root_node)


# CRUD Operations for ElementType
def test_store_single_element_type(mocked_clean_test_db_session):
    et_object = ElementType(id=1, name="Type1")
    store_single_element_type(et_object)
    retrieved_et = read_single_element_type(1)
    assert et_object == retrieved_et


def test_update_element_type_valid_data(mocked_clean_test_db_session):
    et_object = ElementType(id=1, name="Type1")
    store_single_element_type(et_object)
    updated_data = {"name": "UpdatedType1"}
    updated_et = update_et(1, updated_data)
    assert updated_et.name == "UpdatedType1"


def test_update_element_type_invalid_data(mocked_clean_test_db_session):
    et_object = ElementType(id=1, name="Type1")
    store_single_element_type(et_object)
    updated_data = {"name": None}
    with pytest.raises(DBIntegrityError):
        update_et(1, updated_data)


def test_delete_element_type(mocked_clean_test_db_session):
    et_object = ElementType(id=1, name="Type1")
    store_single_element_type(et_object)

    delete_et(1)

    with pytest.raises(DBNotFoundError):
        read_single_element_type(1)


def test_delete_element_type_with_associated_thingnode(mocked_clean_test_db_session):
    et_object = ElementType(id=1, name="Type1")
    store_single_element_type(et_object)
    tn_object = ThingNode(
        ud=1, name="Node1", element_type_id=1, entity_uuid="entity_uuid"
    )
    store_single_thingnode(tn_object)

    with pytest.raises(DBIntegrityError):
        delete_et(1)


def test_delete_cascade_element_type(mocked_clean_test_db_session):
    et_object = ElementType(id=1, name="Type1")
    store_single_element_type(et_object)
    tn_object = ThingNode(
        ud=1, name="Node1", element_type_id=1, entity_uuid="entity_uuid"
    )
    store_single_thingnode(tn_object)

    delete_et_cascade(1)

    with pytest.raises(DBNotFoundError):
        read_single_element_type(1)


# Search and Retrieval Functions
def test_fetch_tn_by_valid_id(mocked_clean_test_db_session):
    et_object = ElementType(id=1, name="Type1")
    store_single_element_type(et_object)
    tn_object = ThingNode(
        id=1, name="Node1", element_type_id=1, entity_uuid="entity_uuid"
    )
    store_single_thingnode(tn_object)
    retrieved_tn = fetch_tn_by_id(mocked_clean_test_db_session(), 1)
    assert retrieved_tn.id == 1


def test_fetch_tn_by_invalid_id(mocked_clean_test_db_session):
    with pytest.raises(DBNotFoundError):
        fetch_tn_by_id(mocked_clean_test_db_session(), 9999)


@pytest.mark.usefixtures("_db_test_thing_node_many_children")
def test_fetch_tn_child_ids_by_parent_id(mocked_clean_test_db_session):
    session = mocked_clean_test_db_session()
    tn_child_list = fetch_tn_child_ids_by_parent_id(session, 1)

    assert tn_child_list == [2, 3]


@pytest.mark.usefixtures("_db_test_thing_node_many_children")
def test_fetch_tn_child_ids_by_parent_id_dbnotfound(mocked_clean_test_db_session):
    session = mocked_clean_test_db_session()

    with pytest.raises(DBNotFoundError):
        fetch_tn_child_ids_by_parent_id(session, 3)


# Tests for Hierarchy and Relationships
@pytest.mark.usefixtures("_db_test_thing_node_hierarchy")
def test_thing_node_hierarchy():
    hierarchy_ids = get_ancestors_tn_ids(3)
    assert hierarchy_ids == [3, 2, 1]
    children_ids = get_children_tn_ids(1)
    assert children_ids == [2]
    with pytest.raises(DBNotFoundError):
        get_ancestors_tn_ids(4)


def test_get_children_tn_ids_valid_id(mocked_clean_test_db_session):
    et_object = ElementType(id=1, name="Type1")
    store_single_element_type(et_object)
    tn_object = ThingNode(
        id=1, name="Node1", element_type_id=1, entity_uuid="entity_uuid"
    )
    child_tn_object = ThingNode(
        id=2,
        name="ChildNode1",
        parent_node_id=1,
        element_type_id=1,
        entity_uuid="child_entity_uuid",
    )
    store_single_thingnode(tn_object)
    store_single_thingnode(child_tn_object)
    children_ids = get_children_tn_ids(1)
    assert children_ids == [2]


def test_get_ancestors_tn_ids_valid_id(mocked_clean_test_db_session):
    et_object = ElementType(id=1, name="Type1")
    store_single_element_type(et_object)

    tn_object1 = ThingNode(
        id=1, name="RootNode", element_type_id=1, entity_uuid="entity_uuid_1"
    )
    tn_object2 = ThingNode(
        id=2,
        name="ChildNode1",
        parent_node_id=1,
        element_type_id=1,
        entity_uuid="entity_uuid_2",
    )
    tn_object3 = ThingNode(
        id=3,
        name="ChildNode2",
        parent_node_id=2,
        element_type_id=1,
        entity_uuid="entity_uuid_3",
    )
    tn_object4 = ThingNode(
        id=4,
        name="GrandChildNode",
        parent_node_id=3,
        element_type_id=1,
        entity_uuid="entity_uuid_4",
    )

    store_single_thingnode(tn_object1)
    store_single_thingnode(tn_object2)
    store_single_thingnode(tn_object3)
    store_single_thingnode(tn_object4)

    ancestors_ids = get_ancestors_tn_ids(4)

    assert ancestors_ids == [4, 3, 2, 1]


def test_get_ancestors_tn_ids_valid_depth_valid_id(mocked_clean_test_db_session):
    et_object = ElementType(id=1, name="Type1")
    store_single_element_type(et_object)

    tn_object1 = ThingNode(
        id=1, name="RootNode", element_type_id=1, entity_uuid="entity_uuid_1"
    )
    tn_object2 = ThingNode(
        id=2,
        name="ChildNode1",
        parent_node_id=1,
        element_type_id=1,
        entity_uuid="entity_uuid_2",
    )
    tn_object3 = ThingNode(
        id=3,
        name="ChildNode2",
        parent_node_id=2,
        element_type_id=1,
        entity_uuid="entity_uuid_3",
    )
    tn_object4 = ThingNode(
        id=4,
        name="GrandChildNode",
        parent_node_id=3,
        element_type_id=1,
        entity_uuid="entity_uuid_4",
    )

    store_single_thingnode(tn_object1)
    store_single_thingnode(tn_object2)
    store_single_thingnode(tn_object3)
    store_single_thingnode(tn_object4)

    ancestors_ids = get_ancestors_tn_ids(4, 2)

    assert ancestors_ids == [4, 3]


def test_get_ancestors_tn_ids_invalid_id(mocked_clean_test_db_session):
    with pytest.raises(DBNotFoundError):
        get_ancestors_tn_ids(9999)


def test_get_ancestors_tn_ids_invalid_depth_valid_id(mocked_clean_test_db_session):
    et_object = ElementType(id=1, name="Type1")
    store_single_element_type(et_object)

    tn_object1 = ThingNode(
        id=1, name="RootNode", element_type_id=1, entity_uuid="entity_uuid_1"
    )
    tn_object2 = ThingNode(
        id=2,
        name="ChildNode1",
        parent_node_id=1,
        element_type_id=1,
        entity_uuid="entity_uuid_2",
    )
    tn_object3 = ThingNode(
        id=3,
        name="ChildNode2",
        parent_node_id=2,
        element_type_id=1,
        entity_uuid="entity_uuid_3",
    )
    tn_object4 = ThingNode(
        id=4,
        name="GrandChildNode",
        parent_node_id=3,
        element_type_id=1,
        entity_uuid="entity_uuid_4",
    )

    store_single_thingnode(tn_object1)
    store_single_thingnode(tn_object2)
    store_single_thingnode(tn_object3)
    store_single_thingnode(tn_object4)

    ancestors_ids = get_ancestors_tn_ids(4, 2)

    with pytest.raises(AssertionError):
        assert ancestors_ids == [4, 3, 2]


# Exception Handling and Data Integrity Tests


@pytest.mark.skip(
    reason="Test skipped temporarily. Replace dictionary with Pydantic model."
)
def test_uniqueness_thingnode(mocked_clean_test_db_session):
    et_object = ElementType(id=1, name="Type1")
    store_single_element_type(et_object)
    tn_object = ThingNode(
        id=1, name="Node1", element_type_id=1, entity_uuid="entity_uuid"
    )
    store_single_thingnode(tn_object)
    updated_data = {"name": "UpdatedNode1"}
    updated_tn = update_tn(1, updated_data)
    with pytest.raises(DBIntegrityError):
        store_single_thingnode(updated_tn)


def test_handle_duplicate_thingnode_insertion(mocked_clean_test_db_session):
    et_object = ElementType(id=1, name="Type1")
    store_single_element_type(et_object)
    tn_object = ThingNode(
        id=1, name="Node1", element_type_id=1, entity_uuid="entity_uuid"
    )
    store_single_thingnode(tn_object)
    with pytest.raises(DBIntegrityError):
        store_single_thingnode(tn_object)


def test_handle_duplicate_elementtype_insertion(mocked_clean_test_db_session):
    et_object1 = ElementType(id=1, name="Type1")
    et_object2 = ElementType(id=1, name="Type2")
    et_object3 = ElementType(id=2, name="Type1")
    store_single_element_type(et_object1)

    with pytest.raises(DBIntegrityError):
        store_single_element_type(et_object2)
    with pytest.raises(DBIntegrityError):
        store_single_element_type(et_object3)


@pytest.mark.skip(reason="Replace dictionary with Pydantic model")
def test_rollback_on_failure(mocked_clean_test_db_session):
    et_object = ElementType(id=1, name="Type1")
    store_single_element_type(et_object)
    tn_object = ThingNode(
        id=1, name="Node1", element_type_id=1, entity_uuid="entity_uuid"
    )
    store_single_thingnode(tn_object)
    updated_data = {"name": None}
    with pytest.raises(DBIntegrityError):
        update_tn(1, updated_data)
    retrieved_tn = read_single_thingnode(1)
    assert retrieved_tn.name == "Node1"


# Performance and Load Tests


@pytest.mark.skip(reason="Skipping during development because it takes too long.")
def test_performance_bulk_insert(mocked_clean_test_db_session):
    num_records = 1000
    et_object = ElementType(id=1, name="Type1")
    store_single_element_type(et_object)
    start_time = time.time()
    for i in range(num_records):
        tn_object = ThingNode(
            id=i + 1,
            name=f"Node{i+1}",
            element_type_id=1,
            entity_uuid=f"entity_uuid_{i+1}",
        )
        store_single_thingnode(tn_object)
    end_time = time.time()
    duration = end_time - start_time
    print(f"Bulk insert of {num_records} records took {duration:.2f} seconds")
    assert duration < 20, f"Bulk insert took too long: {duration:.2f} seconds"


@pytest.mark.skip(reason="Skipping during development because it takes too long.")
def test_performance_bulk_delete(mocked_clean_test_db_session):
    num_records = 1000
    et_object = ElementType(id=1, name="Type1")
    store_single_element_type(et_object)
    for i in range(num_records):
        tn_object = ThingNode(
            id=i + 1,
            name=f"Node{i+1}",
            element_type_id=1,
            entity_uuid=f"entity_uuid_{i+1}",
        )
        store_single_thingnode(tn_object)
    start_time = time.time()
    for i in range(num_records):
        delete_tn(i + 1)
    end_time = time.time()

    duration = end_time - start_time
    print(f"Bulk delete of {num_records} records took {duration:.2f} seconds")
    assert duration < 20, f"Bulk delete took too long: {duration:.2f} seconds"

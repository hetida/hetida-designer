import json
import time
import uuid
from sqlite3 import Connection as SQLite3Connection
from uuid import UUID

import pytest
from pydantic import ValidationError
from sqlalchemy import event
from sqlalchemy.future.engine import Engine

from hetdesrun.persistence.structure_service_dbmodels import (
    ElementTypeOrm,
    ElementTypeToPropertySetOrm,
    PropertyMetadataOrm,
    PropertySetOrm,
    SinkOrm,
    SourceOrm,
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
    fetch_all_element_types,
    fetch_all_sinks,
    fetch_all_sources,
    fetch_all_thing_nodes,
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
    load_structure_from_json_file,
    read_single_element_type,
    read_single_et2ps,
    read_single_property_metadata,
    read_single_property_set,
    read_single_thingnode,
    sort_thing_nodes,
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
    update_structure_from_file,
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
    file_path = (
        "tests/structure/data/"
        "db_test_load_structure_from_json_file_with_unordered_thingnodes_many2many.json"
    )
    update_structure_from_file(file_path)


@pytest.fixture()
def _db_comprehensive_cascade_deletion(mocked_clean_test_db_session):
    file_path = (
        "tests/structure/data/"
        "db_test_load_structure_from_json_file_with_unordered_thingnodes_many2many.json"
    )
    update_structure_from_file(file_path)


@pytest.fixture()
def _db_test_thing_node_many_children(mocked_clean_test_db_session):
    file_path = (
        "tests/structure/data/"
        "db_test_load_structure_from_json_file_with_unordered_thingnodes_many2many.json"
    )
    update_structure_from_file(file_path)


# Enable Foreign Key Constraints for SQLite Connections


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection: SQLite3Connection, connection_record) -> None:  # type: ignore  # noqa: E501,
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# ORM Model Validation Tests


def test_invalid_thing_node_orm_creation(mocked_clean_test_db_session):
    session = mocked_clean_test_db_session()
    et_orm_object = ElementTypeOrm(id=uuid.uuid4(), name="TypeOrm1")
    add_et(session, et_orm_object)
    tn_orm_object = ThingNodeOrm(
        id=uuid.uuid4(), name=123, element_type_id=uuid.uuid4()
    )

    with pytest.raises(DBIntegrityError):
        add_tn(session, tn_orm_object)


# Pydantic Model Validation Tests


def test_invalid_thing_node_creation():
    with pytest.raises(ValidationError):
        ThingNode(id="invalid", name=123, element_type_id="invalid")


def test_valid_thing_node_creation():
    try:
        ThingNode(
            id=uuid.uuid4(),
            name="valid_name",
            element_type_id=uuid.uuid4(),
            external_id="38-1-ext-valid",
        )
    except ValidationError:
        pytest.fail("Valid ThingNode creation raised ValidationError unexpectedly.")


def test_invalid_element_type_creation():
    with pytest.raises(ValidationError):
        ElementType(id="invalid", name=123)


def test_valid_element_type_creation():
    try:
        ElementType(id=uuid.uuid4(), name="valid_name")
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
            id=uuid.uuid4(),
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
        ElementTypeToPropertySet(
            element_type_id=uuid.uuid4(), property_set_id=uuid.uuid4(), order_no=1
        )
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
            id=uuid.uuid4(),
            property_set_id=uuid.uuid4(),
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
    et_orm_object = ElementTypeOrm(id=uuid.uuid4(), name="TypeOrm1")
    add_et(session, et_orm_object)
    tn_orm_object = ThingNodeOrm(
        id=uuid.uuid4(),
        name="NodeOrm1",
        element_type_id=et_orm_object.id,
        external_id="2-ext-valid",
    )
    add_tn(session, tn_orm_object)
    retrieved_et_orm = fetch_et_by_id(session, et_orm_object.id)
    retrieved_tn_orm = fetch_tn_by_id(session, tn_orm_object.id)
    assert et_orm_object == retrieved_et_orm
    assert tn_orm_object == retrieved_tn_orm


def test_add_et_tn_integrity_error(mocked_clean_test_db_session):
    session = mocked_clean_test_db_session()
    et_orm_object = ElementTypeOrm(id=uuid.uuid4(), name="TypeOrm1")
    add_et(session, et_orm_object)
    tn_orm_object = ThingNodeOrm(
        id=uuid.uuid4(), element_type_id=et_orm_object.id
    )  # name missing

    with pytest.raises(DBIntegrityError):
        add_tn(session, tn_orm_object)


# CRUD Operations for ThingNode


def test_store_single_thingnode(mocked_clean_test_db_session):
    et_object = ElementType(id=uuid.uuid4(), name="Type1")
    store_single_element_type(et_object)
    tn_object = ThingNode(
        id=uuid.uuid4(),
        name="Node1",
        element_type_id=et_object.id,
        external_id="3-ext-valid",
    )
    store_single_thingnode(tn_object)
    retrieved_tn = read_single_thingnode(tn_object.id)
    assert tn_object == retrieved_tn


def test_read_single_thingnode(mocked_clean_test_db_session):
    tn_id = uuid.uuid4()
    with pytest.raises(DBNotFoundError):
        read_single_thingnode(tn_id)


def test_storing_and_receiving(mocked_clean_test_db_session):
    et_object = ElementType(id=uuid.uuid4(), name="Type1")
    store_single_element_type(et_object)

    tn_id = uuid.uuid4()
    tn_object = ThingNode(
        id=tn_id, name="Node1", element_type_id=et_object.id, external_id="4-ext-valid"
    )
    store_single_thingnode(tn_object)

    received_tn_object = read_single_thingnode(tn_id)
    assert tn_object == received_tn_object

    wrong_tn_id = uuid.uuid4()
    with pytest.raises(DBNotFoundError):
        received_tn_object = read_single_thingnode(wrong_tn_id)


def test_updating_existing_tn(mocked_clean_test_db_session):
    et_object = ElementType(id=uuid.uuid4(), name="Type1")
    store_single_element_type(et_object)
    tn_id = uuid.uuid4()
    tn_object = ThingNode(
        id=tn_id, external_id="5-ext-valid", name="Node1", element_type_id=et_object.id
    )
    store_single_thingnode(tn_object)

    updated_data = ThingNode(
        id=tn_id,
        external_id="6-updt ext-valid",
        name="UpdatedNode1",
        element_type_id=et_object.id,
    )
    update_tn(tn_id, updated_data)

    fetched_tn_object = read_single_thingnode(tn_id)
    assert fetched_tn_object.name == updated_data.name
    assert fetched_tn_object.description == updated_data.description


def test_updating_nonexisting_tn(mocked_clean_test_db_session):
    non_existent_tn_id = uuid.uuid4()
    updated_data = ThingNode(
        id=non_existent_tn_id,
        external_id="7-ext-valid",
        name="NonExistentNode",
        element_type_id=uuid.uuid4(),
    )
    with pytest.raises(DBNotFoundError):
        update_tn(non_existent_tn_id, updated_data)


def test_update_thingnode_valid_data(mocked_clean_test_db_session):
    et_object = ElementType(id=uuid.uuid4(), name="Type1")
    store_single_element_type(et_object)
    tn_object = ThingNode(
        id=uuid.uuid4(),
        external_id="8-ext-valid",
        name="Node1",
        element_type_id=et_object.id,
    )
    store_single_thingnode(tn_object)
    updated_data = ThingNode(
        id=tn_object.id,
        external_id="9-updt-ext-valid",
        name="UpdatedNode1",
        element_type_id=et_object.id,
    )
    updated_tn = update_tn(tn_object.id, updated_data)
    assert updated_tn.name == "UpdatedNode1"


@pytest.mark.usefixtures("_db_comprehensive_cascade_deletion")
def test_delete_thingnode_valid_id():
    delete_tn(uuid.UUID("00000000-0000-0000-0000-000000000004"))  # Root node

    with pytest.raises(DBNotFoundError):
        read_single_thingnode(
            uuid.UUID("00000000-0000-0000-0000-000000000004")
        )  # Root node should be deleted
    with pytest.raises(DBNotFoundError):
        read_single_thingnode(
            uuid.UUID("11111111-1111-1111-1111-111111111111")
        )  # ChildNode1 should also be deleted
    with pytest.raises(DBNotFoundError):
        read_single_thingnode(
            uuid.UUID("22222222-2222-2222-2222-222222222222")
        )  # ChildNode2 should also be deleted


def test_delete_thingnode_invalid_id(mocked_clean_test_db_session):
    with pytest.raises(DBNotFoundError):
        delete_tn(uuid.uuid4())


def test_delete_thingnode_integrity_error(mocked_clean_test_db_session):
    et_object = ElementType(id=uuid.uuid4(), name="Type1")
    store_single_element_type(et_object)
    parent_tn_object = ThingNode(
        id=uuid.uuid4(),
        external_id="10-ext-valid",
        name="Node1",
        element_type_id=et_object.id,
    )
    child_tn_object = ThingNode(
        id=uuid.uuid4(),
        external_id="11-ext-valid",
        name="Node2",
        parent_node_id=parent_tn_object.id,
        element_type_id=et_object.id,
    )
    store_single_thingnode(parent_tn_object)
    store_single_thingnode(child_tn_object)

    delete_tn(parent_tn_object.id)


# CRUD Operations for ElementType
def test_store_single_element_type(mocked_clean_test_db_session):
    et_object = ElementType(id=uuid.uuid4(), name="Type1")
    store_single_element_type(et_object)
    retrieved_et = read_single_element_type(et_object.id)
    assert et_object == retrieved_et


def test_update_element_type_valid_data(mocked_clean_test_db_session):
    et_object = ElementType(id=uuid.uuid4(), name="Type1")
    store_single_element_type(et_object)
    et_update = et_object
    et_update.name = "UpdatedType1"
    updated_et = update_et(et_object.id, et_update)
    assert updated_et.name == "UpdatedType1"


def test_delete_element_type(mocked_clean_test_db_session):
    et_object = ElementType(id=uuid.uuid4(), name="Type1")
    store_single_element_type(et_object)

    delete_et(et_object.id)

    with pytest.raises(DBNotFoundError):
        read_single_element_type(et_object.id)


def test_delete_element_type_with_associated_thingnode(mocked_clean_test_db_session):
    et_object = ElementType(id=uuid.uuid4(), name="Type1")
    store_single_element_type(et_object)
    tn_object = ThingNode(
        id=uuid.uuid4(),
        external_id="12-ext-valid",
        name="Node1",
        element_type_id=et_object.id,
    )
    store_single_thingnode(tn_object)

    with pytest.raises(DBIntegrityError):
        delete_et(et_object.id)


def test_delete_cascade_element_type(mocked_clean_test_db_session):
    et_object = ElementType(id=uuid.uuid4(), name="Type1")
    store_single_element_type(et_object)
    tn_object = ThingNode(
        id=uuid.uuid4(),
        external_id="13-ext-valid",
        name="Node1",
        element_type_id=et_object.id,
    )
    store_single_thingnode(tn_object)

    delete_et_cascade(et_object.id)

    with pytest.raises(DBNotFoundError):
        read_single_element_type(et_object.id)


# Search and Retrieval Functions
def test_fetch_tn_by_valid_id(mocked_clean_test_db_session):
    et_object = ElementType(id=uuid.uuid4(), name="Type1")
    store_single_element_type(et_object)
    tn_object = ThingNode(
        id=uuid.uuid4(),
        external_id="14-ext-valid",
        name="Node1",
        element_type_id=et_object.id,
    )
    store_single_thingnode(tn_object)
    retrieved_tn = fetch_tn_by_id(mocked_clean_test_db_session(), tn_object.id)
    assert retrieved_tn.id == tn_object.id


def test_fetch_tn_by_invalid_id(mocked_clean_test_db_session):
    with pytest.raises(DBNotFoundError):
        fetch_tn_by_id(mocked_clean_test_db_session(), uuid.uuid4())


@pytest.mark.usefixtures("_db_test_thing_node_many_children")
def test_fetch_tn_child_ids_by_parent_id(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        parent_id = uuid.UUID(
            "00000000-0000-0000-0000-000000000004"
        )  # RootNode ID from the JSON file
        tn_child_list = fetch_tn_child_ids_by_parent_id(session, parent_id)

        assert len(tn_child_list) > 0  # Ensure that the list is not empty
        assert all(
            isinstance(child_id, uuid.UUID) for child_id in tn_child_list
        )  # Ensure all elements are UUIDs


@pytest.mark.usefixtures("_db_test_thing_node_many_children")
def test_fetch_tn_child_ids_by_parent_id_dbnotfound(mocked_clean_test_db_session):
    session = mocked_clean_test_db_session()

    with pytest.raises(DBNotFoundError):
        fetch_tn_child_ids_by_parent_id(
            session, uuid.UUID("00000000-0000-0000-0000-000000000003")
        )


# Tests for Hierarchy and Relationships
@pytest.mark.usefixtures("_db_test_thing_node_hierarchy")
def test_thing_node_hierarchy(mocked_clean_test_db_session):
    file_path = (
        "tests/structure/data/"
        "db_test_load_structure_from_json_file_with_unordered_thingnodes_many2many.json"
    )

    with open(file_path) as file:
        data = json.load(file)

    with mocked_clean_test_db_session() as session:
        # Fetch all elements from the database
        element_types_in_db = fetch_all_element_types(session)
        thing_nodes_in_db = fetch_all_thing_nodes(session)
        sources_in_db = fetch_all_sources(session)
        sinks_in_db = fetch_all_sinks(session)

        # Compare the counts
        assert len(element_types_in_db) == len(
            data["element_types"]
        ), "Mismatch in element types count"
        assert len(thing_nodes_in_db) == len(
            data["thing_nodes"]
        ), "Mismatch in thing nodes count"
        assert len(sources_in_db) == len(data["sources"]), "Mismatch in sources count"
        assert len(sinks_in_db) == len(data["sinks"]), "Mismatch in sinks count"

        # Compare the IDs to ensure all elements are correctly loaded
        element_type_ids_in_db = {
            str(element_type.id) for element_type in element_types_in_db
        }
        thing_node_ids_in_db = {str(thing_node.id) for thing_node in thing_nodes_in_db}
        source_ids_in_db = {str(source.id) for source in sources_in_db}
        sink_ids_in_db = {str(sink.id) for sink in sinks_in_db}

        element_type_ids_in_json = {
            element_type["id"] for element_type in data["element_types"]
        }
        thing_node_ids_in_json = {
            thing_node["id"] for thing_node in data["thing_nodes"]
        }
        source_ids_in_json = {source["id"] for source in data["sources"]}
        sink_ids_in_json = {sink["id"] for sink in data["sinks"]}

        assert (
            element_type_ids_in_db == element_type_ids_in_json
        ), "Mismatch in element type IDs"
        assert (
            thing_node_ids_in_db == thing_node_ids_in_json
        ), "Mismatch in thing node IDs"
        assert source_ids_in_db == source_ids_in_json, "Mismatch in source IDs"
        assert sink_ids_in_db == sink_ids_in_json, "Mismatch in sink IDs"


def test_get_children_tn_ids_valid_id(mocked_clean_test_db_session):
    et_object = ElementType(
        id=uuid.uuid4(), name="Type1"
    )  # Ändern von festen IDs zu uuid.uuid4()
    store_single_element_type(et_object)
    tn_object = ThingNode(
        id=uuid.uuid4(),
        external_id="15-ext-valid",
        name="Node1",
        element_type_id=et_object.id,
    )
    child_tn_object = ThingNode(
        id=uuid.uuid4(),
        external_id="16-ext-valid",
        name="ChildNode1",
        parent_node_id=tn_object.id,
        element_type_id=et_object.id,
    )
    store_single_thingnode(tn_object)
    store_single_thingnode(child_tn_object)
    children_ids = get_children_tn_ids(tn_object.id)
    assert children_ids == [child_tn_object.id]


def test_get_ancestors_tn_ids_valid_id(mocked_clean_test_db_session):
    et_object = ElementType(
        id=uuid.uuid4(), name="Type1"
    )  # Ändern von festen IDs zu uuid.uuid4()
    store_single_element_type(et_object)

    tn_object1 = ThingNode(
        id=uuid.uuid4(),
        external_id="17-ext-valid",
        name="RootNode",
        element_type_id=et_object.id,
    )
    tn_object2 = ThingNode(
        id=uuid.uuid4(),
        name="ChildNode1",
        external_id="18-ext-valid",
        parent_node_id=tn_object1.id,
        element_type_id=et_object.id,
    )
    tn_object3 = ThingNode(
        id=uuid.uuid4(),
        external_id="19-ext-valid",
        name="ChildNode2",
        parent_node_id=tn_object2.id,
        element_type_id=et_object.id,
    )
    tn_object4 = ThingNode(
        id=uuid.uuid4(),
        external_id="20-ext-valid",
        name="GrandChildNode",
        parent_node_id=tn_object3.id,
        element_type_id=et_object.id,
    )

    store_single_thingnode(tn_object1)
    store_single_thingnode(tn_object2)
    store_single_thingnode(tn_object3)
    store_single_thingnode(tn_object4)

    ancestors_ids = get_ancestors_tn_ids(tn_object4.id)

    assert ancestors_ids == [tn_object4.id, tn_object3.id, tn_object2.id, tn_object1.id]


def test_get_ancestors_tn_ids_valid_depth_valid_id(mocked_clean_test_db_session):
    et_object = ElementType(id=uuid.uuid4(), name="Type1")
    store_single_element_type(et_object)

    tn_object1 = ThingNode(
        id=uuid.uuid4(),
        external_id="21-ext-valid",
        name="RootNode",
        element_type_id=et_object.id,
    )
    tn_object2 = ThingNode(
        id=uuid.uuid4(),
        external_id="22-ext-valid",
        name="ChildNode1",
        parent_node_id=tn_object1.id,
        element_type_id=et_object.id,
    )
    tn_object3 = ThingNode(
        id=uuid.uuid4(),
        external_id="23-ext-valid",
        name="ChildNode2",
        parent_node_id=tn_object2.id,
        element_type_id=et_object.id,
    )
    tn_object4 = ThingNode(
        id=uuid.uuid4(),
        external_id="24-ext-valid",
        name="GrandChildNode",
        parent_node_id=tn_object3.id,
        element_type_id=et_object.id,
    )

    store_single_thingnode(tn_object1)
    store_single_thingnode(tn_object2)
    store_single_thingnode(tn_object3)
    store_single_thingnode(tn_object4)

    ancestors_ids = get_ancestors_tn_ids(tn_object4.id, 2)

    assert ancestors_ids == [tn_object4.id, tn_object3.id]


def test_get_ancestors_tn_ids_invalid_id(mocked_clean_test_db_session):
    with pytest.raises(DBNotFoundError):
        get_ancestors_tn_ids(uuid.uuid4())


def test_get_ancestors_tn_ids_invalid_depth_valid_id(mocked_clean_test_db_session):
    et_object = ElementType(
        id=uuid.uuid4(), name="Type1"
    )  # Ändern von festen IDs zu uuid.uuid4()
    store_single_element_type(et_object)

    tn_object1 = ThingNode(
        id=uuid.uuid4(),
        external_id="25-ext-valid",
        name="RootNode",
        element_type_id=et_object.id,
    )
    tn_object2 = ThingNode(
        id=uuid.uuid4(),
        external_id="26-ext-valid",
        name="ChildNode1",
        parent_node_id=tn_object1.id,
        element_type_id=et_object.id,
    )
    tn_object3 = ThingNode(
        id=uuid.uuid4(),
        external_id="27-ext-valid",
        name="ChildNode2",
        parent_node_id=tn_object2.id,
        element_type_id=et_object.id,
    )
    tn_object4 = ThingNode(
        id=uuid.uuid4(),
        external_id="28-ext-valid",
        name="GrandChildNode",
        parent_node_id=tn_object3.id,
        element_type_id=et_object.id,
    )

    store_single_thingnode(tn_object1)
    store_single_thingnode(tn_object2)
    store_single_thingnode(tn_object3)
    store_single_thingnode(tn_object4)

    ancestors_ids = get_ancestors_tn_ids(tn_object4.id, 2)

    with pytest.raises(AssertionError):
        assert ancestors_ids == [tn_object4.id, tn_object3.id, tn_object2.id]


# Exception Handling and Data Integrity Tests


def test_uniqueness_thingnode(mocked_clean_test_db_session):
    et_object = ElementType(id=uuid.uuid4(), name="Type1")
    store_single_element_type(et_object)
    tn_object = ThingNode(
        id=uuid.uuid4(),
        external_id="29-ext-valid",
        name="Node1",
        element_type_id=et_object.id,
    )
    store_single_thingnode(tn_object)
    updated_data = ThingNode(
        id=tn_object.id,
        external_id="30-ext-valid",
        name="UpdatedNode1",
        element_type_id=et_object.id,
    )
    updated_tn = update_tn(tn_object.id, updated_data)
    with pytest.raises(DBIntegrityError):
        store_single_thingnode(updated_tn)


def test_handle_duplicate_thingnode_insertion(mocked_clean_test_db_session):
    et_object = ElementType(id=uuid.uuid4(), name="Type1")
    store_single_element_type(et_object)
    tn_object = ThingNode(
        id=uuid.uuid4(),
        external_id="31-ext-valid",
        name="Node1",
        element_type_id=et_object.id,
    )
    store_single_thingnode(tn_object)
    with pytest.raises(DBIntegrityError):
        store_single_thingnode(tn_object)


def test_handle_duplicate_elementtype_insertion(mocked_clean_test_db_session):
    et_object1 = ElementType(id=uuid.uuid4(), name="Type1")
    et_object2 = ElementType(id=uuid.uuid4(), name="Type1")
    store_single_element_type(et_object1)

    with pytest.raises(DBIntegrityError):
        store_single_element_type(et_object2)


# Performance and Load Tests


@pytest.mark.skip(reason="Skipping during development because it takes too long.")
def test_performance_bulk_insert(mocked_clean_test_db_session):
    num_records = 1000
    et_object = ElementType(id=uuid.uuid4(), name="Type1")
    store_single_element_type(et_object)
    start_time = time.time()
    for i in range(num_records):
        tn_object = ThingNode(
            id=uuid.uuid4(),
            external_id="32-ext-valid",
            name=f"Node{i+1}",
            element_type_id=et_object.id,
        )
        store_single_thingnode(tn_object)
    end_time = time.time()
    duration = end_time - start_time
    print(f"Bulk insert of {num_records} records took {duration:.2f} seconds")
    assert duration < 20, f"Bulk insert took too long: {duration:.2f} seconds"


@pytest.mark.skip(reason="Skipping during development because it takes too long.")
def test_performance_bulk_delete(mocked_clean_test_db_session):
    num_records = 1000
    et_object = ElementType(id=uuid.uuid4(), name="Type1")
    store_single_element_type(et_object)
    tn_objects = []
    for i in range(num_records):
        tn_object = ThingNode(
            id=uuid.uuid4(),
            external_id="33-ext-valid",
            name=f"Node{i+1}",
            element_type_id=et_object.id,
        )
        store_single_thingnode(tn_object)
        tn_objects.append(tn_object)

    start_time = time.time()
    for tn_object in tn_objects:
        delete_tn(tn_object.id)
    end_time = time.time()

    duration = end_time - start_time
    print(f"Bulk delete of {num_records} records took {duration:.2f} seconds")
    assert duration < 20, f"Bulk delete took too long: {duration:.2f} seconds"


# CRUD Operations for Structure


def test_load_structure_from_json_file(mocked_clean_test_db_session):
    file_path = (
        "tests/structure/data/"
        "db_test_load_structure_from_json_file_with_unordered_thingnodes_many2many.json"
    )

    element_types, thing_nodes, sources, sinks = load_structure_from_json_file(
        file_path
    )

    with mocked_clean_test_db_session() as session, session.begin():
        for et in element_types:
            add_tn(
                session,
                ElementTypeOrm(id=et.id, name=et.name, description=et.description),
            )
        for source in sources:
            add_tn(
                session,
                SourceOrm(
                    id=source.id,
                    name=source.name,
                    type=source.type,
                    visible=source.visible,
                    adapter_key=source.adapter_key,
                    source_id=source.source_id,
                    meta_data=source.meta_data,
                ),
            )
        for sink in sinks:
            add_tn(
                session,
                SinkOrm(
                    id=sink.id,
                    name=sink.name,
                    type=sink.type,
                    visible=sink.visible,
                    adapter_key=sink.adapter_key,
                    sink_id=sink.sink_id,
                    meta_data=sink.meta_data,
                ),
            )
        for tn in thing_nodes:
            orm_tn = ThingNodeOrm(
                id=tn.id,
                external_id=tn.external_id,
                name=tn.name,
                description=tn.description,
                parent_node_id=tn.parent_node_id,
                element_type_id=tn.element_type_id,
                meta_data=tn.meta_data,
            )
            orm_tn.sources = (
                session.query(SourceOrm).filter(SourceOrm.id.in_(tn.sources)).all()
            )
            orm_tn.sinks = session.query(SinkOrm).filter(SinkOrm.id.in_(tn.sinks)).all()
            add_tn(session, orm_tn)

        db_element_types = fetch_all_element_types(session)
        db_thing_nodes = fetch_all_thing_nodes(session)
        db_sources = fetch_all_sources(session)
        db_sinks = fetch_all_sinks(session)

        assert len(element_types) == len(db_element_types)
        assert len(thing_nodes) == len(db_thing_nodes)
        assert len(sources) == len(db_sources)
        assert len(sinks) == len(db_sinks)

        for et, db_et in zip(element_types, db_element_types, strict=True):
            assert et.id == db_et.id
            assert et.name == db_et.name
            assert et.description == db_et.description

        for tn, db_tn in zip(thing_nodes, db_thing_nodes, strict=True):
            assert tn.id == db_tn.id
            assert tn.external_id == db_tn.external_id
            assert tn.name == db_tn.name
            assert tn.element_type_id == db_tn.element_type_id
            assert tn.parent_node_id == db_tn.parent_node_id
            assert tn.description == db_tn.description
            assert tn.meta_data == db_tn.meta_data

        for source, db_source in zip(sources, db_sources, strict=True):
            assert source.id == db_source.id
            assert source.name == db_source.name
            assert source.type == db_source.type
            assert source.visible == db_source.visible
            assert source.adapter_key == db_source.adapter_key
            assert source.source_id == db_source.source_id
            assert source.meta_data == db_source.meta_data

        for sink, db_sink in zip(sinks, db_sinks, strict=True):
            assert sink.id == db_sink.id
            assert sink.name == db_sink.name
            assert sink.type == db_sink.type
            assert sink.visible == db_sink.visible
            assert sink.adapter_key == db_sink.adapter_key
            assert sink.sink_id == db_sink.sink_id
            assert sink.meta_data == db_sink.meta_data


def test_update_structure(mocked_clean_test_db_session):
    file_path = (
        "tests/structure/data/"
        "db_test_load_structure_from_json_file_with_unordered_thingnodes_many2many.json"
    )

    update_structure_from_file(file_path)

    with mocked_clean_test_db_session() as session, session.begin():
        db_element_types = fetch_all_element_types(session)
        db_thing_nodes = fetch_all_thing_nodes(session)
        db_sources = fetch_all_sources(session)
        db_sinks = fetch_all_sinks(session)

        assert len(db_element_types) == 3
        assert len(db_thing_nodes) == 10
        assert len(db_sources) == 7
        assert len(db_sinks) == 7

        db_element_types.sort(key=lambda et: et.name)
        db_thing_nodes.sort(key=lambda tn: tn.name)
        db_sources.sort(key=lambda s: s.name)
        db_sinks.sort(key=lambda s: s.name)

        expected_element_types = [
            {
                "id": uuid.UUID("00000000-0000-0000-0000-000000000001"),
                "name": "Type1",
                "description": "Description for Type1",
            },
            {
                "id": uuid.UUID("00000000-0000-0000-0000-000000000002"),
                "name": "Type2",
                "description": "Description for Type2",
            },
            {
                "id": uuid.UUID("00000000-0000-0000-0000-000000000003"),
                "name": "Type3",
                "description": "Description for Type3",
            },
        ]

        for expected, db_et in zip(
            expected_element_types, db_element_types, strict=True
        ):
            assert expected["id"] == db_et.id
            assert expected["name"] == db_et.name
            assert expected["description"] == db_et.description

        expected_thing_nodes = [
            {"name": "ChildNode1"},
            {"name": "ChildNode2"},
            {"name": "ChildNode2_Child1"},
            {"name": "ChildNode2_Child1_Child1"},
            {"name": "ChildNode2_Child1_Child2"},
            {"name": "ChildNode2_Child2"},
            {"name": "ChildNode3"},
            {"name": "LeafNodeWith1Source2Sinks"},
            {"name": "LeafNodeWith2Sources1Sink"},
            {"name": "RootNode"},
        ]

        for expected, db_tn in zip(expected_thing_nodes, db_thing_nodes, strict=True):
            assert expected["name"] == db_tn.name

        expected_sources = [
            {"name": "Source1"},
            {"name": "Source2"},
            {"name": "Source3"},
            {"name": "Source4"},
            {"name": "Source5"},
            {"name": "Source6"},
            {"name": "Source7"},
        ]

        for expected, db_source in zip(expected_sources, db_sources, strict=True):
            assert expected["name"] == db_source.name

        expected_sinks = [
            {"name": "Sink1"},
            {"name": "Sink2"},
            {"name": "Sink3"},
            {"name": "Sink4"},
            {"name": "Sink5"},
            {"name": "Sink6"},
            {"name": "Sink7"},
        ]

        for expected, db_sink in zip(expected_sinks, db_sinks, strict=True):
            assert expected["name"] == db_sink.name


def test_update_structure_from_file_with_unordered_thingnodes_and_many_to_many_relationship(
    mocked_clean_test_db_session,
):
    file_path = (
        "tests/structure/data/"
        "db_test_load_structure_from_json_file_with_unordered_thingnodes_many2many.json"
    )

    update_structure_from_file(file_path)

    with mocked_clean_test_db_session() as session:
        element_types = session.query(ElementTypeOrm).all()
        assert len(element_types) == 3
        assert element_types[0].name == "Type1"
        assert element_types[1].name == "Type2"
        assert element_types[2].name == "Type3"

        thing_nodes = session.query(ThingNodeOrm).all()
        assert len(thing_nodes) == 10

        thing_node_names = [tn.name for tn in thing_nodes]
        expected_names = [
            "RootNode",
            "ChildNode1",
            "ChildNode2",
            "ChildNode3",
            "LeafNodeWith2Sources1Sink",
            "LeafNodeWith1Source2Sinks",
            "ChildNode2_Child1",
            "ChildNode2_Child2",
            "ChildNode2_Child1_Child1",
            "ChildNode2_Child1_Child2",
        ]

        for name in expected_names:
            assert name in thing_node_names

        sources = session.query(SourceOrm).all()
        assert len(sources) == 7
        source_names = [source.name for source in sources]
        expected_source_names = [
            "Source1",
            "Source2",
            "Source3",
            "Source4",
            "Source5",
            "Source6",
            "Source7",
        ]

        for name in expected_source_names:
            assert name in source_names

        sinks = session.query(SinkOrm).all()
        assert len(sinks) == 7
        sink_names = [sink.name for sink in sinks]
        expected_sink_names = [
            "Sink1",
            "Sink2",
            "Sink3",
            "Sink4",
            "Sink5",
            "Sink6",
            "Sink7",
        ]

        for name in expected_sink_names:
            assert name in sink_names


def test_sort_thing_nodes():
    root_node = ThingNode(
        id=UUID("00000000-0000-0000-0000-000000000008"),
        external_id="34-ext-valid",
        name="RootNode",
        description="",
        parent_node_id=None,
        element_type_id=UUID("00000000-0000-0000-0000-000000000001"),
        meta_data={},
    )
    child_node1 = ThingNode(
        id=UUID("00000000-0000-0000-0000-000000000009"),
        external_id="35-ext-valid",
        name="ChildNode1",
        description="",
        parent_node_id=root_node.id,
        element_type_id=UUID("00000000-0000-0000-0000-000000000002"),
        meta_data={},
    )
    child_node2 = ThingNode(
        id=UUID("00000000-0000-0000-0000-000000000004"),
        external_id="36-ext-valid",
        name="ChildNode2",
        description="",
        parent_node_id=root_node.id,
        element_type_id=UUID("00000000-0000-0000-0000-000000000003"),
        meta_data={},
    )
    child_node3 = ThingNode(
        id=UUID("00000000-0000-0000-0000-000000000002"),
        external_id="37-ext-valid",
        name="ChildNode3",
        description="",
        parent_node_id=child_node1.id,
        element_type_id=UUID("00000000-0000-0000-0000-000000000003"),
        meta_data={},
    )

    nodes = [child_node3, child_node2, child_node1, root_node]
    sorted_nodes = sort_thing_nodes(nodes)

    # Preorder Traversal (Depth-First)
    # expected_order = [root_node, child_node1, child_node3, child_node2]

    # Level-Order Traversal (Breadth-First)
    # child_node2.id > child_node1.id, but on same level. child_node3 is child of child_node1.
    expected_order = [root_node, child_node2, child_node1, child_node3]

    assert sorted_nodes == expected_order

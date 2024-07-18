import json
import time
import uuid
from sqlite3 import Connection as SQLite3Connection

import pytest
from pydantic import ValidationError
from sqlalchemy import event
from sqlalchemy.future.engine import Engine

from hetdesrun.persistence.structure_service_dbmodels import (
    ElementTypeOrm,
    SinkOrm,
    SourceOrm,
    ThingNodeOrm,
)
from hetdesrun.structure.db.exceptions import DBIntegrityError, DBNotFoundError
from hetdesrun.structure.db.orm_service import (
    add_et,
    add_tn,
    delete_et,
    delete_et_cascade,
    delete_tn,
    fetch_all_element_types,
    fetch_all_sinks,
    fetch_all_sources,
    fetch_all_thing_nodes,
    fetch_et_by_id,
    fetch_tn_by_id,
    fetch_tn_child_ids_by_parent_id,
    get_ancestors_tn_ids,
    get_children_tn_ids,
    read_single_element_type,
    read_single_thingnode,
    sort_thing_nodes,
    store_single_element_type,
    store_single_thingnode,
    update_et,
    update_structure_from_file,
    update_tn,
)
from hetdesrun.structure.models import (
    ElementType,
    ThingNode,
)

ThingNode.update_forward_refs()

# Fixture definitions


@pytest.fixture()
def _db_test_thing_node_hierarchy(mocked_clean_test_db_session):
    file_path = "tests/structure/data/" "db_test_structure.json"
    update_structure_from_file(file_path)


@pytest.fixture()
def _db_comprehensive_cascade_deletion(mocked_clean_test_db_session):
    file_path = "tests/structure/data/" "db_test_structure.json"
    update_structure_from_file(file_path)


@pytest.fixture()
def _db_test_thing_node_many_children(mocked_clean_test_db_session):
    file_path = "tests/structure/data/" "db_test_structure.json"
    update_structure_from_file(file_path)


@pytest.fixture()
def _db_test_unordered_structure(mocked_clean_test_db_session):
    file_path = "tests/structure/data/" "db_test_unordered_structure.json"
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
    et_orm_object = ElementTypeOrm(
        id=uuid.uuid4(), name="TypeOrm1", external_id="external_test_id", stakeholder_key="shk_test"
    )
    add_et(session, et_orm_object)
    tn_orm_object = ThingNodeOrm(id=uuid.uuid4(), name=123, element_type_id=uuid.uuid4())

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
            element_type_external_id="et-ext-valid",
            external_id="38-1-ext-valid",
            stakeholder_key="shk_test",
        )
    except ValidationError:
        pytest.fail("Valid ThingNode creation raised ValidationError unexpectedly.")


def test_invalid_element_type_creation():
    with pytest.raises(ValidationError):
        ElementType(id="invalid", name=123)


def test_valid_element_type_creation():
    try:
        ElementType(
            id=uuid.uuid4(),
            name="valid_name",
            external_id="external_test_id",
            stakeholder_key="shk_test",
        )
    except ValidationError:
        pytest.fail("Valid ElementType creation raised ValidationError unexpectedly.")


# CRUD ORM Operation Tests


def test_add_et_tn(mocked_clean_test_db_session):
    session = mocked_clean_test_db_session()
    et_orm_object = ElementTypeOrm(
        id=uuid.uuid4(),
        name="TypeOrm1",
        external_id="element_type_external_id",
        stakeholder_key="stakeholder_key_value",
    )
    add_et(session, et_orm_object)
    tn_orm_object = ThingNodeOrm(
        id=uuid.uuid4(),
        name="NodeOrm1",
        element_type_id=et_orm_object.id,
        external_id="2-ext-valid",
        element_type_external_id="element_type_external_id",
        stakeholder_key="stakeholder_key_value",
    )
    add_tn(session, tn_orm_object)
    retrieved_et_orm = fetch_et_by_id(session, et_orm_object.id)
    retrieved_tn_orm = fetch_tn_by_id(session, tn_orm_object.id)
    assert et_orm_object == retrieved_et_orm
    assert tn_orm_object == retrieved_tn_orm


def test_add_et_tn_integrity_error(mocked_clean_test_db_session):
    session = mocked_clean_test_db_session()
    et_orm_object = ElementTypeOrm(
        id=uuid.uuid4(),
        name="TypeOrm1",
        external_id="element_type_external_id",
        stakeholder_key="stakeholder_key_value",
    )
    add_et(session, et_orm_object)
    tn_orm_object = ThingNodeOrm(
        id=uuid.uuid4(),
        element_type_id=et_orm_object.id,
        external_id="2-ext-valid",
        stakeholder_key="stakeholder_key_value",
    )

    with pytest.raises(DBIntegrityError):
        add_tn(session, tn_orm_object)


# CRUD Operations for ThingNode


def test_store_single_thingnode(mocked_clean_test_db_session):
    et_object = ElementType(
        id=uuid.uuid4(),
        name="Type1",
        external_id="element_type_external_id",
        stakeholder_key="stakeholder_key_value",
    )
    store_single_element_type(et_object)
    tn_object = ThingNode(
        id=uuid.uuid4(),
        name="Node1",
        element_type_id=et_object.id,
        element_type_external_id="element_type_external_id",
        external_id="3-ext-valid",
        stakeholder_key="stakeholder_key_value",
    )
    store_single_thingnode(tn_object)
    retrieved_tn = read_single_thingnode(tn_object.id)
    assert tn_object == retrieved_tn


def test_read_single_thingnode(mocked_clean_test_db_session):
    tn_id = uuid.uuid4()
    with pytest.raises(DBNotFoundError):
        read_single_thingnode(tn_id)


def test_storing_and_receiving(mocked_clean_test_db_session):
    et_object = ElementType(
        id=uuid.uuid4(),
        name="Type1",
        external_id="element_type_external_id",
        stakeholder_key="stakeholder_key_value",
    )
    store_single_element_type(et_object)

    tn_id = uuid.uuid4()
    tn_object = ThingNode(
        id=tn_id,
        name="Node1",
        element_type_id=et_object.id,
        element_type_external_id="element_type_external_id",
        external_id="4-ext-valid",
        stakeholder_key="stakeholder_key_value",
    )
    store_single_thingnode(tn_object)

    received_tn_object = read_single_thingnode(tn_id)
    assert tn_object == received_tn_object

    wrong_tn_id = uuid.uuid4()
    with pytest.raises(DBNotFoundError):
        read_single_thingnode(wrong_tn_id)


def test_updating_existing_tn(mocked_clean_test_db_session):
    et_object = ElementType(
        id=uuid.uuid4(),
        name="Type1",
        external_id="element_type_external_id",
        stakeholder_key="stakeholder_key_value",
    )
    store_single_element_type(et_object)
    tn_id = uuid.uuid4()
    tn_object = ThingNode(
        id=tn_id,
        external_id="5-ext-valid",
        name="Node1",
        element_type_id=et_object.id,
        element_type_external_id="element_type_external_id",
        stakeholder_key="stakeholder_key_value",
    )
    store_single_thingnode(tn_object)

    updated_data = ThingNode(
        id=tn_id,
        external_id="6-updt ext-valid",
        name="UpdatedNode1",
        element_type_id=et_object.id,
        element_type_external_id="element_type_external_id",
        stakeholder_key="stakeholder_key_value",
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
        element_type_external_id="element_type_external_id",
        stakeholder_key="stakeholder_key_value",
    )
    with pytest.raises(DBNotFoundError):
        update_tn(non_existent_tn_id, updated_data)


def test_update_thingnode_valid_data(mocked_clean_test_db_session):
    et_object = ElementType(
        id=uuid.uuid4(),
        name="Type1",
        external_id="element_type_external_id",
        stakeholder_key="stakeholder_key_value",
    )
    store_single_element_type(et_object)
    tn_object = ThingNode(
        id=uuid.uuid4(),
        external_id="8-ext-valid",
        name="Node1",
        element_type_id=et_object.id,
        element_type_external_id="element_type_external_id",
        stakeholder_key="stakeholder_key_value",
    )
    store_single_thingnode(tn_object)
    updated_data = ThingNode(
        id=tn_object.id,
        external_id="9-updt-ext-valid",
        name="UpdatedNode1",
        element_type_id=et_object.id,
        element_type_external_id="element_type_external_id",
        stakeholder_key="stakeholder_key_value",
    )
    updated_tn = update_tn(tn_object.id, updated_data)
    assert updated_tn.name == "UpdatedNode1"


@pytest.mark.usefixtures("_db_comprehensive_cascade_deletion")
def test_delete_thingnode_valid_id(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        root_node = (
            session.query(ThingNodeOrm)
            .filter(ThingNodeOrm.external_id == "Wasserwerk1")
            .one_or_none()
        )
        child_node1 = (
            session.query(ThingNodeOrm)
            .filter(ThingNodeOrm.external_id == "Wasserwerk1_Anlage1")
            .one_or_none()
        )
        child_node2 = (
            session.query(ThingNodeOrm)
            .filter(ThingNodeOrm.external_id == "Wasserwerk1_Anlage2")
            .one_or_none()
        )

        assert root_node is not None
        assert child_node1 is not None
        assert child_node2 is not None

        root_node_id = root_node.id
        child_node1_id = child_node1.id
        child_node2_id = child_node2.id

        delete_tn(root_node_id)

        with pytest.raises(DBNotFoundError):
            read_single_thingnode(root_node_id)
        with pytest.raises(DBNotFoundError):
            read_single_thingnode(child_node1_id)
        with pytest.raises(DBNotFoundError):
            read_single_thingnode(child_node2_id)


def test_delete_thingnode_invalid_id(mocked_clean_test_db_session):
    with pytest.raises(DBNotFoundError):
        delete_tn(uuid.uuid4())


def test_delete_thingnode_integrity_error(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        et_object = ElementType(
            id=uuid.uuid4(),
            external_id="type1-ext-id",
            stakeholder_key="stakeholder1",
            name="Type1",
            description="Description of Type1",
        )
        store_single_element_type(et_object)

        parent_tn_object = ThingNode(
            id=uuid.uuid4(),
            external_id="10-ext-valid",
            name="Node1",
            stakeholder_key="stakeholder1",
            element_type_id=et_object.id,
            element_type_external_id="type1-ext-id",
        )
        child_tn_object = ThingNode(
            id=uuid.uuid4(),
            external_id="11-ext-valid",
            name="Node2",
            stakeholder_key="stakeholder1",
            parent_node_id=parent_tn_object.id,
            element_type_id=et_object.id,
            element_type_external_id="type1-ext-id",
        )
        store_single_thingnode(parent_tn_object)
        store_single_thingnode(child_tn_object)

        assert (
            session.query(ThingNodeOrm).filter_by(id=parent_tn_object.id).one_or_none() is not None
        )
        assert (
            session.query(ThingNodeOrm).filter_by(id=child_tn_object.id).one_or_none() is not None
        )

        delete_tn(parent_tn_object.id)

        assert session.query(ThingNodeOrm).filter_by(id=parent_tn_object.id).one_or_none() is None
        assert session.query(ThingNodeOrm).filter_by(id=child_tn_object.id).one_or_none() is None


# CRUD Operations for ElementType


def test_store_single_element_type(mocked_clean_test_db_session):
    et_object = ElementType(
        id=uuid.uuid4(),
        external_id="type1-ext-id",
        stakeholder_key="stakeholder1",
        name="Type1",
        description="Description of Type1",
    )
    store_single_element_type(et_object)
    retrieved_et = read_single_element_type(et_object.id)
    assert et_object == retrieved_et


@pytest.mark.usefixtures("mocked_clean_test_db_session")
def test_update_element_type_valid_data(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        et_object = ElementType(
            id=uuid.uuid4(),
            external_id="type1-ext-id",
            stakeholder_key="stakeholder1",
            name="Type1",
            description="Description of Type1",
        )
        store_single_element_type(et_object)

        et_update = et_object
        et_update.name = "UpdatedType1"

        update_et(et_object.id, et_update)

        updated_et = fetch_et_by_id(session, et_object.id)

        assert updated_et.name == "UpdatedType1"


def test_delete_element_type(mocked_clean_test_db_session):
    et_object = ElementType(
        id=uuid.uuid4(),
        external_id="type1-ext-id",
        stakeholder_key="stakeholder1",
        name="Type1",
        description="Description of Type1",
    )
    store_single_element_type(et_object)

    delete_et(et_object.id)

    with pytest.raises(DBNotFoundError):
        read_single_element_type(et_object.id)


def test_delete_element_type_with_associated_thingnode(mocked_clean_test_db_session):
    et_object = ElementType(
        id=uuid.uuid4(),
        external_id="type1-ext-id",
        stakeholder_key="stakeholder1",
        name="Type1",
        description="Description of Type1",
    )
    store_single_element_type(et_object)

    tn_object = ThingNode(
        id=uuid.uuid4(),
        external_id="12-ext-valid",
        name="Node1",
        stakeholder_key="stakeholder1",
        element_type_id=et_object.id,
        element_type_external_id=et_object.external_id,
    )
    store_single_thingnode(tn_object)

    with pytest.raises(DBIntegrityError):
        delete_et(et_object.id)


def test_delete_cascade_element_type(mocked_clean_test_db_session):
    et_object = ElementType(
        id=uuid.uuid4(),
        external_id="type1-ext-id",
        stakeholder_key="stakeholder1",
        name="Type1",
        description="Description of Type1",
    )
    store_single_element_type(et_object)

    tn_object = ThingNode(
        id=uuid.uuid4(),
        external_id="13-ext-valid",
        name="Node1",
        stakeholder_key="stakeholder1",
        element_type_id=et_object.id,
        element_type_external_id=et_object.external_id,
    )
    store_single_thingnode(tn_object)

    delete_et_cascade(et_object.id)

    with pytest.raises(DBNotFoundError):
        read_single_element_type(et_object.id)


def test_fetch_tn_by_valid_id(mocked_clean_test_db_session):
    et_object = ElementType(
        id=uuid.uuid4(),
        external_id="type1-ext-id",
        stakeholder_key="stakeholder1",
        name="Type1",
        description="Description of Type1",
    )
    store_single_element_type(et_object)

    tn_object = ThingNode(
        id=uuid.uuid4(),
        external_id="14-ext-valid",
        name="Node1",
        stakeholder_key="stakeholder1",
        element_type_id=et_object.id,
        element_type_external_id=et_object.external_id,
    )
    store_single_thingnode(tn_object)

    with mocked_clean_test_db_session() as session:
        retrieved_tn = fetch_tn_by_id(session, tn_object.id)
        assert retrieved_tn.id == tn_object.id


def test_fetch_tn_by_invalid_id(mocked_clean_test_db_session):
    with pytest.raises(DBNotFoundError):
        fetch_tn_by_id(mocked_clean_test_db_session(), uuid.uuid4())


@pytest.mark.usefixtures("_db_test_thing_node_many_children")
def test_fetch_tn_child_ids_by_parent_id(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        parent_node = session.query(ThingNodeOrm).filter_by(external_id="Wasserwerk1").one_or_none()
        assert parent_node is not None, "Parent node not found in the database"

        parent_id = parent_node.id

        tn_child_list = fetch_tn_child_ids_by_parent_id(session, parent_id)

        assert len(tn_child_list) > 0  # Ensure that the list is not empty
        assert all(
            isinstance(child_id, uuid.UUID) for child_id in tn_child_list
        )  # Ensure all elements are UUIDs


@pytest.mark.usefixtures("_db_test_thing_node_many_children")
def test_fetch_tn_child_ids_by_parent_id_dbnotfound(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        non_existent_uuid = uuid.uuid4()

        with pytest.raises(DBNotFoundError):
            fetch_tn_child_ids_by_parent_id(session, non_existent_uuid)


# Tests for Hierarchy and Relationships
@pytest.mark.usefixtures("_db_test_thing_node_hierarchy")
def test_thing_node_hierarchy(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        # Fetch all elements from the database
        element_types_in_db = fetch_all_element_types(session)
        thing_nodes_in_db = fetch_all_thing_nodes(session)
        sources_in_db = fetch_all_sources(session)
        sinks_in_db = fetch_all_sinks(session)

        # Ensure the counts match the expected values
        expected_element_types_count = 3
        expected_thing_nodes_count = 7
        expected_sources_count = 2
        expected_sinks_count = 2

        assert (
            len(element_types_in_db) == expected_element_types_count
        ), "Mismatch in element types count"
        assert len(thing_nodes_in_db) == expected_thing_nodes_count, "Mismatch in thing nodes count"
        assert len(sources_in_db) == expected_sources_count, "Mismatch in sources count"
        assert len(sinks_in_db) == expected_sinks_count, "Mismatch in sinks count"


def test_get_children_tn_ids_valid_id(mocked_clean_test_db_session):
    with mocked_clean_test_db_session():
        et_object = ElementType(
            id=uuid.uuid4(),
            external_id="type1-ext-id",
            stakeholder_key="stakeholder1",
            name="Type1",
            description="Description of Type1",
        )
        store_single_element_type(et_object)

        tn_object = ThingNode(
            id=uuid.uuid4(),
            external_id="15-ext-valid",
            name="Node1",
            stakeholder_key="stakeholder1",
            element_type_id=et_object.id,
            element_type_external_id="type1-ext-id",
        )
        store_single_thingnode(tn_object)

        child_tn_object = ThingNode(
            id=uuid.uuid4(),
            external_id="16-ext-valid",
            name="ChildNode1",
            stakeholder_key="stakeholder1",
            parent_node_id=tn_object.id,
            element_type_id=et_object.id,
            element_type_external_id="type1-ext-id",
        )
        store_single_thingnode(child_tn_object)

        children_ids = get_children_tn_ids(tn_object.id)

        assert children_ids == [child_tn_object.id]


def test_get_ancestors_tn_ids_valid_id(mocked_clean_test_db_session):
    with mocked_clean_test_db_session():
        et_object = ElementType(
            id=uuid.uuid4(),
            external_id="type1-ext-id",
            stakeholder_key="stakeholder1",
            name="Type1",
            description="Description of Type1",
        )
        store_single_element_type(et_object)

        tn_object1 = ThingNode(
            id=uuid.uuid4(),
            external_id="17-ext-valid",
            name="RootNode",
            stakeholder_key="stakeholder1",
            element_type_id=et_object.id,
            element_type_external_id="type1-ext-id",
        )
        tn_object2 = ThingNode(
            id=uuid.uuid4(),
            name="ChildNode1",
            external_id="18-ext-valid",
            parent_node_id=tn_object1.id,
            stakeholder_key="stakeholder1",
            element_type_id=et_object.id,
            element_type_external_id="type1-ext-id",
        )
        tn_object3 = ThingNode(
            id=uuid.uuid4(),
            external_id="19-ext-valid",
            name="ChildNode2",
            parent_node_id=tn_object2.id,
            stakeholder_key="stakeholder1",
            element_type_id=et_object.id,
            element_type_external_id="type1-ext-id",
        )
        tn_object4 = ThingNode(
            id=uuid.uuid4(),
            external_id="20-ext-valid",
            name="GrandChildNode",
            parent_node_id=tn_object3.id,
            stakeholder_key="stakeholder1",
            element_type_id=et_object.id,
            element_type_external_id="type1-ext-id",
        )

        store_single_thingnode(tn_object1)
        store_single_thingnode(tn_object2)
        store_single_thingnode(tn_object3)
        store_single_thingnode(tn_object4)

        ancestors_ids = get_ancestors_tn_ids(tn_object4.id)

        assert ancestors_ids == [tn_object4.id, tn_object3.id, tn_object2.id, tn_object1.id]


def test_get_ancestors_tn_ids_valid_depth_valid_id(mocked_clean_test_db_session):
    with mocked_clean_test_db_session():
        et_object = ElementType(
            id=uuid.uuid4(),
            external_id="type1-ext-id",
            stakeholder_key="stakeholder1",
            name="Type1",
            description="Description of Type1",
        )
        store_single_element_type(et_object)

        tn_object1 = ThingNode(
            id=uuid.uuid4(),
            external_id="21-ext-valid",
            name="RootNode",
            stakeholder_key="stakeholder1",
            element_type_id=et_object.id,
            element_type_external_id="type1-ext-id",
        )
        tn_object2 = ThingNode(
            id=uuid.uuid4(),
            external_id="22-ext-valid",
            name="ChildNode1",
            parent_node_id=tn_object1.id,
            stakeholder_key="stakeholder1",
            element_type_id=et_object.id,
            element_type_external_id="type1-ext-id",
        )
        tn_object3 = ThingNode(
            id=uuid.uuid4(),
            external_id="23-ext-valid",
            name="ChildNode2",
            parent_node_id=tn_object2.id,
            stakeholder_key="stakeholder1",
            element_type_id=et_object.id,
            element_type_external_id="type1-ext-id",
        )
        tn_object4 = ThingNode(
            id=uuid.uuid4(),
            external_id="24-ext-valid",
            name="GrandChildNode",
            parent_node_id=tn_object3.id,
            stakeholder_key="stakeholder1",
            element_type_id=et_object.id,
            element_type_external_id="type1-ext-id",
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
    with mocked_clean_test_db_session():
        et_object = ElementType(
            id=uuid.uuid4(),
            external_id="type1-ext-id",
            stakeholder_key="stakeholder1",
            name="Type1",
            description="Description of Type1",
        )
        store_single_element_type(et_object)

        tn_object1 = ThingNode(
            id=uuid.uuid4(),
            external_id="25-ext-valid",
            name="RootNode",
            stakeholder_key="stakeholder1",
            element_type_id=et_object.id,
            element_type_external_id="type1-ext-id",
        )
        tn_object2 = ThingNode(
            id=uuid.uuid4(),
            external_id="26-ext-valid",
            name="ChildNode1",
            parent_node_id=tn_object1.id,
            stakeholder_key="stakeholder1",
            element_type_id=et_object.id,
            element_type_external_id="type1-ext-id",
        )
        tn_object3 = ThingNode(
            id=uuid.uuid4(),
            external_id="27-ext-valid",
            name="ChildNode2",
            parent_node_id=tn_object2.id,
            stakeholder_key="stakeholder1",
            element_type_id=et_object.id,
            element_type_external_id="type1-ext-id",
        )
        tn_object4 = ThingNode(
            id=uuid.uuid4(),
            external_id="28-ext-valid",
            name="GrandChildNode",
            parent_node_id=tn_object3.id,
            stakeholder_key="stakeholder1",
            element_type_id=et_object.id,
            element_type_external_id="type1-ext-id",
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
    with mocked_clean_test_db_session():
        et_object = ElementType(
            id=uuid.uuid4(),
            external_id="type1-ext-id",
            stakeholder_key="stakeholder1",
            name="Type1",
            description="Description of Type1",
        )
        store_single_element_type(et_object)

        tn_object = ThingNode(
            id=uuid.uuid4(),
            external_id="29-ext-valid",
            name="Node1",
            stakeholder_key="stakeholder1",
            element_type_id=et_object.id,
            element_type_external_id="type1-ext-id",
        )
        store_single_thingnode(tn_object)

        updated_data = ThingNode(
            id=tn_object.id,
            external_id="30-ext-valid",
            name="UpdatedNode1",
            stakeholder_key="stakeholder1",
            element_type_id=et_object.id,
            element_type_external_id="type1-ext-id",
        )

        updated_tn = update_tn(tn_object.id, updated_data)

        with pytest.raises(DBIntegrityError):
            store_single_thingnode(updated_tn)


def test_handle_duplicate_thingnode_insertion(mocked_clean_test_db_session):
    et_object = ElementType(
        id=uuid.uuid4(),
        external_id="type1-ext-id",
        stakeholder_key="stakeholder1",
        name="Type1",
        description="Description of Type1",
    )
    store_single_element_type(et_object)
    tn_object = ThingNode(
        id=uuid.uuid4(),
        external_id="31-ext-valid",
        name="Node1",
        stakeholder_key="stakeholder1",
        element_type_id=et_object.id,
        element_type_external_id=et_object.external_id,
    )
    store_single_thingnode(tn_object)
    with pytest.raises(DBIntegrityError):
        store_single_thingnode(tn_object)


# Performance and Load Tests


@pytest.mark.skip(reason="Skipping during development because it takes too long.")
def test_performance_bulk_insert(mocked_clean_test_db_session):
    num_records = 1000
    et_object = ElementType(
        id=uuid.uuid4(),
        external_id="type1-ext-id",
        stakeholder_key="stakeholder1",
        name="Type1",
        description="Description of Type1",
    )
    store_single_element_type(et_object)
    start_time = time.time()
    for i in range(num_records):
        tn_object = ThingNode(
            id=uuid.uuid4(),
            external_id=f"32-ext-valid-{i}",
            name=f"Node{i+1}",
            stakeholder_key="stakeholder1",
            element_type_id=et_object.id,
            element_type_external_id=et_object.external_id,
        )
        store_single_thingnode(tn_object)
    end_time = time.time()
    duration = end_time - start_time
    print(f"Bulk insert of {num_records} records took {duration:.2f} seconds")
    assert duration < 20, f"Bulk insert took too long: {duration:.2f} seconds"


@pytest.mark.skip(reason="Skipping during development because it takes too long.")
def test_performance_bulk_delete(mocked_clean_test_db_session):
    num_records = 1000
    et_object = ElementType(
        id=uuid.uuid4(),
        external_id="type1-ext-id",
        stakeholder_key="stakeholder1",
        name="Type1",
        description="Description of Type1",
    )
    store_single_element_type(et_object)
    tn_objects = []
    for i in range(num_records):
        tn_object = ThingNode(
            id=uuid.uuid4(),
            external_id=f"33-ext-valid-{i}",
            name=f"Node{i+1}",
            stakeholder_key="stakeholder1",
            element_type_id=et_object.id,
            element_type_external_id=et_object.external_id,
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


@pytest.mark.usefixtures("_db_test_unordered_structure")
def test_load_unordered_structure_from_json_file(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session, session.begin():
        db_element_types = fetch_all_element_types(session)
        db_thing_nodes = fetch_all_thing_nodes(session)
        db_sources = fetch_all_sources(session)
        db_sinks = fetch_all_sinks(session)

        assert len(db_element_types) > 0
        assert len(db_thing_nodes) > 0
        assert len(db_sources) > 0
        assert len(db_sinks) > 0

        element_type_ids_in_db = {et.external_id for et in db_element_types}
        thing_node_ids_in_db = {tn.external_id for tn in db_thing_nodes}
        source_ids_in_db = {source.external_id for source in db_sources}
        sink_ids_in_db = {sink.external_id for sink in db_sinks}

        file_path = "tests/structure/data/" "db_test_unordered_structure.json"

        with open(file_path) as file:
            data = json.load(file)

        element_type_ids_in_json = {et["external_id"] for et in data["element_types"]}
        thing_node_ids_in_json = {tn["external_id"] for tn in data["thing_nodes"]}
        source_ids_in_json = {source["external_id"] for source in data["sources"]}
        sink_ids_in_json = {sink["external_id"] for sink in data["sinks"]}

        assert element_type_ids_in_db == element_type_ids_in_json, "Mismatch in element type IDs"
        assert thing_node_ids_in_db == thing_node_ids_in_json, "Mismatch in thing node IDs"
        assert source_ids_in_db == source_ids_in_json, "Mismatch in source IDs"
        assert sink_ids_in_db == sink_ids_in_json, "Mismatch in sink IDs"


@pytest.mark.usefixtures("_db_test_unordered_structure")
def test_update_structure_from_file_with_unordered_thingnodes_and_many_to_many_relationship(
    mocked_clean_test_db_session,
):
    with mocked_clean_test_db_session() as session:
        element_types = session.query(ElementTypeOrm).all()
        assert len(element_types) == 3

        element_type_names = [et.name for et in element_types]
        expected_element_type_names = ["Wasserwerk", "Anlage", "Hochbehälter"]

        for name in expected_element_type_names:
            assert name in element_type_names

        thing_nodes = session.query(ThingNodeOrm).all()
        assert len(thing_nodes) == 7

        thing_node_names = [tn.name for tn in thing_nodes]
        expected_thing_node_names = [
            "Wasserwerk 1",
            "Anlage 1",
            "Anlage 2",
            "Hochbehälter 1 Anlage 1",
            "Hochbehälter 2 Anlage 1",
            "Hochbehälter 1 Anlage 2",
            "Hochbehälter 2 Anlage 2",
        ]

        for name in expected_thing_node_names:
            assert name in thing_node_names

        sources = session.query(SourceOrm).all()
        assert len(sources) == 2

        source_names = [source.name for source in sources]
        expected_source_names = [
            "Energieverbräuche des Pumpensystems in Hochbehälter",
            "Energieverbrauch einer Einzelpumpe in Hochbehälter",
        ]

        for name in expected_source_names:
            assert name in source_names

        sinks = session.query(SinkOrm).all()
        assert len(sinks) == 2

        sink_names = [sink.name for sink in sinks]
        expected_sink_names = [
            "Anomaly Score für die Energieverbräuche des Pumpensystems in Hochbehälter",
            "Anomaly Score für den Energieverbrauch einer Einzelpumpe in Hochbehälter",
        ]

        for name in expected_sink_names:
            assert name in sink_names


@pytest.mark.usefixtures("_db_test_unordered_structure")
def test_sort_thing_nodes_from_json(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        db_thing_nodes = fetch_all_thing_nodes(session)

    sorted_nodes_by_level = sort_thing_nodes(db_thing_nodes)

    expected_order_names_by_level = {
        0: ["Wasserwerk 1"],
        1: ["Anlage 1", "Anlage 2"],
        2: [
            "Hochbehälter 1 Anlage 1",
            "Hochbehälter 2 Anlage 1",
            "Hochbehälter 1 Anlage 2",
            "Hochbehälter 2 Anlage 2",
        ],
    }

    # Check that the levels have the expected number of nodes
    for level, expected_names in expected_order_names_by_level.items():
        sorted_names = [node.name for node in sorted_nodes_by_level.get(level, [])]
        assert len(sorted_names) == len(
            expected_names
        ), f"Level {level} does not have the expected number of nodes. "
        f"Found: {len(sorted_names)}, Expected: {len(expected_names)}"

    # Check that the nodes at each level match the expected nodes
    for level, expected_names in expected_order_names_by_level.items():
        sorted_names = [node.name for node in sorted_nodes_by_level.get(level, [])]
        assert set(sorted_names) == set(
            expected_names
        ), f"Level {level} does not contain the expected nodes. "
        f"Found: {sorted_names}, Expected: {expected_names}"

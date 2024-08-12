import json
import time
import uuid
from sqlite3 import Connection as SQLite3Connection

import pytest
from sqlalchemy import event
from sqlalchemy.future.engine import Engine

from hetdesrun.persistence.db_engine_and_session import get_session
from hetdesrun.persistence.structure_service_dbmodels import (
    ElementTypeOrm,
    SinkOrm,
    SourceOrm,
    ThingNodeOrm,
)
from hetdesrun.structure.db.exceptions import DBIntegrityError, DBNotFoundError
from hetdesrun.structure.db.orm_service import (
    add_et,
    add_sink,
    add_source,
    add_tn,
    create_mapping_between_external_and_internal_ids,
    delete_et,
    delete_et_cascade,
    delete_sink,
    delete_source,
    delete_tn,
    fetch_all_element_types,
    fetch_all_sinks,
    fetch_all_sources,
    fetch_all_thing_nodes,
    fetch_et_by_external_id,
    fetch_et_by_id,
    fetch_sink_by_external_id,
    fetch_sink_by_id,
    fetch_source_by_external_id,
    fetch_source_by_id,
    fetch_tn_by_external_id,
    fetch_tn_by_id,
    fetch_tn_child_ids_by_parent_id,
    fill_all_element_type_ids,
    fill_all_parent_uuids,
    fill_element_type_ids_of_thing_nodes,
    fill_parent_uuids_of_thing_nodes,
    fill_source_sink_associations,
    flush_items,
    get_ancestors_tn_ids,
    get_children_tn_ids,
    get_descendants_tn_ids,
    get_parent_tn_id,
    insert_structure,
    insert_structure_from_file,
    load_structure_from_json_file,
    purge_structure,
    read_single_element_type,
    read_single_element_type_by_external_id,
    read_single_sink,
    read_single_sink_by_external_id,
    read_single_source,
    read_single_source_by_external_id,
    read_single_thingnode,
    read_single_thingnode_by_external_id,
    sort_thing_nodes,
    store_single_element_type,
    store_single_sink,
    store_single_source,
    store_single_thingnode,
    thingnode_sink_association,
    thingnode_source_association,
    update_et,
    update_sink,
    update_source,
    update_structure,
    update_structure_from_file,
    update_tn,
)
from hetdesrun.structure.models import (
    CompleteStructure,
    ElementType,
    FilterType,
    Sink,
    Source,
    ThingNode,
)

ElementType.update_forward_refs()
ThingNode.update_forward_refs()
Source.update_forward_refs()
Sink.update_forward_refs()
CompleteStructure.update_forward_refs()

# Fixture definitions


@pytest.fixture()
def db_test_structure_file_path():
    return "tests/structure/data/db_test_structure.json"


@pytest.fixture()
def _db_test_structure(mocked_clean_test_db_session):
    file_path = "tests/structure/data/db_test_structure.json"
    update_structure_from_file(file_path)


@pytest.fixture()
def _db_test_unordered_structure(mocked_clean_test_db_session):
    file_path = "tests/structure/data/db_test_unordered_structure.json"
    update_structure_from_file(file_path)


@pytest.fixture()
def _db_empty_database(mocked_clean_test_db_session):
    file_path = "tests/structure/data/db_empty_structure.json"
    update_structure_from_file(file_path)


# Enable Foreign Key Constraints for SQLite Connections


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection: SQLite3Connection, connection_record) -> None:  # type: ignore  # noqa: E501,
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# CRUD Operations for ThingNode


def test_invalid_thing_node_orm_creation(mocked_clean_test_db_session):
    session = mocked_clean_test_db_session()
    et_orm_object = ElementTypeOrm(
        id=uuid.uuid4(), name="TypeOrm1", external_id="external_test_id", stakeholder_key="shk_test"
    )
    add_et(session, et_orm_object)
    tn_orm_object = ThingNodeOrm(id=uuid.uuid4(), name=123, element_type_id=uuid.uuid4())

    with pytest.raises(DBIntegrityError):
        add_tn(session, tn_orm_object)


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
    id_of_non_existing_et = uuid.uuid4()
    tn_orm_object = ThingNodeOrm(
        id=uuid.uuid4(),
        external_id="thingnode_external_id",
        name="thing_node_name",
        element_type_id=id_of_non_existing_et,
        element_type_external_id="element_type_external_id",
        stakeholder_key="stakeholder_key_value",
    )
    with pytest.raises(DBIntegrityError):
        add_tn(session, tn_orm_object)


def test_storing_and_receiving_single_thingnode(mocked_clean_test_db_session):
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

    # Fetch the updated thingnode from the database
    with get_session()() as session, session.begin():
        updated_tn_db = fetch_tn_by_id(session, tn_object.id)
        assert updated_tn_db.name == "UpdatedNode1"


@pytest.mark.usefixtures("_db_test_structure")
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


def test_delete_tn_with_children(mocked_clean_test_db_session):
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


### CRUD Operations for Source


@pytest.mark.usefixtures("_db_test_structure")
def test_storing_and_receiving_single_source(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        thing_node_external_id = "Wasserwerk1_Anlage1_Hochbehaelter1"
        thing_node = (
            session.query(ThingNodeOrm)
            .filter(ThingNodeOrm.external_id == thing_node_external_id)
            .one_or_none()
        )
        assert thing_node is not None, "Expected ThingNode not found in the database"

        source_object = Source(
            id=uuid.uuid4(),
            external_id="Energieverbraeuche_Pumpensystem_Hochbehaelter_TestUnique",
            stakeholder_key="GW_TestUnique",
            name="Energieverbräuche des Pumpensystems in Hochbehälter - Test Unique",
            type="multitsframe",
            adapter_key="sql-adapter",
            source_id="improvt_timescale_db/ts_table/ts_values",
            meta_data={
                "1010001": {
                    "unit": "kW/h",
                    "description": "Energieverbrauchsdaten für eine Einzelpumpe",
                },
                "1010002": {
                    "unit": "kW/h",
                    "description": "Energieverbrauchsdaten für eine Einzelpumpe",
                },
            },
            preset_filters={"metrics": "1010001, 1010002"},
            thing_node_external_ids=[
                "Wasserwerk1_Anlage1_Hochbehaelter1",
                "Wasserwerk1_Anlage2_Hochbehaelter2",
            ],
        )

        store_single_source(source_object)

        retrieved_source = read_single_source(source_object.id)

        assert source_object == retrieved_source

        wrong_source_id = uuid.uuid4()
        with pytest.raises(DBNotFoundError):
            read_single_source(wrong_source_id)


@pytest.mark.usefixtures("_db_test_structure")
def test_update_source_valid_data(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        thing_node_external_id = "Wasserwerk1_Anlage1_Hochbehaelter1"
        thing_node = (
            session.query(ThingNodeOrm)
            .filter(ThingNodeOrm.external_id == thing_node_external_id)
            .one_or_none()
        )
        assert thing_node is not None, "Expected ThingNode not found in the database"

        source_object = Source(
            id=uuid.uuid4(),
            external_id="source1-ext-id",
            stakeholder_key="stakeholder1",
            name="Source1",
            type="multitsframe",
            adapter_key="sql-adapter",
            source_id="improvt_timescale_db/ts_table/ts_values",
            meta_data={"metric1": {"description": "Data for single pump", "unit": "kW/h"}},
            preset_filters={"metrics": "metric1"},
            passthrough_filters=[
                {"name": "timestampFrom", "type": FilterType.free_text, "required": True},
                {"name": "timestampTo", "type": FilterType.free_text, "required": False},
            ],
            thing_node_external_ids=[thing_node_external_id],
        )

        store_single_source(source_object)

        updated_data = Source(
            id=source_object.id,
            external_id="source1-updated-ext-id",
            stakeholder_key="stakeholder1",
            name="UpdatedSource1",
            type="multitsframe",
            adapter_key="sql-adapter",
            source_id="improvt_timescale_db/ts_table/ts_values",
            meta_data={"metric1": {"description": "Updated data for single pump", "unit": "kW/h"}},
            preset_filters={"metrics": "metric1"},
            passthrough_filters=[
                {"name": "timestampFrom", "type": FilterType.free_text, "required": True},
                {"name": "timestampTo", "type": FilterType.free_text, "required": False},
            ],
            thing_node_external_ids=[thing_node_external_id],
        )

        updated_source = update_source(source_object.id, updated_data)

        assert updated_source.name == "UpdatedSource1"

        updated_source_db = fetch_source_by_id(session, source_object.id)
        assert updated_source_db.name == "UpdatedSource1"

        wrong_source_id = uuid.uuid4()
        with pytest.raises(DBNotFoundError):
            fetch_source_by_id(session, wrong_source_id)


@pytest.mark.usefixtures("_db_test_structure")
def test_delete_source_valid_id(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        thing_node_external_id = "Wasserwerk1_Anlage1_Hochbehaelter1"
        thing_node = (
            session.query(ThingNodeOrm)
            .filter(ThingNodeOrm.external_id == thing_node_external_id)
            .one_or_none()
        )
        assert thing_node is not None, "Expected ThingNode not found in the database"

        source_object = Source(
            id=uuid.uuid4(),
            external_id="source1-ext-id",
            stakeholder_key="stakeholder1",
            name="Source1",
            type="multitsframe",
            adapter_key="sql-adapter",
            source_id="improvt_timescale_db/ts_table/ts_values",
            meta_data={
                "metric1": {
                    "unit": "kW/h",
                    "description": "Energy consumption data for single pump",
                }
            },
            preset_filters={"metrics": "metric1"},
            passthrough_filters=[
                {"name": "timestampFrom", "type": FilterType.free_text, "required": True},
                {"name": "timestampTo", "type": FilterType.free_text, "required": False},
            ],
            thing_node_external_ids=[thing_node_external_id],
        )

        store_single_source(source_object)

        source_id = source_object.id

        delete_source(source_id)

        with pytest.raises(DBNotFoundError):
            fetch_source_by_id(session, source_id)


def test_delete_source_invalid_id(mocked_clean_test_db_session):
    with pytest.raises(DBNotFoundError):
        delete_source(uuid.uuid4())


def test_add_source(mocked_clean_test_db_session):
    session = mocked_clean_test_db_session()
    source_orm_object = SourceOrm(
        id=uuid.uuid4(),
        name="SourceOrm1",
        external_id="source_external_id",
        stakeholder_key="stakeholder_key_value",
        type="type_value",
        visible=True,
        display_path="",
        adapter_key="adapter_key_value",
        source_id="source_id_value",
        ref_id="",
        preset_filters={},
        passthrough_filters=[],
        thing_node_external_ids=[],
    )
    add_source(session, source_orm_object)
    retrieved_source_orm = (
        session.query(SourceOrm).filter(SourceOrm.id == source_orm_object.id).one_or_none()
    )
    assert source_orm_object == retrieved_source_orm


def test_add_source_integrity_error(mocked_clean_test_db_session):
    session = mocked_clean_test_db_session()

    source_orm_object_1 = SourceOrm(
        id=uuid.uuid4(),
        name="SourceOrm1",
        external_id="source_external_id",
        stakeholder_key="stakeholder_key_value",
        type="type_value",
        visible=True,
        display_path="",
        adapter_key="adapter_key_value",
        source_id="source_id_value",
        ref_id="",
        preset_filters={},
        passthrough_filters=[],
        thing_node_external_ids=[],
    )
    add_source(session, source_orm_object_1)

    source_orm_object_2 = SourceOrm(
        id=uuid.uuid4(),
        name="SourceOrm2",
        external_id="source_external_id",
        stakeholder_key="stakeholder_key_value",
        type="type_value",
        visible=True,
        adapter_key="adapter_key_value",
        source_id="source_id_value_2",
        preset_filters={},
        passthrough_filters=[],
        thing_node_external_ids=[],
    )

    with pytest.raises(DBIntegrityError):
        add_source(session, source_orm_object_2)


### CRUD Operations for Sink


@pytest.mark.usefixtures("_db_test_structure")
def test_storing_and_receiving_single_sink(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        thing_node_external_id = "Wasserwerk1_Anlage1_Hochbehaelter1"
        thing_node = (
            session.query(ThingNodeOrm)
            .filter(ThingNodeOrm.external_id == thing_node_external_id)
            .one_or_none()
        )
        assert thing_node is not None, "Expected ThingNode not found in the database"

        sink_object = Sink(
            id=uuid.uuid4(),
            external_id="sink1-ext-id",
            stakeholder_key="stakeholder1",
            name="Sink1",
            type="multitsframe",
            adapter_key="sql-adapter",
            sink_id="improvt_timescale_db/ts_table/ts_values",
            meta_data={
                "metric1": {
                    "description": "Anomaly score for single pump",
                    "calculation_details": "Window size: 4h, Timestamp location: center",
                }
            },
            preset_filters={"metrics": "metric1"},
            passthrough_filters=[
                {"name": "timestampFrom", "type": FilterType.free_text, "required": True},
                {"name": "timestampTo", "type": FilterType.free_text, "required": False},
            ],
            thing_node_external_ids=[thing_node_external_id],
        )

        store_single_sink(sink_object)

        retrieved_sink = read_single_sink(sink_object.id)

        assert sink_object == retrieved_sink

        wrong_sink_id = uuid.uuid4()
        with pytest.raises(DBNotFoundError):
            read_single_sink(wrong_sink_id)


@pytest.mark.usefixtures("_db_test_structure")
def test_update_sink_valid_data(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        thing_node_external_id = "Wasserwerk1_Anlage1_Hochbehaelter1"
        thing_node = (
            session.query(ThingNodeOrm)
            .filter(ThingNodeOrm.external_id == thing_node_external_id)
            .one_or_none()
        )
        assert thing_node is not None, "Expected ThingNode not found in the database"

        sink_object = Sink(
            id=uuid.uuid4(),
            external_id="sink1-ext-id",
            stakeholder_key="stakeholder1",
            name="Sink1",
            type="multitsframe",
            adapter_key="sql-adapter",
            sink_id="improvt_timescale_db/ts_table/ts_values",
            meta_data={
                "metric1": {
                    "description": "Anomaly Score for single pump",
                    "calculation_details": "Window size: 4h, Timestamp location: center",
                }
            },
            preset_filters={"metrics": "metric1"},
            passthrough_filters=[
                {"name": "timestampFrom", "type": FilterType.free_text, "required": True},
                {"name": "timestampTo", "type": FilterType.free_text, "required": False},
            ],
            thing_node_external_ids=[thing_node_external_id],
        )

        store_single_sink(sink_object)

        updated_data = Sink(
            id=sink_object.id,
            external_id="sink1-updated-ext-id",
            stakeholder_key="stakeholder1",
            name="UpdatedSink1",
            type="multitsframe",
            adapter_key="sql-adapter",
            sink_id="improvt_timescale_db/ts_table/ts_values",
            meta_data={
                "metric1": {
                    "description": "Anomaly Score for single pump",
                    "calculation_details": "Window size: 4h, Timestamp location: center",
                }
            },
            preset_filters={"metrics": "metric1"},
            passthrough_filters=[
                {"name": "timestampFrom", "type": FilterType.free_text, "required": True},
                {"name": "timestampTo", "type": FilterType.free_text, "required": False},
            ],
            thing_node_external_ids=[thing_node_external_id],
        )

        updated_sink = update_sink(sink_object.id, updated_data)

        assert updated_sink.name == "UpdatedSink1"

        updated_sink_db = fetch_sink_by_id(session, sink_object.id)
        assert updated_sink_db.name == "UpdatedSink1"

        wrong_sink_id = uuid.uuid4()
        with pytest.raises(DBNotFoundError):
            fetch_sink_by_id(session, wrong_sink_id)


def test_delete_sink_invalid_id(mocked_clean_test_db_session):
    with pytest.raises(DBNotFoundError):
        delete_sink(uuid.uuid4())


def test_add_sink(mocked_clean_test_db_session):
    session = mocked_clean_test_db_session()
    sink_orm_object = SinkOrm(
        id=uuid.uuid4(),
        name="SinkOrm1",
        external_id="sink_external_id",
        stakeholder_key="stakeholder_key_value",
        type="type_value",
        visible=True,
        display_path="",
        adapter_key="adapter_key_value",
        sink_id="sink_id_value",
        ref_id="",
        preset_filters={},
        passthrough_filters=[],
        thing_node_external_ids=[],
    )
    add_sink(session, sink_orm_object)
    retrieved_sink_orm = (
        session.query(SinkOrm).filter(SinkOrm.id == sink_orm_object.id).one_or_none()
    )
    assert sink_orm_object == retrieved_sink_orm


def test_add_sink_integrity_error(mocked_clean_test_db_session):
    session = mocked_clean_test_db_session()

    sink_orm_object_1 = SinkOrm(
        id=uuid.uuid4(),
        name="SinkOrm1",
        external_id="sink_external_id",
        stakeholder_key="stakeholder_key_value",
        type="type_value",
        visible=True,
        display_path="",
        adapter_key="adapter_key_value",
        sink_id="sink_id_value",
        ref_id="",
        preset_filters={},
        passthrough_filters=[],
        thing_node_external_ids=[],
    )
    add_sink(session, sink_orm_object_1)

    sink_orm_object_2 = SinkOrm(
        id=uuid.uuid4(),
        name="SinkOrm2",
        external_id="sink_external_id",
        stakeholder_key="stakeholder_key_value",
        type="type_value",
        visible=True,
        adapter_key="adapter_key_value",
        sink_id="sink_id_value_2",
        preset_filters={},
        passthrough_filters=[],
        thing_node_external_ids=[],
    )

    with pytest.raises(DBIntegrityError):
        add_sink(session, sink_orm_object_2)


### Fetch ThingNode by ID


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


### Fetch ThingNode Children by Parent ID


@pytest.mark.usefixtures("_db_test_structure")
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


@pytest.mark.usefixtures("_db_test_structure")
def test_fetch_tn_child_ids_by_parent_id_dbnotfound(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        non_existent_uuid = uuid.uuid4()

        with pytest.raises(DBNotFoundError):
            fetch_tn_child_ids_by_parent_id(session, non_existent_uuid)


# Tests for Hierarchy and Relationships


@pytest.mark.usefixtures("_db_test_structure")
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


@pytest.mark.usefixtures("_db_test_structure")
def test_get_ancestors_tn_ids_valid_id(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        root_node = session.query(ThingNodeOrm).filter_by(external_id="Wasserwerk1").one_or_none()
        child_node1 = (
            session.query(ThingNodeOrm).filter_by(external_id="Wasserwerk1_Anlage1").one_or_none()
        )
        grandchild_node = (
            session.query(ThingNodeOrm)
            .filter_by(external_id="Wasserwerk1_Anlage1_Hochbehaelter1")
            .one_or_none()
        )

        ancestors_ids = get_ancestors_tn_ids(grandchild_node.id)

        assert ancestors_ids == [grandchild_node.id, child_node1.id, root_node.id]


@pytest.mark.usefixtures("_db_test_structure")
def test_get_ancestors_tn_ids_valid_depth_valid_id(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        child_node1 = (
            session.query(ThingNodeOrm).filter_by(external_id="Wasserwerk1_Anlage1").one_or_none()
        )
        grandchild_node = (
            session.query(ThingNodeOrm)
            .filter_by(external_id="Wasserwerk1_Anlage1_Hochbehaelter1")
            .one_or_none()
        )

        ancestors_ids = get_ancestors_tn_ids(grandchild_node.id, 2)

        assert ancestors_ids == [grandchild_node.id, child_node1.id]


def test_get_ancestors_tn_ids_invalid_id(mocked_clean_test_db_session):
    with pytest.raises(DBNotFoundError):
        get_ancestors_tn_ids(uuid.uuid4())


@pytest.mark.usefixtures("_db_test_structure")
def test_get_ancestors_tn_ids_invalid_depth_valid_id(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        root_node = session.query(ThingNodeOrm).filter_by(external_id="Wasserwerk1").one_or_none()
        child_node1 = (
            session.query(ThingNodeOrm).filter_by(external_id="Wasserwerk1_Anlage1").one_or_none()
        )
        grandchild_node = (
            session.query(ThingNodeOrm)
            .filter_by(external_id="Wasserwerk1_Anlage1_Hochbehaelter1")
            .one_or_none()
        )

        ancestors_ids = get_ancestors_tn_ids(grandchild_node.id, 2)

        with pytest.raises(AssertionError):
            assert ancestors_ids == [grandchild_node.id, child_node1.id, root_node.id]


# Exception Handling and Data Integrity Tests


@pytest.mark.usefixtures("_db_test_structure")
def test_uniqueness_thingnode(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        existing_tn = (
            session.query(ThingNodeOrm).filter_by(external_id="Wasserwerk1_Anlage1").one_or_none()
        )
        assert existing_tn is not None, "Expected ThingNode not found in the database"

        updated_data = ThingNode(
            id=existing_tn.id,
            external_id="new-ext-valid",
            name="UpdatedNodeName",
            stakeholder_key=existing_tn.stakeholder_key,
            element_type_id=existing_tn.element_type_id,
            element_type_external_id=existing_tn.element_type_external_id,
        )
        updated_tn = update_tn(existing_tn.id, updated_data)
        assert updated_tn.name == "UpdatedNodeName"

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
def test_insert_structure_from_file_with_unordered_thingnodes_and_many_to_many_relationship(
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


### Fetch Functions


@pytest.mark.usefixtures("_db_test_structure")
def test_fetch_all_element_types(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        element_types = fetch_all_element_types(session)
        assert len(element_types) == 3, "Expected 3 Element Types in the database"

        expected_element_types = [
            {"external_id": "Wasserwerk_Typ", "name": "Wasserwerk"},
            {"external_id": "Anlage_Typ", "name": "Anlage"},
            {"external_id": "Hochbehaelter_Typ", "name": "Hochbehälter"},
        ]

        for expected_et in expected_element_types:
            found = any(
                et.external_id == expected_et["external_id"] and et.name == expected_et["name"]
                for et in element_types
            )
            assert found, (
                f"Expected Element Type with external_id {expected_et['external_id']} "
                f"and name {expected_et['name']} not found"
            )


@pytest.mark.usefixtures("_db_test_structure")
def test_fetch_all_thing_nodes(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        thing_nodes = fetch_all_thing_nodes(session)
        assert len(thing_nodes) == 7, "Expected 7 Thing Nodes in the database"

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

        for expected_tn in expected_thing_nodes:
            found = any(
                tn.external_id == expected_tn["external_id"] and tn.name == expected_tn["name"]
                for tn in thing_nodes
            )
            assert found, (
                f"Expected Thing Node with external_id {expected_tn['external_id']} "
                f"and name {expected_tn['name']} not found"
            )


@pytest.mark.usefixtures("_db_test_structure")
def test_fetch_all_sources(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        sources = fetch_all_sources(session)
        assert len(sources) == 2, "Expected 2 Sources in the database"

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

        for expected_source in expected_sources:
            found = any(
                source.external_id == expected_source["external_id"]
                and source.name == expected_source["name"]
                for source in sources
            )
            assert found, (
                f"Expected Source with external_id {expected_source['external_id']} "
                f"and name {expected_source['name']} not found"
            )


@pytest.mark.usefixtures("_db_test_structure")
def test_fetch_all_sinks(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        sinks = fetch_all_sinks(session)
        assert len(sinks) == 2, "Expected 2 Sinks in the database"

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

        for expected_sink in expected_sinks:
            found = any(
                sink.external_id == expected_sink["external_id"]
                and sink.name == expected_sink["name"]
                for sink in sinks
            )
            assert found, (
                f"Expected Sink with external_id {expected_sink['external_id']} "
                f"and name {expected_sink['name']} not found"
            )


### Utility Functions


@pytest.mark.usefixtures("_db_test_structure")
def test_fetch_tn_by_external_id(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        thing_node_external_id = "Wasserwerk1_Anlage1"
        stakeholder_key = "GW"
        thing_node = fetch_tn_by_external_id(session, thing_node_external_id, stakeholder_key)
        assert thing_node is not None
        assert thing_node.external_id == thing_node_external_id
        assert thing_node.stakeholder_key == stakeholder_key

        wrong_external_id = "NonExistentExternalID"
        with pytest.raises(DBNotFoundError):
            fetch_tn_by_external_id(session, wrong_external_id, stakeholder_key)


@pytest.mark.usefixtures("_db_test_structure")
def test_read_single_thingnode_by_external_id(mocked_clean_test_db_session):
    thing_node_external_id = "Wasserwerk1_Anlage1"
    stakeholder_key = "GW"
    thing_node = read_single_thingnode_by_external_id(thing_node_external_id, stakeholder_key)
    assert thing_node is not None
    assert thing_node.external_id == thing_node_external_id
    assert thing_node.stakeholder_key == stakeholder_key

    wrong_external_id = "NonExistentExternalID"
    with pytest.raises(DBNotFoundError):
        read_single_thingnode_by_external_id(wrong_external_id, stakeholder_key)


@pytest.mark.usefixtures("_db_test_structure")
def test_get_parent_tn_id(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        child_node_external_id = "Wasserwerk1_Anlage1_Hochbehaelter1"
        child_node = (
            session.query(ThingNodeOrm)
            .filter(ThingNodeOrm.external_id == child_node_external_id)
            .one_or_none()
        )
        parent_id = get_parent_tn_id(session, child_node.id)
        assert parent_id is not None

        wrong_tn_id = uuid.uuid4()
        with pytest.raises(DBNotFoundError):
            get_parent_tn_id(session, wrong_tn_id)


@pytest.mark.usefixtures("_db_test_structure")
def test_get_descendants_tn_ids(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        root_node_external_id = "Wasserwerk1"
        root_node = (
            session.query(ThingNodeOrm)
            .filter(ThingNodeOrm.external_id == root_node_external_id)
            .one_or_none()
        )
        descendant_ids = get_descendants_tn_ids(root_node.id)
        assert len(descendant_ids) > 0

        wrong_tn_id = uuid.uuid4()
        descendants_wrong = get_descendants_tn_ids(wrong_tn_id)
        assert descendants_wrong == []


@pytest.mark.usefixtures("_db_test_structure")
def test_fetch_et_by_external_id(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        external_id = "Wasserwerk_Typ"
        stakeholder_key = "GW"
        element_type = fetch_et_by_external_id(session, external_id, stakeholder_key)
        assert element_type is not None
        assert element_type.external_id == external_id
        assert element_type.stakeholder_key == stakeholder_key

        wrong_external_id = "NonExistentExternalID"
        with pytest.raises(DBNotFoundError):
            fetch_et_by_external_id(session, wrong_external_id, stakeholder_key)


@pytest.mark.usefixtures("_db_test_structure")
def test_read_single_element_type_by_external_id(mocked_clean_test_db_session):
    external_id = "Wasserwerk_Typ"
    stakeholder_key = "GW"
    element_type = read_single_element_type_by_external_id(external_id, stakeholder_key)
    assert element_type is not None
    assert element_type.external_id == external_id
    assert element_type.stakeholder_key == stakeholder_key

    wrong_external_id = "NonExistentExternalID"
    with pytest.raises(DBNotFoundError):
        read_single_element_type_by_external_id(wrong_external_id, stakeholder_key)


@pytest.mark.usefixtures("_db_test_structure")
def test_fetch_source_by_external_id(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        external_id = "Energieverbraeuche_Pumpensystem_Hochbehaelter"
        stakeholder_key = "GW"
        source = fetch_source_by_external_id(session, external_id, stakeholder_key)
        assert source is not None
        assert source.external_id == external_id
        assert source.stakeholder_key == stakeholder_key

        wrong_external_id = "NonExistentExternalID"
        with pytest.raises(DBNotFoundError):
            fetch_source_by_external_id(session, wrong_external_id, stakeholder_key)


@pytest.mark.usefixtures("_db_test_structure")
def test_fetch_sink_by_external_id(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        external_id = "Anomaly_Score_Energieverbraeuche_Pumpensystem_Hochbehaelter"
        stakeholder_key = "GW"
        sink = fetch_sink_by_external_id(session, external_id, stakeholder_key)
        assert sink is not None
        assert sink.external_id == external_id
        assert sink.stakeholder_key == stakeholder_key

        wrong_external_id = "NonExistentExternalID"
        with pytest.raises(DBNotFoundError):
            fetch_sink_by_external_id(session, wrong_external_id, stakeholder_key)


@pytest.mark.usefixtures("_db_test_structure")
def test_read_single_source_by_external_id(mocked_clean_test_db_session):
    external_id = "Energieverbraeuche_Pumpensystem_Hochbehaelter"
    stakeholder_key = "GW"
    source = read_single_source_by_external_id(external_id, stakeholder_key)
    assert source is not None
    assert source.external_id == external_id
    assert source.stakeholder_key == stakeholder_key

    wrong_external_id = "NonExistentExternalID"
    with pytest.raises(DBNotFoundError):
        read_single_source_by_external_id(wrong_external_id, stakeholder_key)


@pytest.mark.usefixtures("_db_test_structure")
def test_read_single_sink_by_external_id(mocked_clean_test_db_session):
    external_id = "Anomaly_Score_Energieverbraeuche_Pumpensystem_Hochbehaelter"
    stakeholder_key = "GW"
    sink = read_single_sink_by_external_id(external_id, stakeholder_key)
    assert sink is not None
    assert sink.external_id == external_id
    assert sink.stakeholder_key == stakeholder_key

    wrong_external_id = "NonExistentExternalID"
    with pytest.raises(DBNotFoundError):
        read_single_sink_by_external_id(wrong_external_id, stakeholder_key)


### Structure Helper Functions


ElementType.update_forward_refs()
ThingNode.update_forward_refs()
Source.update_forward_refs()
Sink.update_forward_refs()
CompleteStructure.update_forward_refs()


@pytest.mark.usefixtures("_db_test_structure")
def test_create_mapping_between_external_and_internal_ids(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        thing_nodes = session.query(ThingNodeOrm).all()
        assert thing_nodes is not None

        element_types = session.query(ElementTypeOrm).all()
        assert element_types is not None

        sources = session.query(SourceOrm).all()
        assert sources is not None

        sinks = session.query(SinkOrm).all()
        assert sinks is not None

        thing_node_list = [ThingNode.from_orm(tn) for tn in thing_nodes]
        source_list = [Source.from_orm(src) for src in sources]
        sink_list = [Sink.from_orm(snk) for snk in sinks]

        tn_mapping, src_mapping, snk_mapping = create_mapping_between_external_and_internal_ids(
            thing_node_list, source_list, sink_list
        )

        for thing_node in thing_nodes:
            assert thing_node.stakeholder_key + thing_node.external_id in tn_mapping
            assert tn_mapping[thing_node.stakeholder_key + thing_node.external_id] == thing_node.id

        for source in sources:
            assert source.stakeholder_key + source.external_id in src_mapping
            assert src_mapping[source.stakeholder_key + source.external_id] == source.id

        for sink in sinks:
            assert sink.stakeholder_key + sink.external_id in snk_mapping
            assert snk_mapping[sink.stakeholder_key + sink.external_id] == sink.id


@pytest.mark.usefixtures("_db_test_structure")
def test_fill_parent_uuids_of_thing_nodes(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        thing_nodes = session.query(ThingNodeOrm).all()
        assert thing_nodes is not None

        thing_node_list = [ThingNode.from_orm_model(tn) for tn in thing_nodes]

        tn_mapping = {tn.stakeholder_key + tn.external_id: tn.id for tn in thing_node_list}

        original_parent_node_ids = {node.id: node.parent_node_id for node in thing_node_list}

        fill_parent_uuids_of_thing_nodes(tn_mapping, thing_node_list)

        for node in thing_node_list:
            if node.parent_external_node_id:
                parent_uuid = tn_mapping[node.stakeholder_key + node.parent_external_node_id]
                assert node.parent_node_id == parent_uuid
            else:
                assert node.parent_node_id == original_parent_node_ids[node.id]

        for node in thing_node_list:
            if node.parent_external_node_id:
                assert (
                    node.parent_node_id is not None
                ), f"Parent node ID for {node.external_id} is None"


@pytest.mark.usefixtures("_db_test_structure")
def test_fill_parent_uuids_of_thing_nodes_invalid_parent(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        thing_nodes = session.query(ThingNodeOrm).all()
        assert thing_nodes is not None

        thing_node_list = [ThingNode.from_orm_model(tn) for tn in thing_nodes]

        tn_mapping = {tn.stakeholder_key + tn.external_id: tn.id for tn in thing_node_list}

        invalid_external_id = "invalid_parent_id"
        thing_node_list[0].parent_external_node_id = invalid_external_id

        with pytest.raises(KeyError):
            fill_parent_uuids_of_thing_nodes(tn_mapping, thing_node_list)


@pytest.mark.usefixtures("_db_test_structure")
def test_fill_element_type_ids_of_thing_nodes(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        thing_nodes = session.query(ThingNodeOrm).all()
        element_types = session.query(ElementTypeOrm).all()
        assert thing_nodes is not None
        assert element_types is not None

        thing_node_list = [ThingNode.from_orm_model(tn) for tn in thing_nodes]

        element_type_mapping = {et.stakeholder_key + et.external_id: et.id for et in element_types}

        original_element_type_ids = {node.id: node.element_type_id for node in thing_node_list}

        fill_element_type_ids_of_thing_nodes(element_type_mapping, thing_node_list)

        for node in thing_node_list:
            if node.element_type_external_id:
                element_type_uuid = element_type_mapping[
                    node.stakeholder_key + node.element_type_external_id
                ]
                assert node.element_type_id == element_type_uuid
            else:
                assert node.element_type_id == original_element_type_ids[node.id]

        for node in thing_node_list:
            if node.element_type_external_id:
                assert (
                    node.element_type_id is not None
                ), f"Element type ID for {node.external_id} is None"


@pytest.mark.usefixtures("_db_test_structure")
def test_fill_element_type_ids_of_thing_nodes_invalid_element_type(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        thing_nodes = session.query(ThingNodeOrm).all()
        element_types = session.query(ElementTypeOrm).all()
        assert thing_nodes is not None
        assert element_types is not None

        thing_node_list = [ThingNode.from_orm_model(tn) for tn in thing_nodes]

        element_type_mapping = {et.stakeholder_key + et.external_id: et.id for et in element_types}

        invalid_external_id = "invalid_element_type_id"
        thing_node_list[0].element_type_external_id = invalid_external_id

        with pytest.raises(KeyError):
            fill_element_type_ids_of_thing_nodes(element_type_mapping, thing_node_list)


@pytest.mark.usefixtures("_db_test_structure")
def test_fill_all_parent_uuids_invalid_parent(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        thing_nodes_orm = fetch_all_thing_nodes(session)
        assert thing_nodes_orm is not None

        thing_nodes = [ThingNode.from_orm_model(tn) for tn in thing_nodes_orm]

        element_types = fetch_all_element_types(session)
        sources = fetch_all_sources(session)
        sinks = fetch_all_sinks(session)

        complete_structure = CompleteStructure(
            element_types=element_types, thing_nodes=thing_nodes, sources=sources, sinks=sinks
        )

        thing_nodes[0].parent_external_node_id = "invalid_parent_id"

        with pytest.raises(KeyError, match="invalid_parent_id"):
            fill_all_parent_uuids(complete_structure)


@pytest.mark.usefixtures("_db_test_structure")
def test_fill_all_element_type_ids(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        complete_structure = CompleteStructure(
            element_types=fetch_all_element_types(session),
            thing_nodes=fetch_all_thing_nodes(session),
            sources=fetch_all_sources(session),
            sinks=fetch_all_sinks(session),
        )

        for node in complete_structure.thing_nodes:
            assert node.element_type_id is not None, "ThingNode should have a dummy element_type_id"

        fill_all_element_type_ids(complete_structure)

        element_type_mapping = {
            et.stakeholder_key + et.external_id: et.id for et in complete_structure.element_types
        }

        for node in complete_structure.thing_nodes:
            expected_element_type_id = element_type_mapping[
                node.stakeholder_key + node.element_type_external_id
            ]
            assert (
                node.element_type_id == expected_element_type_id
            ), f"ThingNode with external_id {node.external_id} has an incorrect element_type_id."


@pytest.mark.usefixtures("_db_test_structure")
def test_fill_source_sink_associations(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        # Load the complete structure from the test fixture
        complete_structure = CompleteStructure(
            element_types=fetch_all_element_types(session),
            thing_nodes=fetch_all_thing_nodes(session),
            sources=fetch_all_sources(session),
            sinks=fetch_all_sinks(session),
        )

        # Ensure the initial state of associations is empty
        session.execute(thingnode_source_association.delete())
        session.execute(thingnode_sink_association.delete())
        session.commit()
        initial_source_associations = session.query(thingnode_source_association).all()
        initial_sink_associations = session.query(thingnode_sink_association).all()
        assert len(initial_source_associations) == 0, "Source associations table should be empty"
        assert len(initial_sink_associations) == 0, "Sink associations table should be empty"

        # Call the function to fill source-sink associations
        fill_source_sink_associations(complete_structure, session)
        session.commit()

        # Fetch the updated associations
        updated_source_associations = session.query(thingnode_source_association).all()
        updated_sink_associations = session.query(thingnode_sink_association).all()

        # Verify that the associations are correctly set
        for source in complete_structure.sources:
            if source.thing_node_external_ids:
                for tn_external_id in source.thing_node_external_ids:
                    thing_node_id = (
                        session.query(ThingNodeOrm).filter_by(external_id=tn_external_id).one().id
                    )
                    source_id = (
                        session.query(SourceOrm).filter_by(external_id=source.external_id).one().id
                    )
                    association = (thing_node_id, source_id)
                    assert association in updated_source_associations, (
                        f"Association for source {source.external_id} "
                        f"and thing node {tn_external_id} is missing"
                    )

        for sink in complete_structure.sinks:
            if sink.thing_node_external_ids:
                for tn_external_id in sink.thing_node_external_ids:
                    thing_node_id = (
                        session.query(ThingNodeOrm).filter_by(external_id=tn_external_id).one().id
                    )
                    sink_id = (
                        session.query(SinkOrm).filter_by(external_id=sink.external_id).one().id
                    )
                    association = (thing_node_id, sink_id)
                    assert association in updated_sink_associations, (
                        f"Association for sink {sink.external_id} "
                        f"and thing node {tn_external_id} is missing"
                    )


def test_load_structure_from_json_file(db_test_structure_file_path):
    complete_structure = load_structure_from_json_file(db_test_structure_file_path)

    # Check if the complete_structure is an instance of CompleteStructure
    assert isinstance(
        complete_structure, CompleteStructure
    ), "Loaded structure is not an instance of CompleteStructure"

    # Load the expected structure directly from the JSON file for comparison
    with open(db_test_structure_file_path) as file:
        expected_structure_json = json.load(file)

    expected_structure = CompleteStructure(**expected_structure_json)

    # Set all UUID fields to the same value pairwise
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

    for complete, expected in zip(
        complete_structure.thing_nodes, expected_structure.thing_nodes, strict=False
    ):
        uniform_id = uuid.uuid4()
        complete.element_type_id = uniform_id
        expected.element_type_id = uniform_id

    assert (
        complete_structure == expected_structure
    ), "Loaded structure does not match the expected structure"


@pytest.mark.usefixtures("_db_test_structure")
def test_purge_structure(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        # Verify that the database is initially populated
        assert session.query(ElementTypeOrm).count() > 0
        assert session.query(ThingNodeOrm).count() > 0
        assert session.query(SourceOrm).count() > 0
        assert session.query(SinkOrm).count() > 0
        assert session.query(thingnode_source_association).count() > 0
        assert session.query(thingnode_sink_association).count() > 0

        purge_structure(session)

        # Verify that all tables are empty after purging
        assert session.query(ElementTypeOrm).count() == 0
        assert session.query(ThingNodeOrm).count() == 0
        assert session.query(SourceOrm).count() == 0
        assert session.query(SinkOrm).count() == 0
        assert session.query(thingnode_source_association).count() == 0
        assert session.query(thingnode_sink_association).count() == 0


@pytest.mark.usefixtures("_db_test_structure")
def test_update_structure_with_new_elements():
    with get_session()() as session, session.begin():
        # Verify initial structure
        verify_initial_structure(session)

        # Load updated structure from JSON file
        file_path = "tests/structure/data/db_updated_test_structure.json"
        updated_structure = load_structure_from_json_file(file_path)

    # Update the structure in the database
    update_structure(updated_structure)

    # Verify structure after update
    with get_session()() as session, session.begin():
        verify_updated_structure(session)


def verify_initial_structure(session):
    initial_element_types = session.query(ElementTypeOrm).all()
    initial_thing_nodes = session.query(ThingNodeOrm).all()
    initial_sources = session.query(SourceOrm).all()
    initial_sinks = session.query(SinkOrm).all()

    assert len(initial_element_types) == 3
    assert len(initial_thing_nodes) == 7
    assert len(initial_sources) == 2
    assert len(initial_sinks) == 2

    # Initial values before the update
    initial_tn = (
        session.query(ThingNodeOrm)
        .filter_by(external_id="Wasserwerk1_Anlage1_Hochbehaelter1")
        .one()
    )
    assert initial_tn.meta_data["capacity"] == "5000"
    assert initial_tn.meta_data["description"] == ("Wasserspeicherungskapazität für Hochbehälter 1")

    initial_tn2 = (
        session.query(ThingNodeOrm)
        .filter_by(external_id="Wasserwerk1_Anlage1_Hochbehaelter2")
        .one()
    )
    assert initial_tn2.meta_data["capacity"] == "6000"
    assert initial_tn2.meta_data["description"] == (
        "Wasserspeicherungskapazität für Hochbehälter 2"
    )


def verify_updated_structure(session):
    final_element_types = session.query(ElementTypeOrm).all()
    final_thing_nodes = session.query(ThingNodeOrm).all()
    final_sources = session.query(SourceOrm).all()
    final_sinks = session.query(SinkOrm).all()

    assert len(final_element_types) == 4
    assert len(final_thing_nodes) == 8
    assert len(final_sources) == 3
    assert len(final_sinks) == 2

    verify_new_elements_and_nodes(session, final_element_types, final_thing_nodes)
    verify_associations(session)


def verify_new_elements_and_nodes(session, final_element_types, final_thing_nodes):
    # Verify new element type added
    new_element_type = next(
        et for et in final_element_types if et.external_id == "Filteranlage_Typ"
    )
    assert new_element_type.name == "Filteranlage"
    assert new_element_type.description == "Elementtyp für Filteranlagen"

    # Verify new thing node added
    new_tn = next(tn for tn in final_thing_nodes if tn.external_id == "Wasserwerk1_Filteranlage")
    assert new_tn.name == "Filteranlage 1"
    assert new_tn.description == "Neue Filteranlage im Wasserwerk 1"
    assert new_tn.meta_data["location"] == "Zentral"
    assert new_tn.meta_data["technology"] == "Advanced Filtration"

    # Check that the thing nodes were updated correctly
    updated_tn1 = next(
        tn for tn in final_thing_nodes if tn.external_id == "Wasserwerk1_Anlage1_Hochbehaelter1"
    )
    assert updated_tn1.meta_data["capacity"] == "5200"
    assert updated_tn1.meta_data["description"] == (
        "Erhöhte Wasserspeicherungskapazität für Hochbehälter 1"
    )

    updated_tn2 = next(
        tn for tn in final_thing_nodes if tn.external_id == "Wasserwerk1_Anlage1_Hochbehaelter2"
    )
    assert updated_tn2.meta_data["capacity"] == "6100"
    assert updated_tn2.meta_data["description"] == (
        "Erhöhte Wasserspeicherungskapazität für Hochbehälter 2"
    )


def verify_associations(session):
    source_associations = session.query(thingnode_source_association).all()
    sink_associations = session.query(thingnode_sink_association).all()

    expected_source_associations = [
        ("Wasserwerk1_Anlage1_Hochbehaelter1", "Energieverbraeuche_Pumpensystem_Hochbehaelter"),
        ("Wasserwerk1_Filteranlage", "Energieverbraeuche_Pumpensystem_Hochbehaelter"),
        ("Wasserwerk1_Anlage2_Hochbehaelter1", "Energieverbrauch_Einzelpumpe_Hochbehaelter"),
        ("Wasserwerk1_Filteranlage", "Neue_Energiequelle_Filteranlage"),
    ]

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
        ]

    for tn_external_id, sink_external_id in expected_sink_associations:
        tn_id = (
            session.query(ThingNodeOrm.id)
            .filter(ThingNodeOrm.external_id == tn_external_id)
            .one()[0]
        )
        sink_id = session.query(SinkOrm.id).filter(SinkOrm.external_id == sink_external_id).one()[0]
        assert (tn_id, sink_id) in [
            (assoc.thing_node_id, assoc.sink_id) for assoc in sink_associations
        ]


@pytest.mark.usefixtures("_db_empty_database")
def test_insert_structure_from_file():
    # Path to the JSON file containing the test structure
    file_path = "tests/structure/data/db_test_structure.json"

    # Ensure the database is empty at the beginning
    with get_session()() as session:
        assert session.query(ElementTypeOrm).count() == 0
        assert session.query(ThingNodeOrm).count() == 0
        assert session.query(SourceOrm).count() == 0
        assert session.query(SinkOrm).count() == 0

    # Load structure from the file and insert it into the database
    insert_structure_from_file(file_path)

    # Verify that the structure was correctly inserted
    with get_session()() as session:
        assert session.query(ElementTypeOrm).count() == 3
        assert session.query(ThingNodeOrm).count() == 7
        assert session.query(SourceOrm).count() == 2
        assert session.query(SinkOrm).count() == 2

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


@pytest.mark.usefixtures("_db_empty_database")
def test_insert_structure_with_insert_structure():
    # Ensure the database is empty at the beginning
    with get_session()() as session:
        assert session.query(ElementTypeOrm).count() == 0
        assert session.query(ThingNodeOrm).count() == 0
        assert session.query(SourceOrm).count() == 0
        assert session.query(SinkOrm).count() == 0

    # Load structure from JSON file
    file_path = "tests/structure/data/db_test_structure.json"
    new_structure = load_structure_from_json_file(file_path)

    # Insert the new structure into the database using insert_structure
    insert_structure(new_structure)

    # Verify the structure was correctly inserted
    with get_session()() as session:
        assert session.query(ElementTypeOrm).count() == 3
        assert session.query(ThingNodeOrm).count() == 7
        assert session.query(SourceOrm).count() == 2
        assert session.query(SinkOrm).count() == 2

        # Example check for a specific inserted element type
        wasserwerk_typ = session.query(ElementTypeOrm).filter_by(external_id="Wasserwerk_Typ").one()
        assert wasserwerk_typ.name == "Wasserwerk"
        assert wasserwerk_typ.description == "Elementtyp für Wasserwerke"

        # Example check for a specific inserted thing node
        wasserwerk1 = session.query(ThingNodeOrm).filter_by(external_id="Wasserwerk1").one()
        assert wasserwerk1.name == "Wasserwerk 1"
        assert wasserwerk1.meta_data["location"] == "Hauptstandort"

        # Example check for a specific source
        source = (
            session.query(SourceOrm)
            .filter_by(external_id="Energieverbraeuche_Pumpensystem_Hochbehaelter")
            .one()
        )
        assert source.name == "Energieverbräuche des Pumpensystems in Hochbehälter"
        assert source.meta_data["1010001"]["unit"] == "kW/h"


@pytest.mark.usefixtures("_db_empty_database")
def test_update_structure_from_file():
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
        assert session.query(SourceOrm).count() == 2
        assert session.query(SinkOrm).count() == 2

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


@pytest.mark.usefixtures("_db_empty_database")
def test_insert_structure_with_update_structure():
    # Ensure the database is empty at the beginning
    with get_session()() as session:
        assert session.query(ElementTypeOrm).count() == 0
        assert session.query(ThingNodeOrm).count() == 0
        assert session.query(SourceOrm).count() == 0
        assert session.query(SinkOrm).count() == 0

    # Load structure from JSON file
    file_path = "tests/structure/data/db_test_structure.json"
    new_structure = load_structure_from_json_file(file_path)

    # Call update_structure to insert the new structure into the database
    update_structure(new_structure)

    # Verify the structure was correctly inserted
    with get_session()() as session:
        assert session.query(ElementTypeOrm).count() == 3
        assert session.query(ThingNodeOrm).count() == 7
        assert session.query(SourceOrm).count() == 2
        assert session.query(SinkOrm).count() == 2

        # Example check for a specific inserted element type
        wasserwerk_typ = session.query(ElementTypeOrm).filter_by(external_id="Wasserwerk_Typ").one()
        assert wasserwerk_typ.name == "Wasserwerk"
        assert wasserwerk_typ.description == "Elementtyp für Wasserwerke"

        # Example check for a specific inserted thing node
        wasserwerk1 = session.query(ThingNodeOrm).filter_by(external_id="Wasserwerk1").one()
        assert wasserwerk1.name == "Wasserwerk 1"
        assert wasserwerk1.meta_data["location"] == "Hauptstandort"

        # Example check for a specific source
        source = (
            session.query(SourceOrm)
            .filter_by(external_id="Energieverbraeuche_Pumpensystem_Hochbehaelter")
            .one()
        )
        assert source.name == "Energieverbräuche des Pumpensystems in Hochbehälter"
        assert source.meta_data["1010001"]["unit"] == "kW/h"


def test_flush_items(mocked_clean_test_db_session):
    file_path = "tests/structure/data/db_test_structure.json"
    complete_structure = insert_structure_from_file(file_path)
    with mocked_clean_test_db_session() as session:
        # Bereinige alle bestehenden Daten

        print(complete_structure)

        purge_structure(session)

        # # Flush items into the database
        flush_items(session, complete_structure.element_types)
        flush_items(session, complete_structure.thing_nodes)
        flush_items(session, complete_structure.sources)
        flush_items(session, complete_structure.sinks)

        # Verify if items are flushed correctly
        flushed_element_types = session.query(ElementTypeOrm).all()
        flushed_thing_nodes = session.query(ThingNodeOrm).all()
        flushed_sources = session.query(SourceOrm).all()
        flushed_sinks = session.query(SinkOrm).all()

        assert len(flushed_element_types) == len(complete_structure.element_types)
        assert len(flushed_thing_nodes) == len(complete_structure.thing_nodes)
        assert len(flushed_sources) == len(complete_structure.sources)
        assert len(flushed_sinks) == len(complete_structure.sinks)

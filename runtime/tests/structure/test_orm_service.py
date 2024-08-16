import json
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
from hetdesrun.structure.db.orm_service import (
    fetch_all_element_types,
    fetch_all_sinks,
    fetch_all_sources,
    fetch_all_thing_nodes,
    load_structure_from_json_file,
    orm_delete_structure,
    orm_is_database_empty,
    orm_update_structure,
    thingnode_sink_association,
    thingnode_source_association,
    update_structure_from_file,
)
from hetdesrun.structure.models import (
    CompleteStructure,
    ElementType,
    Sink,
    Source,
    ThingNode,
)

ElementType.update_forward_refs()
ThingNode.update_forward_refs()
Source.update_forward_refs()
Sink.update_forward_refs()
CompleteStructure.update_forward_refs()

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

        # Ensure the counts match the expected values
        expected_element_types_count = 3
        expected_thing_nodes_count = 7
        expected_sources_count = 3
        expected_sinks_count = 3

        assert (
            len(element_types_in_db) == expected_element_types_count
        ), "Mismatch in element types count"
        assert len(thing_nodes_in_db) == expected_thing_nodes_count, "Mismatch in thing nodes count"
        assert len(sources_in_db) == expected_sources_count, "Mismatch in sources count"
        assert len(sinks_in_db) == expected_sinks_count, "Mismatch in sinks count"


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
        assert len(sources) == 3, "Expected 3 Sources in the database"

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
        assert len(sinks) == 3, "Expected 3 Sinks in the database"

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
    initial_element_types = session.query(ElementTypeOrm).all()
    initial_thing_nodes = session.query(ThingNodeOrm).all()
    initial_sources = session.query(SourceOrm).all()
    initial_sinks = session.query(SinkOrm).all()

    assert len(initial_element_types) == 3
    assert len(initial_thing_nodes) == 7
    assert len(initial_sources) == 3
    assert len(initial_sinks) == 3

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
    assert len(final_sources) == 4
    assert len(final_sinks) == 3

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


@pytest.mark.usefixtures("_db_empty_database")
def test_is_database_empty_when_empty(mocked_clean_test_db_session):
    assert orm_is_database_empty(), "Database should be empty but is not."


@pytest.mark.usefixtures("_db_test_structure")
def test_is_database_empty_when_not_empty(mocked_clean_test_db_session):
    assert not orm_is_database_empty(), "Database should not be empty but it is."

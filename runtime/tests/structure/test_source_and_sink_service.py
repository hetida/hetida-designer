import uuid

import pytest

from hetdesrun.persistence.structure_service_dbmodels import (
    StructureServiceSinkDBModel,
    StructureServiceSourceDBModel,
)
from hetdesrun.structure.db.exceptions import DBNotFoundError
from hetdesrun.structure.db.source_sink_service import (
    fetch_all_sinks_from_db,
    fetch_all_sources_from_db,
    fetch_collection_of_sinks_from_db_by_id,
    fetch_collection_of_sources_from_db_by_id,
    fetch_single_sink_from_db_by_id,
    fetch_single_source_from_db_by_id,
    fetch_sinks_by_substring_match,
    fetch_sources_by_substring_match,
)


@pytest.mark.usefixtures("_db_test_structure")
def test_fetch_single_source_from_db_by_id(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        # Fetch an existing StructureServiceSource ID from the database
        existing_source = session.query(StructureServiceSourceDBModel).first()
        assert (
            existing_source is not None
        ), "Expected at least one StructureServiceSource in the test database."
        existing_source_id = existing_source.id

        # Test retrieving the StructureServiceSource by its ID
        fetched_source = fetch_single_source_from_db_by_id(existing_source_id)
        assert (
            fetched_source.id == existing_source_id
        ), f"Expected StructureServiceSource ID {existing_source_id}."

        # Test that a non-existent StructureServiceSource raises a DBNotFoundError
        non_existent_id = uuid.uuid4()
        with pytest.raises(DBNotFoundError):
            fetch_single_source_from_db_by_id(non_existent_id)


@pytest.mark.usefixtures("_db_test_structure")
def test_fetch_all_sources_from_db(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        # Fetch all sources directly from the database using the ORM for comparison
        expected_sources = session.query(StructureServiceSourceDBModel).all()

    # Use the get_all_sources_from_db function to fetch all sources
    fetched_sources = fetch_all_sources_from_db()

    # Verify that the number of sources fetched matches the expected number
    assert len(fetched_sources) == len(expected_sources), (
        f"Expected {len(expected_sources)} sources, " f"but fetched {len(fetched_sources)} sources."
    )

    # Verify that all sources fetched match the expected sources
    for expected_source in expected_sources:
        matched_source = next(
            (source for source in fetched_sources if source.id == expected_source.id),
            None,
        )
        assert (
            matched_source is not None
        ), f"StructureServiceSource with ID {expected_source.id} was expected but not found."


@pytest.mark.usefixtures("_db_test_structure")
def test_fetch_collection_of_sources_from_db_by_id(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        # Fetch some specific sources directly from the database
        expected_sources = session.query(StructureServiceSourceDBModel).limit(2).all()
        expected_source_ids = [source.id for source in expected_sources]

    # Use the get_collection_of_sources_from_db function to fetch the sources
    fetched_sources = fetch_collection_of_sources_from_db_by_id(expected_source_ids)

    # Verify that the number of sources fetched matches the expected number
    assert len(fetched_sources) == len(expected_source_ids), (
        f"Expected {len(expected_source_ids)} sources, "
        f"but fetched {len(fetched_sources)} sources."
    )

    # Verify that each expected source is in the fetched sources dictionary
    for expected_source in expected_sources:
        assert expected_source.id in fetched_sources, (
            f"StructureServiceSource with ID {expected_source.id} "
            "was expected but not found in the fetched sources."
        )

        # Verify that the fetched source matches the expected source
        fetched_source = fetched_sources[expected_source.id]
        assert (
            fetched_source.external_id == expected_source.external_id
        ), f"StructureServiceSource with ID {expected_source.id} has mismatched external_id."
        assert (
            fetched_source.name == expected_source.name
        ), f"StructureServiceSource with ID {expected_source.id} has mismatched name."


@pytest.mark.usefixtures("_db_test_structure")
def test_fetch_single_sink_from_db_by_id(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        # Fetch a specific sink directly from the database
        expected_sink = session.query(StructureServiceSinkDBModel).first()
        assert expected_sink is not None, "No sinks found in the test database."

    # Use the get_single_sink_from_db function to fetch the sink
    fetched_sink = fetch_single_sink_from_db_by_id(expected_sink.id)

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
    with pytest.raises(
        DBNotFoundError, match=f"No StructureServiceSink found for ID {non_existent_sink_id}"
    ):
        fetch_single_sink_from_db_by_id(non_existent_sink_id)


@pytest.mark.usefixtures("_db_test_structure")
def test_fetch_all_sinks_from_db(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        # Fetch all sinks directly from the database
        expected_sinks = session.query(StructureServiceSinkDBModel).all()
        assert len(expected_sinks) > 0, "No sinks found in the test database."

    # Use the get_all_sinks_from_db function to fetch all sinks
    fetched_sinks = fetch_all_sinks_from_db()

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
def test_fetch_collection_of_sinks_from_db_by_id(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        # Fetch some sinks directly from the database
        sinks_in_db = session.query(StructureServiceSinkDBModel).limit(2).all()
        sink_ids = [sink.id for sink in sinks_in_db]
        assert len(sink_ids) > 0, "No sinks found in the test database."

    # Use the get_collection_of_sinks_from_db function to fetch sinks by their IDs
    fetched_sinks = fetch_collection_of_sinks_from_db_by_id(sink_ids)

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


@pytest.mark.usefixtures("_db_test_structure")
def test_filter_sinks_by_substring_match_success(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        # Fetch an example sink name from the database to use in the test
        example_sink = session.query(StructureServiceSinkDBModel).first()
        assert example_sink is not None, "No sinks found in the database."

        # Use a substring of the example sink's name to perform the search
        substring_to_match = example_sink.name[:30]  # Take the first 30 characters as a substring
        result = fetch_sinks_by_substring_match(substring_to_match)

        # Verify that the correct StructureServiceSinkDBModel is returned
        assert len(result) == 1
        assert result[0].name == example_sink.name


@pytest.mark.usefixtures("_db_test_structure")
def test_filter_sinks_by_substring_match_no_matches(mocked_clean_test_db_session):
    result = fetch_sinks_by_substring_match("Nonexistent")

    # Assert that no StructureServiceSinkDBModel is returned
    assert len(result) == 0


@pytest.mark.usefixtures("_db_test_structure")
def test_filter_sources_by_substring_match_success(mocked_clean_test_db_session):
    with mocked_clean_test_db_session() as session:
        # Fetch an example source name from the database to use in the test
        example_source = session.query(StructureServiceSourceDBModel).first()
        assert example_source is not None, "No sources found in the database."

        # Use a substring of the example source's name to perform the search
        substring_to_match = example_source.name[:30]  # Take the first 30 characters as a substring
        result = fetch_sources_by_substring_match(substring_to_match)

        # Verify that the correct StructureServiceSourceDBModel is returned
        assert len(result) == 1
        assert result[0].name == example_source.name


@pytest.mark.usefixtures("_db_test_structure")
def test_filter_sources_by_substring_match_no_matches(mocked_clean_test_db_session):
    result = fetch_sources_by_substring_match("Nonexistent")

    # Assert that no StructureServiceSourceDBModel is returned
    assert len(result) == 0

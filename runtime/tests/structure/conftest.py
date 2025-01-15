from typing import Any
from unittest import mock

import pytest
from sqlalchemy.future.engine import Engine

from hetdesrun.persistence.db_engine_and_session import get_db_engine, sessionmaker
from hetdesrun.persistence.structure_service_dbmodels import Base
from hetdesrun.structure.db.structure_service import (
    update_structure_from_file,
)


# Fixture to provide the test database engine
@pytest.fixture(scope="session")
def test_db_engine(use_in_memory_db: bool) -> Engine:
    if use_in_memory_db:
        in_memory_database_url = "sqlite+pysqlite:///:memory:"
        engine = get_db_engine(override_db_url=in_memory_database_url)
    else:
        engine = get_db_engine()
    return engine


# Fixture to clean the database and set up the schema
@pytest.fixture()
def clean_test_db_engine(test_db_engine: Engine) -> Engine:
    Base.metadata.drop_all(test_db_engine)
    Base.metadata.create_all(test_db_engine)
    return test_db_engine


# Fixture to provide a mocked session bound to the clean test database engine
@pytest.fixture()
def mocked_clean_test_db_session(clean_test_db_engine):
    with mock.patch(
        "hetdesrun.persistence.db_engine_and_session.Session",
        sessionmaker(clean_test_db_engine),
    ) as _fixture:
        yield _fixture


# Fixture to determine whether to use an in-memory database, based on pytest options
@pytest.fixture(scope="session")
def use_in_memory_db(pytestconfig: pytest.Config) -> Any:
    return pytestconfig.getoption("use_in_memory_db")


# Fixture to load a basic test structure into the database from a JSON file
@pytest.fixture()
def _db_test_structure(mocked_clean_test_db_session):
    file_path = "tests/structure/data/db_test_structure.json"
    update_structure_from_file(file_path)


# Fixture to provide the file path of the test structure JSON
@pytest.fixture()
def db_test_structure_file_path():
    return "tests/structure/data/db_test_structure.json"


# Fixture to load an unordered test structure into the database from a JSON file
@pytest.fixture()
def _db_test_unordered_structure(mocked_clean_test_db_session):
    file_path = "tests/structure/data/db_test_unordered_structure.json"
    update_structure_from_file(file_path)

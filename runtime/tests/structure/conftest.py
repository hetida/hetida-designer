from typing import Any
from unittest import mock

import pytest
from sqlalchemy.future.engine import Engine

from hetdesrun.persistence.dbmodels import Base
from hetdesrun.structure.db import get_db_engine, sessionmaker


@pytest.fixture(scope="session")
def test_db_engine(use_in_memory_db: bool) -> Engine:
    if use_in_memory_db:
        in_memory_database_url = "sqlite+pysqlite:///:memory:"
        engine = get_db_engine(override_db_url=in_memory_database_url)
    else:
        engine = get_db_engine()
    return engine


@pytest.fixture()
def clean_test_db_engine(test_db_engine: Engine) -> Engine:
    Base.metadata.drop_all(test_db_engine)
    Base.metadata.create_all(test_db_engine)
    return test_db_engine


@pytest.fixture()
def mocked_clean_test_db_session(clean_test_db_engine):
    with mock.patch(
        "hetdesrun.structure.db.Session",
        sessionmaker(clean_test_db_engine),
    ) as _fixture:
        yield _fixture


@pytest.fixture(scope="session")
def use_in_memory_db(pytestconfig: pytest.Config) -> Any:
    return pytestconfig.getoption("use_in_memory_db")

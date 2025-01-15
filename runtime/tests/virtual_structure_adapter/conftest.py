from typing import Any
from unittest import mock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.future.engine import Engine

from hetdesrun.persistence.db_engine_and_session import get_db_engine, sessionmaker
from hetdesrun.persistence.structure_service_dbmodels import Base
from hetdesrun.structure.db.structure_service import update_structure_from_file
from hetdesrun.webservice.application import init_app


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
        "hetdesrun.persistence.db_engine_and_session.Session",
        sessionmaker(clean_test_db_engine),
    ) as _fixture:
        yield _fixture


@pytest.fixture(scope="session")
def use_in_memory_db(pytestconfig: pytest.Config) -> Any:
    return pytestconfig.getoption("use_in_memory_db")


@pytest.fixture(scope="function")  # noqa: PT003
def _fill_db(mocked_clean_test_db_session):
    file_path = "tests/virtual_structure_adapter/data/simple_end_to_end_with_any_test.json"
    update_structure_from_file(file_path)


@pytest.fixture(scope="session")
def app_without_auth() -> FastAPI:
    with mock.patch("hetdesrun.webservice.config.runtime_config.auth", False):
        return init_app()


@pytest.fixture()
def async_test_client_with_vst_adapter(
    _fill_db,
    app_without_auth: FastAPI,
) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app_without_auth), base_url="http://test")

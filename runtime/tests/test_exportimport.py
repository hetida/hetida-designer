import os

from unittest import mock
import pytest

from starlette.testclient import TestClient

from hetdesrun.webservice.application import app

from hetdesrun.exportimport.importing import transformation_revision_from_python_code

from hetdesrun.persistence import get_db_engine, sessionmaker
from hetdesrun.persistence.dbmodels import Base

client = TestClient(app)


@pytest.fixture(scope="function")
def clean_test_db_engine(use_in_memory_db):
    if use_in_memory_db:
        in_memory_database_url = "sqlite+pysqlite:///:memory:"
        engine = get_db_engine(override_db_url=in_memory_database_url)
    else:
        engine = get_db_engine()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    return engine


@pytest.mark.asyncio
async def test_execute_for_component_without_hetdesrun_imports(clean_test_db_engine):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        path = os.path.join(
                "tests",
                "data",
                "components",
                "alerts-from-score_100_38f168ef-cb06-d89c-79b3-0cd823f32e9d.py",
            )
        with open(path) as f:
            code = f.read()

        tr_json = transformation_revision_from_python_code(code, path)

        assert tr_json["id"] == "38f168ef-cb06-d89c-79b3-0cd823f32e9d"

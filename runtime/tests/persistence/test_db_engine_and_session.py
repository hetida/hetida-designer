from unittest import mock

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from hetdesrun.persistence.db_engine_and_session import db_url_for_logging, is_in_memory_db


@pytest.mark.filterwarnings("ignore:Selection of the SingletonThreadPool")
@pytest.mark.parametrize(
    ("db_url", "expected"),
    [
        ("sqlite+pysqlite:///:memory:", True),
        ("sqlite://", True),
        ("sqlite:///", True),
        ("sqlite:///file::memory:?cache=shared&uri=true", True),
        ("sqlite:///file::memory:?uri=True", True),
        ("sqlite:///file::memory:?uri=1", True),
        ("sqlite:///file:memdb1?mode=memory&cache=shared&uri=true", True),
        ("sqlite:///file:?uri=true", True),  # temporary db
        ("sqlite:///file://localhost?uri=true", True),  # temporary db, with authority
        ("sqlite:///file::memory:", False),  # without uri=true this is a file name
        ("sqlite:///file::memory:?uri=false", False),
        ("sqlite:///hd.db?mode=memory&uri=true", False),  # file "hd.db?mode=memory"
        ("sqlite:///file:hd.db?uri=true", False),
        ("sqlite+pysqlite:///./hd.db", False),
        ("sqlite:///hd.db", False),
        ("postgresql+psycopg://user:password@host:5432/db", False),
    ],
)
def test_is_in_memory_db(db_url, expected, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # file dbs are created here
    engine = create_engine(db_url)

    with mock.patch(
        "hetdesrun.persistence.db_engine_and_session.get_db_engine", return_value=engine
    ):
        assert is_in_memory_db() is expected

    if engine.dialect.name == "sqlite":
        # sqlite itself agrees: in-memory and temporary dbs have no file
        try:
            with engine.connect() as connection:
                db_file = connection.execute(text("PRAGMA database_list")).fetchone()[2]
        finally:
            engine.dispose()  # closes the pooled connection
        assert (db_file == "") is expected


@pytest.mark.parametrize(
    ("db_url", "expected"),
    [
        (
            "postgresql+psycopg://user:secret@host:5432/db",
            "postgresql+psycopg://user:***@host:5432/db",
        ),
        (
            "postgresql+psycopg://user@host/db?password=secret&sslmode=require",
            "postgresql+psycopg://user@host/db?password=***&sslmode=require",
        ),
        ("sqlite+pysqlite:///:memory:", "sqlite+pysqlite:///:memory:"),
    ],
)
def test_db_url_for_logging(db_url, expected):
    assert db_url_for_logging(make_url(db_url)) == expected

    with mock.patch(
        "hetdesrun.persistence.db_engine_and_session.get_db_engine",
        return_value=mock.Mock(url=make_url(db_url)),
    ):
        assert db_url_for_logging() == expected

from __future__ import annotations  # for type hinting the Session from sessionmaker

import json
import logging
from functools import cache
from typing import Any
from uuid import UUID

from pydantic import SecretStr
from sqlalchemy import create_engine, event
from sqlalchemy.engine import URL
from sqlalchemy.future.engine import Engine
from sqlalchemy.orm import Session as SQLAlchemySession  # noqa: F401
from sqlalchemy.orm import sessionmaker

from hetdesrun.structure.models import (
    Filter,
)
from hetdesrun.webservice.config import get_config

logger = logging.getLogger(__name__)


def _default(val: Any) -> Any:
    if isinstance(val, UUID):
        return str(val)
    if isinstance(val, Filter):
        return {
            "name": val.name,
            "type": val.type.value,
            "required": val.required,
        }
    raise TypeError(f"Object of type {type(val).__name__} is not JSON serializable")


def dumps(d: Any) -> str:
    return json.dumps(d, default=_default)


@cache
def get_db_engine(override_db_url: SecretStr | str | URL | None = None) -> Engine:
    if get_config().sqlalchemy_connection_string is None:
        raise TypeError("No sqlalchemy connection string configured/inferred!")

    db_url_to_use: SecretStr | str | URL
    if override_db_url is None:
        db_url_to_use = get_config().sqlalchemy_connection_string  # type: ignore
    else:
        db_url_to_use = override_db_url

    if isinstance(db_url_to_use, SecretStr):
        db_url_to_use = db_url_to_use.get_secret_value()

    if isinstance(db_url_to_use, URL):
        db_url_to_use = db_url_to_use.render_as_string(hide_password=False)

    engine = create_engine(  # type: ignore
        db_url_to_use,
        future=True,
        json_serializer=dumps,
        connect_args={"options": "-c timezone=utc"} if db_url_to_use.startswith("postgres") else {},
        **(
            {"pool_size": get_config().sqlalchemy_pool_size}
            if not str(db_url_to_use).startswith("sqlite://")
            else {}
        ),
    )

    if engine.dialect.name == "sqlite":
        # SQLite does not enforce foreign key constraints unless explicitly enabled per
        # connection. The persistence schema relies on foreign keys (e.g. nestings ->
        # transformation_revisions), so enable enforcement to get the same integrity
        # guarantees as on postgres. Scoped to this engine so it does not affect other
        # engines (e.g. user-configured sql adapter databases).
        @event.listens_for(engine, "connect")
        def _enable_sqlite_foreign_keys(dbapi_connection: Any, _connection_record: Any) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    logger.debug("Created DB Engine with url: %s", repr(engine.url))

    return engine  # type: ignore


Session = sessionmaker(get_db_engine())


def get_session() -> sessionmaker[SQLAlchemySession]:
    return Session

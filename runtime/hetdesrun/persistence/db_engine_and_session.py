from __future__ import annotations  # for type hinting the Session from sessionmaker

import json
import logging
from functools import cache
from typing import Any
from uuid import UUID

from pydantic import SecretStr
from sqlalchemy import create_engine
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
        **(
            {"pool_size": get_config().sqlalchemy_pool_size}
            if not str(db_url_to_use).startswith("sqlite://")
            else {}
        ),
    )

    logger.debug("Created DB Engine with url: %s", repr(engine.url))

    return engine  # type: ignore


Session = sessionmaker(get_db_engine())


def get_session() -> sessionmaker[SQLAlchemySession]:
    return Session

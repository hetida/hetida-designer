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

from hetdesrun.structure.config import get_config

logger = logging.getLogger(__name__)


def _default(val: Any) -> str:
    if isinstance(val, UUID):
        return str(val)
    raise TypeError()


def dumps(d: Any) -> str:
    return json.dumps(d, default=_default)


@cache
def get_db_engine(override_db_url: SecretStr | str | URL | None = None) -> Engine:
    if get_config().db_url is None:
        raise TypeError("No db url configured/inferred!")

    db_url_to_use: SecretStr | str | URL

    db_url_to_use = get_config().db_url if override_db_url is None else override_db_url  # type: ignore

    if isinstance(db_url_to_use, SecretStr):
        db_url_to_use = db_url_to_use.get_secret_value()

    engine = create_engine(  # type: ignore
        str(db_url_to_use),
        future=True,
        json_serializer=dumps,
        pool_size=get_config().db_pool_size,
    )

    logger.debug("Created DB Engine with url: %s", repr(engine.url))

    return engine


Session = sessionmaker(get_db_engine())


def get_session() -> sessionmaker[SQLAlchemySession]:
    return Session

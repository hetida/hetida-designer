import json
import logging
from functools import cache
from typing import Any, Optional, Union
from uuid import UUID

# pylint: disable=no-name-in-module
from pydantic import SecretStr
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.future.engine import Engine
from sqlalchemy.orm import Session as SQLAlchemySession
from sqlalchemy.orm import sessionmaker

from hetdesrun.webservice.config import get_config

logger = logging.getLogger(__name__)


def _default(val: Any) -> str:
    if isinstance(val, UUID):
        return str(val)
    raise TypeError()


def dumps(d: Any) -> str:
    return json.dumps(d, default=_default)


@cache
def get_db_engine(
    override_db_url: Optional[Union[SecretStr, str, URL]] = None
) -> Engine:

    assert get_config().sqlalchemy_connection_string is not None

    db_url_to_use: Union[SecretStr, str, URL]
    if override_db_url is None:
        db_url_to_use = get_config().sqlalchemy_connection_string  # type: ignore
    else:
        db_url_to_use = override_db_url

    if isinstance(db_url_to_use, SecretStr):
        db_url_to_use = db_url_to_use.get_secret_value()

    engine = create_engine(  # type: ignore
        str(db_url_to_use),
        future=True,
        json_serializer=dumps,
        pool_size=get_config().sqlalchemy_pool_size,
    )

    logger.debug("Created DB Engine with url: %s", repr(engine.url))

    return engine


Session = sessionmaker(get_db_engine())

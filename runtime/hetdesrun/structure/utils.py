from functools import cache

from sqlalchemy.engine import Engine


@cache
def is_postgresql(engine: Engine) -> bool:
    return engine.dialect.name == "postgresql"


@cache
def is_sqlite(engine: Engine) -> bool:
    return engine.dialect.name == "sqlite"

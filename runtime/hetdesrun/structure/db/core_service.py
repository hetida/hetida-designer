import logging

from sqlalchemy import Column, Integer, MetaData, Table, inspect
from sqlalchemy.sql.type_api import TypeEngine

from hetdesrun.persistence.db_engine_and_session import get_db_engine

logger = logging.getLogger(__name__)

metadata = MetaData()


def create_property_table(name: str, columns: list[tuple[str, TypeEngine]]) -> Table:
    inspector = inspect(get_db_engine())
    if not inspector.has_table(name):
        column_definitions = [Column("id", Integer, primary_key=True)] + [
            Column(column_name, column_type) for column_name, column_type in columns
        ]

        table = Table(name, metadata, *column_definitions)
        table.create(bind=get_db_engine())
    else:
        table = Table(name, metadata, autoload_with=get_db_engine())
    return table

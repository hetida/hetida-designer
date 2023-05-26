from sqlalchemy import create_engine, inspect

from hetdesrun.adapters.exceptions import AdapterHandlingException
from hetdesrun.adapters.sql_reader.config import (
    SQLReaderDBConfig,
)
from hetdesrun.adapters.sql_reader.models import (
    SQLReaderStructureSource,
    StructureResponse,
    StructureThingNode,
)
from hetdesrun.adapters.sql_reader.utils import get_configured_dbs_by_key


def get_table_names(uri: str) -> list[str]:
    engine = create_engine(uri)
    inspection = inspect(engine)
    return inspection.get_table_names()


def get_sources_of_db(db_config: SQLReaderDBConfig) -> list[SQLReaderStructureSource]:
    return [
        SQLReaderStructureSource(
            id=db_config.key + "/query",
            thingNodeId=db_config.key,
            name="SQL Query in " + db_config.name,
            path=db_config.key + "|" + db_config.name + "/query/sql",
            filters={
                "sql_query": {
                    "name": " SQL Query",
                    "type": "free_text",
                    "required": True,
                }
            },
        )
    ] + [
        # query source
        SQLReaderStructureSource(
            id=db_config.key + "/table/" + table_name,
            thingNodeId=db_config.key,
            name="Table " + table_name,
            path=db_config.key + "|" + db_config.name + "/table/" + table_name,
        )
        for table_name in get_table_names(db_config.connection_url)
    ]


def get_all_db_sources(
    db_configs: list[SQLReaderDBConfig],
) -> list[SQLReaderStructureSource]:
    sources = []
    for db_config in db_configs:
        sources.extend(get_sources_of_db(db_config))
    return sources


def filter_sql_sources(
    sql_sources: list[SQLReaderStructureSource], filter_str: str  # noqa: A002
) -> list[SQLReaderStructureSource]:
    filter_lower = filter_str.lower()

    return [
        x
        for x in sql_sources
        if filter_lower in x.name.lower() or filter_lower in x.path.lower()
    ]


def get_structure(parent_id: str | None = None) -> StructureResponse:
    configured_dbs_by_key = get_configured_dbs_by_key()

    if parent_id is None:
        # available databases
        return StructureResponse(
            id="sql-table-reader-adapter",
            name="SQL Reader Adapter",
            thingNodes=[
                StructureThingNode(
                    id=configured_db.key,
                    name=configured_db.name,
                    parentId=None,
                    description="Configured database " + configured_db.name,
                )
                for configured_db in configured_dbs_by_key.values()
            ],
            sources=[],
            sinks=[],
        )

    if parent_id in configured_dbs_by_key:
        return StructureResponse(
            id="db/" + parent_id,
            name=configured_dbs_by_key[parent_id].name,
            thingNodes=[
                # tables
            ],
            sources=get_sources_of_db(configured_dbs_by_key[parent_id]),
            sinks=[],
        )

    raise AdapterHandlingException("Unknown database key provided as parent_id")


def get_source_by_id(source_id: str) -> SQLReaderStructureSource | None:
    """Get a specific sql source by id

    Returns None if source could not be found.
    """

    configured_dbs_by_key = get_configured_dbs_by_key()

    id_split = source_id.split("/", 2)
    db_key = id_split[0]

    if db_key not in configured_dbs_by_key or len(id_split) < 2:
        return None

    source_type = id_split[1]

    if source_type == "query" and len(id_split) == 2:
        db_config = configured_dbs_by_key[db_key]
        return SQLReaderStructureSource(
            id=source_id,
            thingNodeId=db_key,
            name="SQL Query in " + db_config.name,
            path=db_key + "|" + db_config.name + "/query/sql",
            filters={
                "sql_query": {
                    "name": " SQL Query",
                    "type": "free_text",
                    "required": True,
                }
            },
        )
    if source_type == "table":
        db_config = configured_dbs_by_key[db_key]
        table_name = id_split[2]
        return SQLReaderStructureSource(
            id=source_id,
            thingNodeId=db_key,
            name="Table " + table_name,
            path=db_key + "|" + db_config.name + "/table/" + table_name,
        )
    return None


def get_sources(filter_str: str | None) -> list[SQLReaderStructureSource]:
    configured_dbs_by_key = get_configured_dbs_by_key()

    all_sources = get_all_db_sources(configured_dbs_by_key.values())

    if filter_str is None:
        return all_sources

    return filter_sql_sources(all_sources, filter_str)


def get_thing_node_by_id(
    id: str,  # noqa: A002
) -> StructureThingNode | None:
    configured_dbs_by_key = get_configured_dbs_by_key()

    if id in configured_dbs_by_key:
        configured_db = configured_dbs_by_key[id]
        return StructureThingNode(
            id=configured_db.key,
            name=configured_db.name,
            parentId=None,
            description="Configured database " + configured_db.name,
        )

    return None

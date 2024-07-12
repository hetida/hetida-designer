import logging
from collections.abc import Iterable

from pydantic import ValidationError
from sqlalchemy import create_engine, inspect

from hetdesrun.adapters.exceptions import AdapterHandlingException
from hetdesrun.adapters.generic_rest.external_types import ExternalType
from hetdesrun.adapters.sql_adapter.config import (
    SQLAdapterDBConfig,
)
from hetdesrun.adapters.sql_adapter.models import (
    SQLAdapterStructureSink,
    SQLAdapterStructureSource,
    StructureResponse,
    StructureThingNode,
    WriteTable,
    WriteTableMode,
    to_table_type_str,
)
from hetdesrun.adapters.sql_adapter.utils import get_configured_dbs_by_key

logger = logging.getLogger(__name__)


def get_table_names(uri: str) -> list[str]:
    engine = create_engine(uri)
    inspection = inspect(engine)
    return inspection.get_table_names()


def is_allowed_dataframe_source_table(table_name: str, db_config: SQLAdapterDBConfig) -> bool:
    return (
        (db_config.explicit_source_tables is None or table_name in db_config.explicit_source_tables)
        and not table_name in db_config.ignore_tables
        and not table_name in db_config.timeseries_tables
    )


def get_allowed_dataframe_source_tables(db_config: SQLAdapterDBConfig) -> list[str]:
    return [
        table_name
        for table_name in get_table_names(db_config.connection_url)
        if is_allowed_dataframe_source_table(table_name, db_config)
    ]


def get_sources_of_db(db_config: SQLAdapterDBConfig) -> list[SQLAdapterStructureSource]:
    return (
        [
            # query source
            SQLAdapterStructureSource(
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
        ]
        + [
            # dataframe source tables
            SQLAdapterStructureSource(
                id=db_config.key + "/table/" + table_name,
                thingNodeId=db_config.key,
                name="Table " + table_name,
                path=db_config.key + "|" + db_config.name + "/table/" + table_name,
            )
            for table_name in get_allowed_dataframe_source_tables(db_config)
        ]
        + [
            SQLAdapterStructureSource(
                id=db_config.key + "/ts_table/" + ts_table_name,
                thingNodeId=db_config.key,
                type=ExternalType.MULTITSFRAME,
                name="Timeseries Table " + ts_table_name,
                path=db_config.key + "|" + db_config.name + "/ts_table/" + ts_table_name,
                filters={
                    "metrics": {  # metric ids as comma separated string
                        "name": "Metrics (json array or just comma separated or ALL)",
                        "type": "free_text",
                        "required": True,
                    }
                },
            )
            for ts_table_name in db_config.timeseries_tables
        ]
    )


def get_all_db_sources(
    db_configs: Iterable[SQLAdapterDBConfig],
) -> list[SQLAdapterStructureSource]:
    sources = []
    for db_config in db_configs:
        sources.extend(get_sources_of_db(db_config))
    return sources


def filter_sql_sources(
    sql_sources: Iterable[SQLAdapterStructureSource],
    filter_str: str,  # noqa: A002
) -> list[SQLAdapterStructureSource]:
    filter_lower = filter_str.lower()

    return [
        x for x in sql_sources if filter_lower in x.name.lower() or filter_lower in x.path.lower()
    ]


def get_sinks_of_db(db_config: SQLAdapterDBConfig) -> list[SQLAdapterStructureSink]:
    return (
        [
            SQLAdapterStructureSink(
                id=db_config.key + "/append_table/" + append_table_name,
                thingNodeId=db_config.key,
                name="Append Table " + append_table_name,
                path=db_config.key + "|" + db_config.name + "/append_table/" + append_table_name,
            )
            for append_table_name in db_config.append_tables
        ]
        + [
            SQLAdapterStructureSink(
                id=db_config.key + "/replace_table/" + replace_table_name,
                thingNodeId=db_config.key,
                name="Replace Table " + replace_table_name,
                path=db_config.key + "|" + db_config.name + "/replace_table/" + replace_table_name,
            )
            for replace_table_name in db_config.replace_tables
        ]
        + [
            # appendable timeseries tables
            SQLAdapterStructureSink(
                id=db_config.key + "/appendable_ts_table/" + timeseries_table_name,
                thingNodeId=db_config.key,
                type=ExternalType.MULTITSFRAME,
                name="Timeseries Table " + timeseries_table_name,
                path=db_config.key
                + "|"
                + db_config.name
                + "/appendable_ts_table/"
                + timeseries_table_name,
            )
            for timeseries_table_name in db_config.timeseries_tables
            if db_config.timeseries_tables[timeseries_table_name].appendable
        ]
    )


def get_all_db_sinks(
    db_configs: Iterable[SQLAdapterDBConfig],
) -> list[SQLAdapterStructureSink]:
    sinks = []
    for db_config in db_configs:
        sinks.extend(get_sinks_of_db(db_config))
    return sinks


def filter_sql_sinks(
    sql_sinks: Iterable[SQLAdapterStructureSink],
    filter_str: str,  # noqa: A002
) -> list[SQLAdapterStructureSink]:
    filter_lower = filter_str.lower()

    return [
        x for x in sql_sinks if filter_lower in x.name.lower() or filter_lower in x.path.lower()
    ]


def get_structure(parent_id: str | None = None) -> StructureResponse:
    configured_dbs_by_key = get_configured_dbs_by_key()

    if parent_id is None:
        # available databases
        return StructureResponse(
            id="sql-adapter",
            name="SQL Adapter",
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
            thingNodes=[],
            sources=get_sources_of_db(configured_dbs_by_key[parent_id]),
            sinks=get_sinks_of_db(configured_dbs_by_key[parent_id]),
        )

    raise AdapterHandlingException("Unknown database key provided as parent_id")


def get_source_by_id(source_id: str) -> SQLAdapterStructureSource | None:
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
        return SQLAdapterStructureSource(
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
        return SQLAdapterStructureSource(
            id=source_id,
            thingNodeId=db_key,
            name="Table " + table_name,
            path=db_key + "|" + db_config.name + "/table/" + table_name,
        )

    if source_type == "ts_table":
        db_config = configured_dbs_by_key[db_key]
        ts_table_name = id_split[2]
        return SQLAdapterStructureSource(
            id=db_config.key + "/ts_table/" + ts_table_name,
            thingNodeId=db_config.key,
            type=ExternalType.MULTITSFRAME,
            name="Timeseries Table " + ts_table_name,
            path=db_config.key + "|" + db_config.name + "/ts_table/" + ts_table_name,
            filters={
                "metrics": {  # metric ids as comma separated string
                    "name": "Metrics (json array or just comma separated or ALL)",
                    "type": "free_text",
                    "required": True,
                }
            },
        )
    return None


def get_sink_by_id(sink_id: str) -> SQLAdapterStructureSink | None:
    """Get a specific sql sink by id

    Returns None if sink could not be found.
    """

    # Parse sink_id
    try:
        write_table = WriteTable.from_sink_id(sink_id)
    except ValidationError as e:
        msg = f"Could not parse and validate sink id {sink_id}. Error was {str(e)}."
        logger.info(msg)  # noqa: G003
        return None

    # Handle appendable ts tables
    if write_table.write_mode is WriteTableMode.TIMSERIES_APPEND:
        if write_table.db_config.timeseries_tables[write_table.table_name].appendable:
            return SQLAdapterStructureSink(
                id=write_table.sink_id,
                thingNodeId=write_table.db_config.key,
                type=ExternalType.MULTITSFRAME,
                name="Timeseries Table " + write_table.table_name,
                path=write_table.db_config.key
                + "|"
                + write_table.db_config.name
                + "/"
                + to_table_type_str(write_table.write_mode)
                + "/"
                + write_table.table_name,
            )
        logger.debug(
            "Timeseries table %s is not appendable!",
            str(
                write_table.table_name,
            ),
        )
        return None

    # Handle table not present
    if (
        write_table.write_mode is WriteTableMode.APPEND
        and write_table.table_name not in write_table.db_config.append_tables
    ):
        return None
    if (
        write_table.write_mode is WriteTableMode.REPLACE
        and write_table.table_name not in write_table.db_config.replace_tables
    ):
        return None

    return SQLAdapterStructureSink(
        id=write_table.sink_id,
        thingNodeId=write_table.db_config.key,
        name=(
            "Replace Table "
            if write_table.write_mode is WriteTableMode.REPLACE
            else "Append Table "
        )
        + write_table.table_name,
        path=write_table.db_config.key
        + "|"
        + write_table.db_config.name
        + "/"
        + to_table_type_str(write_table.write_mode)
        + "/"
        + write_table.table_name,
    )


def get_sources(filter_str: str | None = None) -> list[SQLAdapterStructureSource]:
    configured_dbs_by_key = get_configured_dbs_by_key()

    all_sources = get_all_db_sources(configured_dbs_by_key.values())

    if filter_str is None:
        return all_sources

    return filter_sql_sources(all_sources, filter_str)


def get_sinks(filter_str: str | None = None) -> list[SQLAdapterStructureSink]:
    configured_dbs_by_key = get_configured_dbs_by_key()

    all_sinks = get_all_db_sinks(configured_dbs_by_key.values())

    if filter_str is None:
        return all_sinks

    return filter_sql_sinks(all_sinks, filter_str)


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

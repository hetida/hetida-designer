import logging

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError as SQLOpsError

from hetdesrun.adapters.exceptions import AdapterHandlingException
from hetdesrun.adapters.sql_adapter.config import SQLAdapterDBConfig
from hetdesrun.adapters.sql_adapter.utils import get_configured_dbs_by_key

logger = logging.getLogger(__name__)


def load_table_from_provided_source_id(
    source_id: str, source_filters: dict
) -> pd.DataFrame:
    configured_dbs_by_key = get_configured_dbs_by_key()

    id_split = source_id.split("/", 2)
    db_key = id_split[0]

    if db_key not in configured_dbs_by_key or len(id_split) < 2:
        msg = f"Invalid source id requested from sql adapter: {source_id}"
        logger.info(msg)
        raise AdapterHandlingException(msg)

    db_config = configured_dbs_by_key[db_key]

    if id_split[1] == "query" and len(id_split) == 2:
        query = source_filters.get("sql_query", None)
        if query is None:
            msg = (
                "Source of type query from sql adapter but no sql_query filter!\n"
                f"Source id: {source_id}\n"
                f"source filters: {str(source_filters)}"
            )
            logger.info(msg)
            raise AdapterHandlingException(msg)
        return load_sql_query(db_config, query)

    if id_split[1] == "table" and len(id_split) > 2:
        table_name = id_split[2]
        return load_sql_table(db_config, table_name)

    msg = (
        "Invalid source id structure. Cannot find or identify source."
        f"source id: {source_id}"
    )
    logger.info(msg)
    raise AdapterHandlingException(msg)


def load_sql_table(db_config: SQLAdapterDBConfig, table_name: str) -> pd.DataFrame:
    engine = create_engine(db_config.connection_url)
    try:
        return pd.read_sql_table(table_name, engine)
    except SQLOpsError as e:
        msg = f"Sql adapter pandas sql reading error: {str(e)}"
        logger.info(msg)
        raise AdapterHandlingException(msg) from e


def load_sql_query(db_config: SQLAdapterDBConfig, query: str) -> pd.DataFrame:
    engine = create_engine(db_config.connection_url)
    try:
        return pd.read_sql_query(query, engine)
    except SQLOpsError as e:
        msg = f"Sql adapter pandas sql query error: {str(e)}"
        logger.info(msg)
        raise AdapterHandlingException(msg) from e

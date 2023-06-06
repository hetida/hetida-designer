import logging

import pandas as pd

from hetdesrun.adapters.exceptions import AdapterHandlingException
from hetdesrun.adapters.sql_adapter.utils import get_configured_dbs_by_key
from sqlalchemy.exc import OperationalError as SQLOpsError
from sqlalchemy import create_engine

logger = logging.getLogger(__name__)


def write_table_to_provided_sink_id(data: pd.DataFrame, sink_id: str) -> None:
    configured_dbs_by_key = get_configured_dbs_by_key()

    id_split = sink_id.split("/", 2)
    db_key = id_split[0]

    if db_key not in configured_dbs_by_key or len(id_split) < 3:
        msg = f"Invalid sink id requested from sql adapter: {sink_id}"
        logger.info(msg)
        raise AdapterHandlingException(msg)

    db_config = configured_dbs_by_key[db_key]

    write_mode = "append"

    if id_split[1] == "append_table":
        write_mode = "append"
    elif id_split[1] == "replace_table":
        write_mode = "replace"
    else:
        raise AdapterHandlingException("Unknown table mode!")

    table_name = id_split[2]

    engine = create_engine(db_config.connection_url)
    try:
        data.to_sql(table_name, engine, if_exists=write_mode, index=False)
    except SQLOpsError as e:
        msg = f"Sql adapter pandas to_sql writing error: {str(e)}"
        logger.info(msg)
        raise AdapterHandlingException(msg) from e

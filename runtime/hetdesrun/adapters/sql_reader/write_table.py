import logging

import pandas as pd

from hetdesrun.adapters.exceptions import AdapterHandlingException
from hetdesrun.adapters.sql_reader.utils import get_configured_dbs_by_key

logger = logging.getLogger(__name__)


def write_table_to_provided_sink_id(data: pd.DataFrame, sink_id: str) -> None:
    configured_dbs_by_key = get_configured_dbs_by_key()

    id_split = sink_id.split("/", 2)
    db_key = id_split[0]

    if db_key not in configured_dbs_by_key or len(id_split) < 3:
        msg = f"Invalid sink id requested from sql reader adapter: {sink_id}"
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

    data.to_sql(table_name, db_config.connection_url, if_exists=write_mode, index=False)

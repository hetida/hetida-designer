import logging

import pandas as pd
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError as SQLOpsError

from hetdesrun.adapters.exceptions import AdapterHandlingException
from hetdesrun.adapters.sql_adapter.models import WriteTable

logger = logging.getLogger(__name__)


def write_table_to_provided_sink_id(data: pd.DataFrame, sink_id: str) -> None:
    try:
        write_table = WriteTable.from_sink_id(sink_id)
    except ValidationError as e:
        msg = "Could not parse and validate sink id."
        logger.info(msg + f"Error was: {str(e)}")  # noqa: G003
        raise AdapterHandlingException(msg) from e

    engine = create_engine(write_table.db_config.connection_url)
    try:
        data.to_sql(
            write_table.table_name,
            engine,
            if_exists=write_table.pandas_if_exists_mode,
            index=False,
        )
    except SQLOpsError as e:
        msg = f"Sql adapter pandas to_sql writing error: {str(e)}"
        logger.info(msg)
        raise AdapterHandlingException(msg) from e

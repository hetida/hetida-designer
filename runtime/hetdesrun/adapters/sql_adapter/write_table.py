import logging

import pandas as pd
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError as SQLOpsError

from hetdesrun.adapters.exceptions import AdapterHandlingException
from hetdesrun.adapters.sql_adapter.models import WriteTable, WriteTableMode
from hetdesrun.adapters.sql_adapter.utils import get_configured_dbs_by_key

logger = logging.getLogger(__name__)


def write_table_to_provided_sink_id(data: pd.DataFrame, sink_id: str) -> None:
    try:
        write_table = WriteTable.from_sink_id(sink_id)
    except ValidationError as e:
        msg = f"Could not parse and validate sink id {sink_id}. Error was {str(e)}."
        logger.info(msg)  # noqa: G003
        raise AdapterHandlingException(msg) from e

    data_to_send = data

    if write_table.write_mode is WriteTableMode.TIMSERIES_APPEND:
        configured_dbs_by_key = get_configured_dbs_by_key()
        db_config = configured_dbs_by_key[write_table.db_key]
        ts_table_config = db_config.timeseries_tables[write_table.table_name]

        if not ts_table_config.appendable:
            msg = (
                f"Configured timeseries table {write_table.table_name} for "
                f"db key {write_table.db_key} is not appendable. Aborting write"
                "operation for sink_id {sink_id}."
            )
            logger.error(msg)
            raise AdapterHandlingException(msg)

            expected_columns = [
                ts_table_config.metric_col_name,
                ts_table_config.timestamp_col_name,
            ] + ts_table_config.fetchable_value_cols

            if not set(expected_columns) in set(data_to_send.columns):
                msg = (
                    f"Could not find expected columns {expected_columns}"
                    f" in the provided dataframe columns {data_to_send.columns}."
                    f" Aborting write operation for db key {write_table.db_key} for"
                    f" sink id {sink_id}"
                )

            data_to_send = data[expected_columns]

    engine = create_engine(write_table.db_config.connection_url)
    try:
        data_to_send.to_sql(
            write_table.table_name,
            engine,
            if_exists=write_table.pandas_if_exists_mode,
            index=False,
        )
    except SQLOpsError as e:
        msg = f"Sql adapter pandas to_sql writing error: {str(e)}"
        logger.info(msg)
        raise AdapterHandlingException(msg) from e

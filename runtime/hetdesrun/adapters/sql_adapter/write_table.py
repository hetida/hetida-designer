import logging

import pandas as pd
from pydantic import ValidationError
from sqlalchemy.exc import OperationalError as SQLOpsError

from hetdesrun.adapters.exceptions import AdapterHandlingException
from hetdesrun.adapters.sql_adapter.config import TimeseriesTableConfig
from hetdesrun.adapters.sql_adapter.models import WriteTable, WriteTableMode
from hetdesrun.adapters.sql_adapter.utils import (
    get_configured_dbs_by_key,
    validate_multits_frame,
)

logger = logging.getLogger(__name__)


def prepare_validate_multitsframe(
    data_to_send: pd.DataFrame,
    ts_table_config: TimeseriesTableConfig,
    sink_id: str,
    write_table: WriteTable,
) -> pd.DataFrame:
    """Make sure the dataframe is a multitsframe as expected and contains expected columns"""

    # Guarantee that the database will only receive utc timestamps.
    # Naive timestamps will be assumed to be UTC, non-naive will be transformed to
    # explicit UTC timestamps
    if "timestamp" in data_to_send.columns:
        data_to_send["timestamp"] = pd.to_datetime(data_to_send["timestamp"], utc=True)

    try:
        data_to_send = validate_multits_frame(data_to_send)
    except ValidationError as e:  # pragma: no cover
        msg = (
            "Could not validate multi ts frame prepared for sending via"
            f" sql adapter with sink id {sink_id}. Error was: \n{str(e)}"
        )
        raise AdapterHandlingException(msg) from e

    # Column mapping

    data_to_send.rename(
        columns=ts_table_config.column_mapping_hd_to_db,
        inplace=True,  # noqa:PD002
    )

    expected_columns = [
        ts_table_config.metric_col_name,
        ts_table_config.timestamp_col_name,
    ] + ts_table_config.writable_value_cols

    if not set(expected_columns).issubset(set(data_to_send.columns)):  # pragma: no cover
        msg = (
            f"Could not find expected columns {expected_columns}"
            f" in the provided dataframe columns {data_to_send.columns}."
            f" Aborting write operation for db key {write_table.db_key} for"
            f" sink id {sink_id}"
        )
        logger.error(msg)
        raise AdapterHandlingException(msg)

    data_to_send = data_to_send[expected_columns]

    return data_to_send


def write_table_to_provided_sink_id(data: pd.DataFrame, sink_id: str) -> None:
    try:
        write_table = WriteTable.from_sink_id(sink_id)
    except ValidationError as e:  # pragma: no cover
        msg = f"Could not parse and validate sink id {sink_id}. Error was {str(e)}."
        logger.info(msg)  # noqa: G003
        raise AdapterHandlingException(msg) from e

    data_to_send = data.copy()  # deep copy by default!

    configured_dbs_by_key = get_configured_dbs_by_key()
    db_config = configured_dbs_by_key[write_table.db_key]

    if write_table.write_mode is WriteTableMode.TIMSERIES_APPEND:
        ts_table_config = db_config.timeseries_tables[write_table.table_name]

        if not ts_table_config.appendable:  # pragma: no cover
            msg = (
                f"Configured timeseries table {write_table.table_name} for "
                f"db key {write_table.db_key} is not appendable. Aborting write"
                "operation for sink_id {sink_id}."
            )
            logger.error(msg)
            raise AdapterHandlingException(msg)

        data_to_send = prepare_validate_multitsframe(
            data_to_send, ts_table_config, sink_id, write_table
        )

    engine = db_config.engine
    try:
        with engine.begin():  # transactional / roll back in case of exceptions
            data_to_send.to_sql(
                write_table.table_name,
                engine,
                if_exists=write_table.pandas_if_exists_mode,
                index=False,
                method="multi",
            )
    except SQLOpsError as e:
        msg = f"Sql adapter pandas to_sql writing error: {str(e)}"
        logger.info(msg)
        raise AdapterHandlingException(msg) from e

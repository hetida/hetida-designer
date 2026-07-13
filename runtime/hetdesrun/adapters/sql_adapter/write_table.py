import logging
import operator

import pandas as pd
from pydantic import ValidationError
from sqlalchemy import MetaData, Table, and_, delete, tuple_
from sqlalchemy.engine import Connection
from sqlalchemy.exc import OperationalError as SQLOpsError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql.expression import ColumnElement

from hetdesrun.adapters.exceptions import AdapterHandlingException
from hetdesrun.adapters.sql_adapter.config import TimeseriesTableConfig, get_sql_adapter_config
from hetdesrun.adapters.sql_adapter.models import WriteTable, WriteTableMode
from hetdesrun.adapters.sql_adapter.utils import (
    get_configured_dbs_by_key,
    validate_multits_frame,
)
from hetdesrun.models.dataset_metadata import (
    DatasetMetadata,
    IntervalType,
    get_dataset_metadata_from_attrs,
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

    # Ensure correct metric column data type before applying column mapping
    if ts_table_config.metric_type == "str":
        data_to_send["metric"] = data_to_send["metric"].astype(str)
    else:
        try:
            data_to_send["metric"] = data_to_send["metric"].astype(int)
        except (ValueError, TypeError) as e:
            msg = "Error converting metrics to integers while preparing data so send via sql."
            logger.info(msg)
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


# Interval type to operator mapping for deletion process
INTERVAL_OPERATORS = {
    IntervalType.CLOSED: (operator.ge, operator.le),  # >=, <=
    IntervalType.LEFT_CLOSED: (operator.ge, operator.lt),  # >=, <
    IntervalType.RIGHT_CLOSED: (operator.gt, operator.le),  # >, <=
    IntervalType.OPEN: (operator.gt, operator.lt),  # >, <
    IntervalType.LEFT_OPEN: (operator.gt, operator.le),  # Same as right_closed
    IntervalType.RIGHT_OPEN: (operator.ge, operator.lt),  # Same as left_closed
}


def _execute_delete(
    connection: Connection, clause: ColumnElement, table: Table, table_name: str
) -> None:
    try:
        delete_statement = delete(table).where(clause)
        result = connection.execute(delete_statement)
        logger.info("Deleted %s rows from table %s.", result.rowcount, table_name)
    except SQLAlchemyError as e:
        msg = f"Error during deletion from table {table_name}: {e}"
        logger.error(msg)
        raise AdapterHandlingException(msg) from e


def _handle_deletion(  # noqa: PLR0915, PLR0912
    connection: Connection,
    metadata: DatasetMetadata,
    df: pd.DataFrame,
    metrics: list[str],
    ts_table_config: TimeseriesTableConfig,
    table_name: str,
) -> None:
    """Perform deletion in the database, based on metadata configuration.

    Deletion is performed based on the following order of precedence:
    - Invalidation dataset
    - Discrete reference dataset
    - Reference dataset based on interval
    - Interval-based dataset inferred from data
    """
    if metadata.invalidate_dataset is False or metadata.delete_invalidated is False:
        logger.debug("Skipping deletion: invalidate_dataset or delete_invalidated is not true.")
        return

    if not metrics:
        logger.warning("Cannot perform deletion: No metrics specified.")
        return

    metadata_obj = MetaData()
    table_obj = Table(table_name, metadata_obj, autoload_with=connection)
    timestamp_col = getattr(table_obj.c, ts_table_config.timestamp_col_name)
    metric_col = getattr(table_obj.c, ts_table_config.metric_col_name)

    metrics_to_use: list[str] | list[int]

    if ts_table_config.metric_type == "str":
        metrics_to_use = metrics
    else:
        try:
            metrics_to_use = [int(metric) for metric in metrics]
        except (ValueError, TypeError) as e:
            msg = "Error converting metrics to integers while deleting data."
            logger.info(msg)
            raise AdapterHandlingException(msg) from e

    where_clause = None

    # Invalidation interval is set
    if (
        metadata.invalidation_interval_start is not None
        and metadata.invalidation_interval_end is not None
        and metadata.invalidation_interval_type is not None
    ):
        logger.info("Deletion based on invalidation dataset.")
        start_op, end_op = INTERVAL_OPERATORS[metadata.invalidation_interval_type]
        where_clause = and_(
            start_op(timestamp_col, metadata.invalidation_interval_start),
            end_op(timestamp_col, metadata.invalidation_interval_end),
            metric_col.in_(metrics_to_use),
        )

    # Ref dataset is discrete
    elif metadata.ref_dataset_discrete:
        if df.empty:
            logger.warning("Skipping discrete deletion: DataFrame is empty.")
            return
        logger.info("Deletion based on discrete timestamps from the reference dataset.")

        filtered_df = df[df["metric"].isin(metrics)]

        if filtered_df.empty:
            logger.info("No data points for discrete deletion for the given metrics.")
            return

        if ts_table_config.metric_type == "str":
            metric_data = filtered_df["metric"]
        else:
            try:
                metric_data = filtered_df["metric"].astype(int)
            except (ValueError, TypeError) as e:
                msg = "Error converting metrics to integers while deleting discrete data."
                logger.info(msg)
                raise AdapterHandlingException(msg) from e

        data_points_to_delete = list(
            zip(
                filtered_df["timestamp"],
                metric_data,
                strict=True,
            )
        )

        where_clause = tuple_(timestamp_col, metric_col).in_(data_points_to_delete)

    # Ref interval is set
    elif (
        metadata.ref_interval_start_timestamp is not None
        and metadata.ref_interval_end_timestamp is not None
        and metadata.ref_interval_type is not None
    ):
        logger.info("Deletion based on reference dataset.")
        start_op, end_op = INTERVAL_OPERATORS[metadata.ref_interval_type]
        where_clause = and_(
            start_op(timestamp_col, metadata.ref_interval_start_timestamp),
            end_op(timestamp_col, metadata.ref_interval_end_timestamp),
            metric_col.in_(metrics_to_use),
        )

    # Infer interval from data
    elif not df.empty:
        min_ts = df["timestamp"].min()
        max_ts = df["timestamp"].max()
        logger.info("Deletion based on inferred interval from data: %s to %s", min_ts, max_ts)
        start_op, end_op = INTERVAL_OPERATORS[IntervalType.CLOSED]
        where_clause = and_(
            start_op(timestamp_col, min_ts),
            end_op(timestamp_col, max_ts),
            metric_col.in_(metrics_to_use),
        )

    # No criteria met
    else:
        logger.info("No deletion criteria met. No data will be deleted.")
        return

    if where_clause is not None:
        _execute_delete(connection, where_clause, table_obj, table_name)


def _retrieve_metrics(data: pd.DataFrame) -> list[str]:
    if metrics := list(data.attrs.get("by_metric", {}).keys()):
        return metrics
    # Legacy code might use the old convention of ref_metrics
    if metrics := data.attrs.get("ref_metrics", []):
        return metrics  # type: ignore[no-any-return]
    # Fallback to building metrics from data
    if get_sql_adapter_config().infer_metrics_from_metric_column_for_deletion_if_not_present:
        return [str(metric) for metric in data["metric"].unique().tolist()]
    return []


def validate_sink_is_allowed(write_table: WriteTable, sink_id: str) -> None:
    """Ensure the requested sink is configured as a writable target.

    The set of writable tables is restricted by configuration (append_tables,
    replace_tables and appendable timeseries tables). Parsing a sink id only checks
    that the db key is configured, so this check must be enforced here at write time
    and not only when listing the offered sinks. Otherwise a crafted sink id could be
    used to append to or replace an arbitrary table reachable by the connection user.
    """
    db_config = write_table.db_config
    table_name = write_table.table_name
    write_mode = write_table.write_mode

    if write_mode is WriteTableMode.APPEND:
        allowed = table_name in db_config.append_tables
    elif write_mode is WriteTableMode.REPLACE:
        allowed = table_name in db_config.replace_tables
    elif write_mode is WriteTableMode.TIMSERIES_APPEND:
        ts_table_config = db_config.timeseries_tables.get(table_name)
        allowed = ts_table_config is not None and ts_table_config.appendable
    else:  # pragma: no cover
        allowed = False

    if not allowed:
        msg = (
            f"Writing to sink id {sink_id} is not allowed: table {table_name!r} is not"
            f" configured as a writable {write_mode.value} sink for db key"
            f" {write_table.db_key!r}."
        )
        logger.error(msg)
        raise AdapterHandlingException(msg)


def write_table_to_provided_sink_id(data: pd.DataFrame, sink_id: str) -> None:
    try:
        write_table = WriteTable.from_sink_id(sink_id)
    except ValidationError as e:  # pragma: no cover
        msg = f"Could not parse and validate sink id {sink_id}. Error was {str(e)}."
        logger.info(msg)  # noqa: G003
        raise AdapterHandlingException(msg) from e

    validate_sink_is_allowed(write_table, sink_id)

    data_to_send = data.copy()  # deep copy by default!

    configured_dbs_by_key = get_configured_dbs_by_key()
    db_config = configured_dbs_by_key[write_table.db_key]
    ts_table_config: TimeseriesTableConfig | None = None

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

    try:
        metadata = get_dataset_metadata_from_attrs(data)
        metrics = _retrieve_metrics(data)
    except (ValidationError, TypeError, AttributeError, KeyError) as e:
        raise AdapterHandlingException(f"Error processing metadata for sink {sink_id}: {e}") from e

    engine = db_config.engine
    try:
        with engine.begin() as connection:  # Transactional / roll back in case of exceptions
            if (
                ts_table_config is not None
                and ts_table_config.allow_invalidation
                and ts_table_config.delete_invalidated
            ):
                _handle_deletion(
                    connection,
                    metadata,
                    data,
                    metrics,
                    ts_table_config,
                    write_table.table_name,
                )
            elif metadata.invalidate_dataset and not metadata.delete_invalidated is False:
                logger.warning(
                    "According to dataset_metadata deletion should happen, "
                    "but according to the table configuration, deletion is not allowed. "
                    "Hence, no deletion took place."
                )

            if metadata.only_invalidate:
                logger.info(
                    "Execution for sink %s finished. "
                    "only_invalidate=true, so no new data was written.",
                    sink_id,
                )
                return

            if data_to_send.empty:
                logger.info("Dataframe for sink %s is empty. Nothing to write.", sink_id)
                return

            data_to_send.to_sql(
                write_table.table_name,
                connection,
                if_exists=write_table.pandas_if_exists_mode,
                index=False,
                method="multi",
            )
    except SQLOpsError as e:
        msg = f"Sql adapter pandas to_sql writing error for sink {sink_id}: {str(e)}"
        logger.info(msg)
        raise AdapterHandlingException(msg) from e

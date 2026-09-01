import datetime
import logging
from typing import Literal

import pandas as pd
from dtexp import DtexpParsingError
from pydantic import RootModel, ValidationError
from sqlalchemy.exc import OperationalError as SQLOpsError
from sqlalchemy.sql import and_, column, select, table
from sqlalchemy.sql.selectable import Select

from hetdesrun.adapters.exceptions import AdapterHandlingException
from hetdesrun.adapters.sql_adapter.config import (
    SQLAdapterDBConfig,
    TimeseriesTableConfig,
)
from hetdesrun.adapters.sql_adapter.utils import (
    get_configured_dbs_by_key,
    is_allowed_dataframe_source_table,
    validate_multits_frame,
)
from hetdesrun.dt_utils import resolve_interval

logger = logging.getLogger(__name__)


MetricList = RootModel[list[str]]  # list of timeseries metrics


def split_metric_ids(metric_ids_string: str | None) -> list[str]:
    if metric_ids_string is None:
        return []
    try:
        return MetricList.model_validate_json(metric_ids_string).root
    except ValidationError:
        # handle as comma separated string
        return [x.strip() for x in metric_ids_string.split(",") if x != ""]


def extract_time_range(
    source_filters: dict[str, str],
) -> tuple[datetime.datetime, datetime.datetime]:
    from_timestamp = source_filters.get("timestampFrom")
    to_timestamp = source_filters.get("timestampTo")

    try:
        from_datetime, to_datetime = resolve_interval(from_timestamp, to_timestamp)
    except (ValueError, DtexpParsingError) as e:
        raise AdapterHandlingException(
            "Could not resolve timestamp filters for multitsframe timeseries source."
        ) from e

    return from_datetime, to_datetime


def prepare_sql_statement(
    ts_table_name: str,
    ts_table_config: TimeseriesTableConfig,
    from_datetime: datetime.datetime,
    to_datetime: datetime.datetime,
    metrics_list: list[str] | None,
    metric_type: Literal["str", "int"] = "str",
) -> Select:
    """Prepare the statement for fetching metrics

    If metrics_list is None all metrics will be fetched.
    """

    # ad hoc table object without data type specifications since
    # corresponding to the fact that we want to employ pandas read_sql automatic
    # flexible dtype inference.

    ts_table = table(
        ts_table_name,
        column(
            ts_table_config.timestamp_col_name,
        ),
        column(ts_table_config.metric_col_name),
        *(column(val_col_name) for val_col_name in ts_table_config.fetchable_value_cols),
    )

    metrics_to_use: list[str] | list[int]
    if metrics_list is not None:
        if metric_type == "str":
            metrics_to_use = metrics_list
        else:
            try:
                metrics_to_use = [int(metric) for metric in metrics_list]
            except (ValueError, TypeError) as e:
                msg = "Error converting metrics to integers for loading data."
                logger.info(msg)
                raise AdapterHandlingException(msg) from e

    clauses = (
        ts_table.c[ts_table_config.timestamp_col_name] >= from_datetime,
        ts_table.c[ts_table_config.timestamp_col_name] <= to_datetime,
    ) + (
        ()
        if metrics_list is None
        else (ts_table.c[ts_table_config.metric_col_name].in_(metrics_to_use),)
    )

    # ad hoc sqlalchemy expression construction
    statement = select(ts_table).where(and_(*clauses))

    return statement


def prepare_validate_loaded_raw_multitsframe(
    multits_frame: pd.DataFrame,
    ts_table_config: TimeseriesTableConfig,
    source_id: str,
    metrics_list: list[str] | None,
    from_datetime: datetime.datetime,
    to_datetime: datetime.datetime,
) -> pd.DataFrame:
    """Prepares and validates a multitsframe.

    Preparation is done by enforcing UTC and correct column naming.
    For validation, the corresponding function is called.

    Args:
        metrics_list (list[str] | None):
            Is only None if 'ALL' was provided in the metrics filter when calling the adapter.

    Returns:
        pd.DataFrame: A validated multitsframe
    """

    # Guarantee that we have utc timezoned timetsamp column (naive timestamps from db
    # will be assumed to be UTC, non-naive will be transformed into explicit UTC):
    multits_frame[ts_table_config.timestamp_col_name] = pd.to_datetime(
        multits_frame[ts_table_config.timestamp_col_name], utc=True
    )

    multits_frame[ts_table_config.metric_col_name] = multits_frame[
        ts_table_config.metric_col_name
    ].astype(str)

    # Column mapping
    multits_frame.rename(
        columns=ts_table_config.column_mapping_db_to_hd,
        inplace=True,  # noqa:PD002
    )

    # multi ts frame validation
    try:
        validated_multi_ts_frame = validate_multits_frame(multits_frame)
    except ValidationError as e:  # pragma: no cover
        msg = (
            "Could not validate multi ts frame received via sql adapter"
            f" from source id {source_id}. Error was: \n{str(e)}"
        )
        raise AdapterHandlingException(msg) from e

    # setting meta data (attrs)
    validated_multi_ts_frame.attrs = {
        "dataset_metadata": {
            "ref_interval_start_timestamp": from_datetime.isoformat(),
            "ref_interval_end_timestamp": to_datetime.isoformat(),
            "ref_interval_type": "closed",
        },
    }
    if metrics_list is not None:
        validated_multi_ts_frame.attrs.update(
            {"by_metric": {metric: {} for metric in metrics_list}}
        )

    return validated_multi_ts_frame


def load_table_from_provided_source_id(source_id: str, source_filters: dict) -> pd.DataFrame:
    configured_dbs_by_key = get_configured_dbs_by_key()

    id_split = source_id.split("/", 2)
    db_key = id_split[0]

    if db_key not in configured_dbs_by_key or len(id_split) < 2:
        msg = f"Invalid source id requested from sql adapter: {source_id}"
        logger.info(msg)
        raise AdapterHandlingException(msg)

    db_config = configured_dbs_by_key[db_key]

    if id_split[1] == "query" and len(id_split) == 2:
        if not db_config.allow_arbitrary_sql_query_sources:
            msg = (
                f"Arbitrary SQL query source {source_id} is not allowed: arbitrary SQL"
                f" queries are disabled for db key {db_key!r}. Set"
                " allow_arbitrary_sql_query_sources to True for this database to enable them."
            )
            logger.info(msg)
            raise AdapterHandlingException(msg)
        query = source_filters.get("sql_query")
        if query is None:  # pragma: no cover
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
        if not is_allowed_dataframe_source_table(table_name, db_config):
            msg = (
                f"Reading table {table_name!r} via source id {source_id} is not allowed:"
                f" it is not an accessible dataframe table source for db key {db_key!r}."
            )
            logger.info(msg)
            raise AdapterHandlingException(msg)
        return load_sql_table(db_config, table_name)

    if id_split[1] == "ts_table" and len(id_split) > 2:
        ts_table_name = id_split[2]

        if ts_table_name not in db_config.timeseries_tables:
            msg = (
                f"Reading timeseries table {ts_table_name!r} via source id {source_id} is not"
                f" allowed: it is not a configured timeseries table for db key {db_key!r}."
            )
            logger.info(msg)
            raise AdapterHandlingException(msg)

        metric_ids_string = source_filters.get("metrics", "")

        if metric_ids_string.upper() == "ALL":
            metrics_list = None
        else:
            metrics_list = split_metric_ids(metric_ids_string)

        logger.debug(
            "Parsed metric list %s from metrics filter %s",
            str(metrics_list),
            metric_ids_string,
        )

        from_datetime, to_datetime = extract_time_range(source_filters)

        ts_table_config = db_config.timeseries_tables[ts_table_name]

        statement = prepare_sql_statement(
            ts_table_name,
            ts_table_config,
            from_datetime,
            to_datetime,
            metrics_list,
            metric_type=ts_table_config.metric_type,
        )

        multits_frame = load_sql_query(db_config, statement)

        validated_multi_ts_frame = prepare_validate_loaded_raw_multitsframe(
            multits_frame,
            ts_table_config,
            source_id,
            metrics_list,
            from_datetime,
            to_datetime,
        )

        return validated_multi_ts_frame

    msg = f"Invalid source id structure. Cannot find or identify source.source id: {source_id}"
    logger.info(msg)
    raise AdapterHandlingException(msg)


def load_sql_table(db_config: SQLAdapterDBConfig, table_name: str) -> pd.DataFrame:
    engine = db_config.engine
    try:
        with engine.begin():
            result = pd.read_sql_table(table_name, engine)
    except SQLOpsError as e:
        msg = f"Sql adapter pandas sql reading error: {str(e)}"
        logger.info(msg)
        raise AdapterHandlingException(msg) from e
    return result


def load_sql_query(db_config: SQLAdapterDBConfig, query: Select) -> pd.DataFrame:
    engine = db_config.engine
    try:
        with engine.begin():
            result = pd.read_sql_query(query, engine)
    except SQLOpsError as e:
        msg = f"Sql adapter pandas sql query error: {str(e)}"
        logger.info(msg)
        raise AdapterHandlingException(msg) from e
    return result

import datetime
import logging

import pandas as pd
from pydantic import BaseModel, ValidationError
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
    validate_multits_frame,
)

logger = logging.getLogger(__name__)


class MetricList(BaseModel):
    """List of timeseries metrics"""

    __root__: list[str]


def split_metric_ids(metric_ids_string: str | None) -> list[str]:
    if metric_ids_string is None:
        return []
    try:
        return MetricList.parse_raw(metric_ids_string).__root__
    except ValidationError:
        # handle as comma separated string
        return [x.strip() for x in metric_ids_string.split(",") if x != ""]


def extract_time_range(
    source_filters: dict[str, str],
) -> tuple[datetime.datetime, datetime.datetime]:
    from_timestamp = source_filters.get("timestampFrom")
    to_timestamp = source_filters.get("timestampTo")

    if from_timestamp is None or to_timestamp is None:
        msg = "Missing timestamp filters for multitsframe timeseries source"
        logger.error(msg)
        raise AdapterHandlingException(msg)

    try:
        from_datetime = pd.to_datetime(from_timestamp, utc=True).to_pydatetime()
        to_datetime = pd.to_datetime(to_timestamp, utc=True).to_pydatetime()
    except ValueError as e:  # pragma: no cover
        msg = (
            "Could not parse one of multitsframe timestamp filters: "
            f"(timestampFrom: {from_timestamp}), "
            f"(timestampTo: {to_timestamp})."
        )
        raise AdapterHandlingException(msg) from e

    return from_datetime, to_datetime


def prepare_sql_statement(
    ts_table_name: str,
    ts_table_config: TimeseriesTableConfig,
    from_datetime: datetime.datetime,
    to_datetime: datetime.datetime,
    metrics_list: list[str] | None,
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

    clauses = (
        ts_table.c[ts_table_config.timestamp_col_name] >= from_datetime,
        ts_table.c[ts_table_config.timestamp_col_name] <= to_datetime,
    ) + (
        ()
        if metrics_list is None
        else (ts_table.c[ts_table_config.metric_col_name].in_(metrics_list),)
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
        "ref_interval_start_timestamp": from_datetime.isoformat(),
        "ref_interval_end_timestamp": to_datetime.isoformat(),
        "ref_interval_type": "closed",
        "ref_metrics": metrics_list,
    }

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
        return load_sql_table(db_config, table_name)

    if id_split[1] == "ts_table" and len(id_split) > 2:
        ts_table_name = id_split[2]

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
            ts_table_name, ts_table_config, from_datetime, to_datetime, metrics_list
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

    msg = "Invalid source id structure. Cannot find or identify source." f"source id: {source_id}"
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

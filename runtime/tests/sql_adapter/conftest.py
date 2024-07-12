import os
from unittest import mock

import pandas as pd
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine

from hetdesrun.adapters.sql_adapter.config import (
    SQLAdapterDBConfig,
    TimeseriesTableConfig,
)
from hetdesrun.adapters.sql_adapter.utils import get_configured_dbs_by_key
from hetdesrun.webservice.application import init_app


@pytest.fixture(scope="function")  # noqa: PT003
def temporary_sqlite_file_path(tmpdir):
    return os.path.join(tmpdir, "temporary_sqlite.db")


@pytest.fixture(scope="function")  # noqa: PT003
def temporary_sqlite_file_path_ts_db(tmpdir):
    return os.path.join(tmpdir, "temporary_sqlite_ts_db.db")


@pytest.fixture(scope="function")  # noqa: PT003
def temporary_prefilled_sqlite_ts_db(temporary_sqlite_file_path_ts_db):
    ts_df = pd.DataFrame(
        {
            "value": [1.2, 1.3, 2, 2.2],
            "timestamp": pd.to_datetime(
                [
                    "2023-08-29T11:58:02+00:00",
                    "2023-08-29T12:27:31+00:00",
                    "2023-08-29T13:07:46+00:00",
                    "2023-08-29T13:07:46+00:00",
                ]
            ),
            "metric": ["a", "b", "a", "c"],
        }
    )
    engine = create_engine("sqlite+pysqlite:///" + temporary_sqlite_file_path_ts_db, echo=True)

    ts_df.to_sql(
        "ro_ts_table",  # ts table name
        engine,
        if_exists="replace",  # versus "append"
        index=False,
    )

    ts_df.to_sql(
        "ts_table",  # ts table name
        engine,
        if_exists="replace",  # versus "append"
        index=False,
    )

    # some more tables!
    ts_df.to_sql(
        "table1",
        engine,
        if_exists="replace",
        index=False,
    )

    ts_df.to_sql(
        "table2",
        engine,
        if_exists="replace",
        index=False,
    )

    ts_df.rename(
        columns={"metric": "tsid", "timestamp": "datetime", "value": "measurement_val"}
    ).to_sql(
        "table3",
        engine,
        if_exists="replace",
        index=False,
    )

    return temporary_sqlite_file_path_ts_db


@pytest.fixture(scope="function")  # noqa: PT003
def _clean_configured_dbs_by_key():
    get_configured_dbs_by_key.cache_clear()


@pytest.fixture(scope="function")  # noqa: PT003
def two_sqlite_dbs_configured(temporary_sqlite_file_path, _clean_configured_dbs_by_key):
    with mock.patch(
        "hetdesrun.adapters.sql_adapter.config.sql_adapter_config.sql_databases",
        new=[
            SQLAdapterDBConfig(
                connection_url="sqlite+pysqlite:///./tests/data/sql_adapter/example_sqlite.db",
                name="sqlite test example db",
                key="test_example_sqlite_read_db",
            ),
            SQLAdapterDBConfig(
                connection_url="sqlite+pysqlite:///" + temporary_sqlite_file_path,
                name="writable temporary sqlite db",
                key="test_writable_temp_sqlite_db",
                append_tables=["append_alert_table", "model_run_stats"],
                replace_tables=["model_config_params"],
            ),
        ],
    ) as _fixture:
        yield _fixture


@pytest.fixture(scope="function")  # noqa: PT003
def three_sqlite_dbs_configured(
    temporary_sqlite_file_path,
    temporary_prefilled_sqlite_ts_db,
    _clean_configured_dbs_by_key,
):
    with mock.patch(
        "hetdesrun.adapters.sql_adapter.config.sql_adapter_config.sql_databases",
        new=[
            SQLAdapterDBConfig(
                connection_url="sqlite+pysqlite:///./tests/data/sql_adapter/example_sqlite.db",
                name="sqlite test example db",
                key="test_example_sqlite_read_db",
            ),
            SQLAdapterDBConfig(
                connection_url="sqlite+pysqlite:///" + temporary_sqlite_file_path,
                name="writable temporary sqlite db",
                key="test_writable_temp_sqlite_db",
                append_tables=["append_alert_table", "model_run_stats"],
                replace_tables=["model_config_params"],
            ),
            SQLAdapterDBConfig(
                connection_url="sqlite+pysqlite:///" + temporary_prefilled_sqlite_ts_db,
                name="read_only_timeseries sqlite database",
                key="read_only_timeseries_sqlite_database",
                explicit_source_tables={"table1", "table2"},
                ignore_tables={"table1"},
                timeseries_tables={
                    "ro_ts_table": TimeseriesTableConfig(appendable=False),
                    "ts_table": TimeseriesTableConfig(appendable=True),
                    "table3": TimeseriesTableConfig(
                        appendable=True,
                        metric_col_name="tsid",
                        timestamp_col_name="datetime",
                        fetchable_value_cols=["measurement_val"],
                        writable_value_cols=["measurement_val"],
                        column_mapping_hd_to_db={
                            "metric": "tsid",
                            "timestamp": "datetime",
                            "value": "measurement_val",
                        },
                    ),
                },
            ),
        ],
    ) as _fixture:
        yield _fixture


@pytest.fixture(scope="session")
def app_without_auth() -> FastAPI:
    with mock.patch("hetdesrun.webservice.config.runtime_config.auth", False):
        return init_app()


@pytest.fixture
def async_test_client_with_sql_adapter(
    two_sqlite_dbs_configured,
    app_without_auth: FastAPI,
) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app_without_auth), base_url="http://test")

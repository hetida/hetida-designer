import pytest

import os
import tempfile

from unittest import mock
from hetdesrun.adapters.sql_adapter.config import SQLAdapterDBConfig


@pytest.fixture(scope="function")
def temporary_sqlite_file_path():
    with tempfile.TemporaryDirectory() as tmp_dir_name:
        yield os.path.join(tmp_dir_name, "temporary_sqlite.db")


@pytest.fixture(scope="function")
def two_sqlite_dbs_configured(temporary_sqlite_file_path):
    with mock.patch(
        "hetdesrun.adapters.sql_adapter.config.sql_adapter_config.sql_databases",
        new=[
            SQLAdapterDBConfig(
                connection_url="sqlite+pysqlite:///./tests/data/sql_adapter/example_sqlite.db?mode=ro",
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

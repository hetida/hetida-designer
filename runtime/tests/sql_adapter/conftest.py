import os
import tempfile
from unittest import mock

import pytest

from hetdesrun.adapters.sql_adapter.config import SQLAdapterDBConfig
from hetdesrun.adapters.sql_adapter.utils import get_configured_dbs_by_key


@pytest.fixture(scope="function")  # noqa: PT003
def temporary_sqlite_file_path(tmpdir):
    return os.path.join(tmpdir, "temporary_sqlite.db")


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

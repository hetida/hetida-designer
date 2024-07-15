import os
from functools import cached_property
from typing import Any

from pydantic import BaseModel, BaseSettings, Field, validator
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from hetdesrun.models.util import valid_python_identifier


class TimeseriesTableConfig(BaseModel):
    appendable: bool = Field(
        True,
        description="Whether writing into this table is offered as sink."
        " Note that this is setting does not provide write protection. This has to be ensured "
        "on the database via its security / access management features if necessary.",
    )
    metric_col_name: str = "metric"
    timestamp_col_name: str = "timestamp"
    fetchable_value_cols: list[str] = ["value"]
    writable_value_cols: list[str] = ["value"]
    column_mapping_hd_to_db: dict[str, str] = Field(
        {},
        description=(
            " Mapping that will be applied to dataframe columns to match db columns"
            " when writing."
            " Must be invertible, the inverse mapping will be applied when loading data"
            " from the db."
            " A mapping is required at least for timestamp or metric column if their name"
            " differs from the default, since on the hd side they are required to be"
            ' "timestamp" and "mertic".'
            " Note that mapped columns must not be present when the mapping is applied."
            " It is for example possible to write a column, mapped to another name in the db"
            " but not fetching it (and therefore not apply the inverse mapping) by excluding"
            " it from fetachable_value_cols."
        ),
    )

    @validator("column_mapping_hd_to_db")
    def column_mapping_invertible(cls, v: dict[str, str]) -> dict[str, str]:
        if len(v.values()) != len(set(v.values())):
            raise ValueError(f"Column mapping must be invertible. Got {v}.")
        return v

    @cached_property
    def column_mapping_db_to_hd(self) -> dict[str, str]:
        """inverse mapping"""
        return {v: k for k, v in self.column_mapping_hd_to_db.items()}

    class Config:
        arbitrary_types_allowed = True
        keep_untouched = (cached_property,)


class SQLAdapterDBConfig(BaseModel):
    """A config of a database for the sql adapter

    All tables will be made available as sources by default and additionally an arbitrary
    query source is offered. It is up to the database admin to restrict access for the
    user configured in the connection url.

    Only the tables configured in append_tables and replace_tables will be offered as
    fixed sinks.
    * They will be created if not present
    * append tables will be appendet to when writing data to them
    * replace tables will be completely replaced with the data when writing to them

    """

    connection_url: str = Field(..., description="a valid and complete sql connection uri")
    name: str
    key: str
    append_tables: list[str] = Field(
        [], description="names of tables that are offered as sinks for appending data"
    )
    replace_tables: list[str] = Field(
        [],
        description="names of tables that are offered as sinks for replacing the whole table",
    )
    ignore_tables: set[str] = Field(
        set(), description="tables that should not be made accessable as sources"
    )
    timeseries_tables: dict[str, TimeseriesTableConfig] = Field(
        {},
        description="Mapping of table names to TimeseriesTableConfig objects."
        " Timeseries tables are offered as timeseries sources. They are not "
        " available as ordinary table sources of type DATAFRAME.",
    )
    explicit_source_tables: None | set[str] = Field(
        None,
        description=(
            "If None, all tables (minus ignore tables) will be available as sources for reading."
            " If set to a list of table names only these tables (minus ignore tables) will be"
            " made available as sources."
        ),
    )

    create_engine_kwargs: dict[str, Any] = Field(
        {},
        description=(
            "Additional keyword arguments to create_engine."
            " E.g. you can set the connection pool size via pool_size."
            " See sqlalchemy documentation for more options."
        ),
    )

    @cached_property
    def engine(self) -> Engine:
        return create_engine(self.connection_url, **self.create_engine_kwargs)  # type: ignore

    class Config:
        arbitrary_types_allowed = True
        keep_untouched = (cached_property,)


class SQLAdapterConfig(BaseSettings):
    """Configuration for sql adapter"""

    active: bool = Field(
        True,
        description="Whether generic SQL adapter is started",
        env="SQL_ADAPTER_ACTIVE",
    )

    service_in_runtime: bool = Field(
        True,
        description=(
            "Whether the API part serving the hd frontend is started as part"
            " of the runtime API service as opposed to as part of the backend API."
        ),
        env="SQL_ADAPTER_SERVICE_IN_RUNTIME",
    )

    sql_databases: list[SQLAdapterDBConfig] = Field([], env="SQL_ADAPTER_SQL_DATABASES")

    @validator("sql_databases")
    def unique_db_keys(cls, v: list[SQLAdapterDBConfig]) -> list[SQLAdapterDBConfig]:
        if len({configured_db.key for configured_db in v}) != len(v):
            raise ValueError("Configured db keys not unique")
        return v

    @validator("sql_databases")
    def db_keys_valid_python_identifiers(
        cls, v: list[SQLAdapterDBConfig]
    ) -> list[SQLAdapterDBConfig]:
        if not all(valid_python_identifier(cls, configured_db.key) for configured_db in v):
            raise ValueError(
                "Some configured db key of the generic sql adapter contains invalid characters."
            )
        return v


environment_file = os.environ.get("HD_GENERIC_SQL_ADAPTER_ENVIRONMENT_FILE", None)

sql_adapter_config = SQLAdapterConfig(
    _env_file=environment_file if environment_file else None  # type: ignore[call-arg]
)


def get_sql_adapter_config() -> SQLAdapterConfig:
    return sql_adapter_config

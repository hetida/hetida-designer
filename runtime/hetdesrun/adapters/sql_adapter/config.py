import os

from pydantic import BaseModel, BaseSettings, Field, validator

from hetdesrun.models.util import valid_python_identifier


class SQLAdapterDBConfig(BaseModel):
    """A config of a database for the sql adapter

    All tables will be made available as sources and additionally an arbitrary query
    source is offered. It is up to the database admin to restrict access for the user
    configured in the connection url.

    Only the tables configured in append_tables and replace_tables will be offered as
    fixed sinks.
    * They will be created if not present
    * append tables will be appendet to when writing data to them
    * replace tables will be completely replaced with the data when writing to them

    """

    connection_url: str = Field(
        ..., description="a valid and complete sql connection uri"
    )
    name: str
    key: str
    append_tables: list[str] = Field(
        [], description="names of tables that are offered as sinks for appending data"
    )
    replace_tables: list[str] = Field(
        [],
        description="names of tables that are offered as sinks for replacing the whole table",
    )


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
        if not all(
            valid_python_identifier(cls, configured_db.key) for configured_db in v
        ):
            raise ValueError(
                "Some configured db key of the generic sql adapter contains invalid characters."
            )
        return v


environment_file = os.environ.get("HD_GENERIC_SQL_ADAPTER_ENVIRONMENT_FILE", None)

sql_adapter_config = SQLAdapterConfig(
    _env_file=environment_file if environment_file else None
)


def get_sql_adapter_config() -> SQLAdapterConfig:
    return sql_adapter_config

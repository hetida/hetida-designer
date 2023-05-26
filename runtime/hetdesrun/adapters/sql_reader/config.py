import os

from pydantic import BaseModel, BaseSettings, Field, validator


class SQLReaderDBConfig(BaseModel):
    connection_url: str
    name: str
    key: str


class SQLReaderAdapterConfig(BaseSettings):
    """Configuration for sql reader adapter"""

    sql_databases: list[SQLReaderDBConfig] = Field(
        [], env="RUNTIME_SQL_READER_ADAPTER_SQL_DATABASES"
    )

    allowed_origins: str = Field(
        (
            "http://localhost:4200,http://localhost:80,localhost"
            ",http://localhost,hetida-designer-runtime"
        ),
        description="Comma separated allowed origins (CORS)",
        env="RUNTIME_LOCAL_FILE_ADAPTER_ALLOWED_ORIGINS",
        example="http://exampledomain.com,http://anotherexampledomain.de",
    )

    @validator("sql_databases")
    def unique_db_keys(cls, v: list[SQLReaderDBConfig]) -> list[SQLReaderDBConfig]:
        if len({configured_db.key for configured_db in v}) != len(v):
            return ValueError("Configured db keys not unique")
        return v


environment_file = os.environ.get("HD_RUNTIME_ENVIRONMENT_FILE", None)

sql_reader_adapter_config = SQLReaderAdapterConfig(
    _env_file=environment_file if environment_file else None
)

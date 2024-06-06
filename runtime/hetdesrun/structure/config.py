import os
import re
from enum import Enum

from pydantic import BaseSettings, Field, SecretStr, validator
from sqlalchemy.engine import URL as DB_URL

maintenance_secret_pattern = re.compile("[a-zA-Z0-9]+")


class LogLevel(str, Enum):
    # https://docs.python.org/3/library/logging.html#logging-levels
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"
    NOTSET = "NOTSET"


class ThingNodeDynPropConfig(BaseSettings):
    log_level: LogLevel = Field(
        LogLevel.INFO,
        description="Python logging level as string, i.e. one of "
        + ", ".join(['"' + x.value + '"' for x in list(LogLevel)]),
    )

    db_host: str = "hetida-designer-db"

    db_port: int = 5432

    db_database: str = "hetida_designer_db"

    db_drivername: str = "postgresql+psycopg2"

    db_user: str = "hetida_designer_dbuser"

    db_password: SecretStr = Field(SecretStr("hetida_designer_dbpasswd"))

    db_url: SecretStr | DB_URL | None = Field(
        None,
        description=(
            "Rfc 1738 database url. Not set by default."
            " If set, takes precedence over db_* attributes!"
            " Otherwise will be constructed from the db_* attributes"
        ),
        examples=[
            "postgresql+psycopg2://hetida_designer_dbuser:"
            "hetida_designer_dbpasswd@hetida-designer-db:5432/hetida_designer_db"
        ],
    )

    db_pool_size: int = Field(100, gt=0, env="DB_POOL_SIZE")

    @validator("db_url")
    @classmethod
    def database_url(
        cls, db_url: SecretStr | DB_URL, values: dict
    ) -> SecretStr | DB_URL:
        if db_url is None:
            pw_secret = values["db_password"]
            return DB_URL.create(
                drivername=values["db_drivername"],
                username=values["db_user"],
                password=(
                    pw_secret.get_secret_value()
                    if isinstance(pw_secret, SecretStr)
                    else pw_secret
                ),
                host=values["db_host"],
                port=values["db_port"],
                database=values["db_database"],
            )
        return db_url


environment_file = os.environ.get("TNDP_ENVIRONMENT_FILE", None)

tndp_config = ThingNodeDynPropConfig(
    _env_file=environment_file if environment_file else None  # type: ignore[call-arg]
)


def get_config() -> ThingNodeDynPropConfig:
    return tndp_config

import os
import re
from enum import Enum

from pydantic import BaseSettings, Field

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


environment_file = os.environ.get("TNDP_ENVIRONMENT_FILE", None)

tndp_config = ThingNodeDynPropConfig(
    _env_file=environment_file if environment_file else None  # type: ignore[call-arg]
)


def get_config() -> ThingNodeDynPropConfig:
    return tndp_config

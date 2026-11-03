import os
from enum import Enum

from pydantic import Field
from pydantic_settings import BaseSettings


class LogLevel(str, Enum):
    # https://docs.python.org/3/library/logging.html#logging-levels
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"
    NOTSET = "NOTSET"


class PythonDemoAdapterConfig(BaseSettings):
    log_level: LogLevel = Field(
        LogLevel.INFO,
        alias="LOG_LEVEL",
        description="Python logging level as string, i.e. one of "
        + ", ".join(['"' + x.value + '"' for x in list(LogLevel)]),
    )
    swagger_prefix: str = Field(
        "",
        alias="OPENAPI_PREFIX",
        description="root path (necessary for OpenAPI UI if behind proxy)",
    )
    allowed_origins: str = Field(
        (
            "http://localhost:4200,http://localhost:80,localhost"
            ",http://localhost,hetida-designer-demo-adapter-python"
        ),
        description="Comma separated allowed origins (CORS)",
        alias="ALLOWED_ORIGINS",
        examples=["http://exampledomain.com,http://anotherexampledomain.de"],
    )
    compress_metadata: bool = Field(
        True,
        description=(
            "Whether the Data-Attributes header (metadata) of GET responses is sent"
            " gzip-compressed, if the request announces via the header"
            ' "Data-Attributes-Accept-Encoding: gzip" that the hetida designer runtime'
            " understands it"
        ),
        alias="COMPRESS_METADATA",
    )


environment_file = os.environ.get("HD_DEMO_ADAPTER_PYTHON_ENVIRONMENT_FILE", None)

demo_adapter_config = PythonDemoAdapterConfig(  # type: ignore[call-arg]
    _env_file=environment_file if environment_file else None
)

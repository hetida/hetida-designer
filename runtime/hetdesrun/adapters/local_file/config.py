import os

from pydantic import BaseSettings, Field


class LocalFileAdapterConfig(BaseSettings):
    """Configuration for local file adapter"""

    local_dirs: set[str] = Field(
        {"tests/data/local_files"},
        description=(
            "Root directory paths provided as JSON-List of Strings."
            " These pathes will be made available by the local file adapter."
            " Typically these are volume mounts in the runtime container."
        ),
        env="RUNTIME_LOCAL_FILE_ADAPTER_LOCAL_DIRECTORIES",
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
    generic_any_sink: bool = Field(
        True,
        description="Whether a generic sink of type any is offered in each directory",
        env="RUNTIME_LOCAL_FILE_ADAPTER_GENERIC_ANY_SINKS",
    )


environment_file = os.environ.get("HD_RUNTIME_ENVIRONMENT_FILE", None)

local_file_adapter_config = LocalFileAdapterConfig(
    _env_file=environment_file if environment_file else None
)

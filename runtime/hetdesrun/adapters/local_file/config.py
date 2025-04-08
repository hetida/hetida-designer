import os

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LocalFileAdapterConfig(BaseSettings):
    """Configuration for local file adapter"""

    local_dirs: set[str] = Field(
        {"tests/data/local_files"},
        description=(
            "Root directory paths provided as JSON-List of Strings."
            " These paths will be made available by the local file adapter."
            " Typically these are volume mounts in the runtime container."
        ),
        validation_alias="RUNTIME_LOCAL_FILE_ADAPTER_LOCAL_DIRECTORIES",
    )
    allowed_origins: str = Field(
        (
            "http://localhost:4200,http://localhost:80,localhost"
            ",http://localhost,hetida-designer-runtime"
        ),
        description="Comma separated allowed origins (CORS)",
        validation_alias="RUNTIME_LOCAL_FILE_ADAPTER_ALLOWED_ORIGINS",
        examples=["http://exampledomain.com,http://anotherexampledomain.de"],
    )
    generic_any_sink: bool = Field(
        True,
        description="Whether a generic sink of type ANY is offered in each directory",
        validation_alias="RUNTIME_LOCAL_FILE_ADAPTER_GENERIC_ANY_SINKS",
    )
    generic_dataframe_sink: bool = Field(
        True,
        description="Whether a generic sink of type DATAFRAME is offered in each directory",
        validation_alias="RUNTIME_LOCAL_FILE_ADAPTER_GENERIC_DATAFRAME_SINKS",
    )

    model_config = SettingsConfigDict(validate_by_alias=True, validate_by_name=True)


environment_file = os.environ.get("HD_LOCAL_FILE_ADAPTER_ENVIRONMENT_FILE", None)

local_file_adapter_config = LocalFileAdapterConfig(
    _env_file=environment_file if environment_file else None  # type: ignore[call-arg]
)

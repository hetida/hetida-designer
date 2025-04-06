import os

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings


class ExternalSourcesAdapterConfig(BaseSettings):
    """Configuration for external sources adapter"""

    active: bool = Field(
        True,
        description="Whether external sources adapter is started",
        validation_alias="EXTERNAL_SOURCES_ADAPTER_ACTIVE",
    )
    service_in_runtime: bool = Field(
        True,
        description=(
            "Whether the API part serving the hd frontend is started as part"
            " of the runtime API service as opposed to as part of the backend API."
        ),
        validation_alias="EXTERNAL_SOURCES_ADAPTER_SERVICE_IN_RUNTIME",
    )

    openmeteo_api_key: str | None = Field(None, validation_alias="OPEN_METEO_API_KEY")
    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)


environment_file = os.environ.get("HD_EXTERNAL_SOURCES_ADAPTER_ENVIRONMENT_FILE", None)

external_sources_adapter_config = ExternalSourcesAdapterConfig(
    _env_file=environment_file if environment_file else None  # type: ignore[call-arg]
)


def get_external_sources_adapter_config() -> ExternalSourcesAdapterConfig:
    return external_sources_adapter_config

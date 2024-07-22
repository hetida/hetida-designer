import os

from pydantic import BaseSettings, Field


class VirtualStructureAdapterConfig(BaseSettings):
    active: bool = Field(
        True,
        description="Whether to use the adapter or not",
        env="VST_ADAPTER_ACTIVE",
    )

    service_in_runtime: bool = Field(
        True,
        description=(
            "Whether the API part serving the hd frontend is started as part"
            " of the runtime API service as opposed to as part of the backend API."
        ),
        env="VST_ADAPTER_SERVICE_IN_RUNTIME",
    )


environment_file = os.environ.get("HD_VST_ADAPTER_ENVIRONMENT_FILE", None)

vst_adapter_config = VirtualStructureAdapterConfig(
    _env_file=environment_file if environment_file else None  # type: ignore[call-arg]
)


def get_vst_adapter_config() -> VirtualStructureAdapterConfig:
    return vst_adapter_config

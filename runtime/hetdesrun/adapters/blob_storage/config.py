import os

from pydantic import BaseSettings, Field, validator


class BlobStorageAdapterConfig(BaseSettings):
    """Configuration for blob storage adapter"""

    adapter_hierarchy_location: str = Field(
        "",
        description=(
            "Path to the adapter hierarchy json file. "
            "Must be set to enable the BLOB storage adapter REST API. "
        ),
        env="BLOB_STORAGE_ADAPTER_HIERARCHY_LOCATION",
        example="/mnt/blob_storage_adapter_hierarchy.json",
    )
    access_duration: int = Field(
        3600,
        description=(
            "Sets the request parameter `DurationSeconds` "
            "in the role session authentication towards the BLOB storage. "
            "Must be at least 900 (15 minutes) and smaller than "
            "the maximum session duration setting for the role, which is at most 12 hours."
        ),
        env="BLOB_STORAGE_ACCESS_DURATION",
    )
    endpoint_url: str = Field(
        "",
        description="URL under which the BLOB storage is accessible.",
        env="BLOB_STORAGE_ENDPOINT_URL",
        example="http://minio:9000",
    )
    region_name: str = Field(
        "eu-central-1", description="", env="BLOB_STORAGE_REGION_NAME"
    )

    @validator("access_duration")
    def access_duration_in_range(cls, access_duration: int) -> int:
        if access_duration < 900:
            raise ValueError("The access duration must be at least 900 (seconds).")
        if access_duration > 43200:
            raise ValueError(
                "The access duration for the role session must be smaller than the maximum session "
                "duration setting for the role, which may at most be 12 hours, "
                "and thus at most 43200 (seconds)."
            )
        return access_duration


environment_file = os.environ.get("HD_RUNTIME_ENVIRONMENT_FILE", None)
blob_storage_adapter_config = BlobStorageAdapterConfig(_env_file=environment_file)


def get_blob_adapter_config() -> BlobStorageAdapterConfig:
    return blob_storage_adapter_config

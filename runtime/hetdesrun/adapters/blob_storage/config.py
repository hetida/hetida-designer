from pydantic import BaseSettings, Field


class BlobStorageAdapterConfig(BaseSettings):
    """Configuration for blob storage adapter"""

    adapter_hierarchy_location: str = Field(
        "/mount/blob_storage_adapter_hierarchy.json",
        env="BLOB_STORAGE_ADAPTER_HIERARCHY_LOCATION",
    )
    account_id: str = Field("", env="BLOB_STORAGE_ACCOUNT_ID")
    resource_id: str = Field("", env="BLOB_STORAGE_RESOURCE_ID")
    access_duration: int = Field(3600, env="BLOB_STORAGE_ACCESS_DURATION")
    endpoint_url: str = Field("", env="BLOB_STORAGE_ENDPOINT_URL")
    region_name: str = Field("eu-central-1", env="BLOB_STORAGE_REGION_NAME")


blob_storage_adapter_config = BlobStorageAdapterConfig()


def get_blob_adapter_config() -> BlobStorageAdapterConfig:
    return blob_storage_adapter_config

from typing import Optional

from pydantic import BaseSettings, Field, validator

from hetdesrun.webservice.config import get_config


class BlobStorageAdapterConfig(BaseSettings):
    """Configuration for blob storage adapter"""

    adapter_hierarchy_location: str = Field(
        "/mount/blob_storage_adapter_hierarchy.json",
        env="BLOB_STORAGE_ADAPTER_HIERARCHY_LOCATION",
    )
    account_id: Optional[str] = Field(None, env="BLOB_STORAGE_ACCOUNT_ID")
    resource_id: Optional[str] = Field(None, env="BLOB_STORAGE_RESOURCE_ID")
    access_duration: int = Field(3600, env="BLOB_STORAGE_ACCESS_DURATION")
    endpoint_url: Optional[str] = Field(None, env="BLOB_STORAGE_ENDPOINT_URL")
    region_name: Optional[str] = Field(None, env="BLOB_STORAGE_REGION_NAME")

    # pylint: disable=no-self-argument
    @validator("account_id", "resource_id", "endpoint_url", "region_name")
    def required_parameters_provided(cls, param: Optional[str]) -> Optional[str]:
        if param is None and get_config().is_runtime_service is True:
            raise ValueError
        return param


blob_storage_adapter_config = BlobStorageAdapterConfig()


def get_blob_adapter_config() -> BlobStorageAdapterConfig:
    return blob_storage_adapter_config

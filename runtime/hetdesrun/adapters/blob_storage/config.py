import os
from typing import Literal

from pydantic import BaseSettings, Field


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
    allow_bucket_creation: bool = Field(
        True,
        description=(
            "Allow the creation of buckets which match the adapter hierarchy if they are missing"
        ),
        env="BLOB_STORAGE_ADAPTER_ALLOW_BUCKET_CREATION",
    )
    endpoint_url: str = Field(
        "",
        description="URL under which the BLOB storage is accessible.",
        env="BLOB_STORAGE_ENDPOINT_URL",
        example="http://minio:9000",
    )
    sts_params: dict = Field(
        {},
        description=(
            "Parameters needed for authentication at the STS client "
            "additionaly to Action and WebIdentityToken."
        ),
        env="BLOB_STORAGE_STS_PARAMS",
        example={
            "DurationSeconds": 3600,
            "Version": "2011-06-15",
        },
    )
    region_name: Literal[
        "EU",
        "af-south-1",
        "ap-east-1",
        "ap-northeast-1",
        "ap-northeast-2",
        "ap-northeast-3",
        "ap-south-1",
        "ap-southeast-1",
        "ap-southeast-2",
        "ap-southeast-3",
        "ca-central-1",
        "cn-north-1",
        "cn-northwest-1",
        "eu-central-1",
        "eu-north-1",
        "eu-south-1",
        "eu-west-1",
        "eu-west-2",
        "eu-west-3",
        "me-south-1",
        "sa-east-1",
        "us-east-2",
        "us-gov-east-1",
        "us-gov-west-1",
        "us-west-1",
        "us-west-2",
    ] = Field(
        "eu-central-1",
        description="The name of the region associated with the S3 client.",
        env="BLOB_STORAGE_REGION_NAME",
    )


environment_file = os.environ.get("HD_RUNTIME_ENVIRONMENT_FILE", None)
blob_storage_adapter_config = BlobStorageAdapterConfig(_env_file=environment_file)


def get_blob_adapter_config() -> BlobStorageAdapterConfig:
    return blob_storage_adapter_config

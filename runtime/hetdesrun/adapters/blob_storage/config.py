from pydantic import BaseSettings, Field


class BlobStorageAdapterConfig(BaseSettings):
    """Configuration for blob storage adapter"""

    client_id: str = Field("", env="BLOB_STORAGE_IDENTITY_OPENID_CLIENT_ID")
    client_secret: str = Field("", env="BLOB_STORAGE_IDENTITY_OPENID_CLIENT_SECRET")
    redirect_uri: str = Field("", env="BLOB_STORAGE_IDENTITY_OPENID_REDIRECT_URI")
    authorize_url: str = Field("", env="BLOB_STORAGE_IDENTITY_AUTHORIZE_URL")
    token_url: str = Field("", env="BLOB_STORAGE_IDENTITY_TOKEN_URL")
    endpoint_url: str = Field("", env="BLOB_STORAGE_ENDPOINT_URL")
    region_name: str = Field("eu-central-1", env="BLOB_STORAGE_REGION_NAME")
    aws_access_key_id = Field("", env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key = Field("", env="AWS_SECRET_ACCESS_KEY")
    aws_session_token = Field("", env="AWS_SESSION_TOKEN")


blob_storage_adapter_config = BlobStorageAdapterConfig()


def get_blob_adapter_config() -> BlobStorageAdapterConfig:
    return blob_storage_adapter_config

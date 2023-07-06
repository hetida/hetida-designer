from hetdesrun.adapters.blob_storage.config import BlobStorageAdapterConfig


def test_blob_storage_adapter_config_default_values() -> None:
    config = BlobStorageAdapterConfig()

    assert config.adapter_hierarchy_location == ""
    assert config.anonymous is False
    assert config.allow_bucket_creation is True
    assert config.endpoint_url == ""
    assert config.sts_params == {}
    assert config.region_name == "eu-central-1"
    assert config.checksum_algorithm == "SHA1"


def test_blob_storage_adapter_config_validator_no_anonymous_bucket_creation() -> None:
    anonymous_config = BlobStorageAdapterConfig(anonymous=True)

    assert anonymous_config.anonymous is True
    assert anonymous_config.allow_bucket_creation is False

from unittest import mock

import boto3
import pytest
from moto import mock_s3

from hetdesrun.adapters.blob_storage.authentication import Credentials
from hetdesrun.adapters.blob_storage.exceptions import StorageAuthenticationError
from hetdesrun.adapters.blob_storage.models import BucketName
from hetdesrun.adapters.blob_storage.service import (
    ensure_bucket_exists,
    get_object_key_strings_in_bucket,
    get_s3_client,
    get_session,
)
from hetdesrun.adapters.exceptions import AdapterConnectionError


@pytest.mark.asyncio
async def test_blob_storage_service_get_session() -> None:
    with (
        mock.patch(
            "hetdesrun.adapters.blob_storage.service.get_credentials",
            return_value=Credentials(
                access_key_id="some_id",
                secret_access_key="some_key",  # noqa: S106
                session_token="some_token",  # noqa: S106
            ),
        ),
        mock_s3(),
    ):
        session = await get_session()
        boto3_credentials = session.get_credentials()
        assert boto3_credentials.access_key == "some_id"
        assert boto3_credentials.secret_key == "some_key"  # noqa: S105
        assert boto3_credentials.token == "some_token"  # noqa: S105
        assert session.region_name == "eu-central-1"


@pytest.mark.asyncio
async def test_blob_storage_service_get_s3_client() -> None:
    with (
        mock_s3(),
        mock.patch(
            "hetdesrun.adapters.blob_storage.service.get_session",
            return_value=boto3.Session(
                aws_access_key_id="some_key_id",
                aws_secret_access_key="some_key",  # noqa: S106
                aws_session_token="some_token",  # noqa: S106
                region_name="eu-central-1",
            ),
        ),
    ):
        with mock.patch(
            "hetdesrun.adapters.blob_storage.service.get_blob_adapter_config",
            return_value=mock.Mock(endpoint_url="invalid_endpoint_url"),
        ):
            with pytest.raises(StorageAuthenticationError) as exc_info:
                await get_s3_client()
            assert "The string 'invalid_endpoint_url' is no valid endpoint url!" in str(
                exc_info.value
            )

        with mock.patch(
            "hetdesrun.adapters.blob_storage.service.get_blob_adapter_config",
            return_value=mock.Mock(endpoint_url="http://localhost:9000"),
        ):
            await get_s3_client()


@pytest.mark.asyncio
async def test_ensure_bucket_exists() -> None:
    with mock_s3():
        client_mock = boto3.client("s3", region_name="us-east-1")
        with mock.patch(
            "hetdesrun.adapters.blob_storage.service.get_s3_client",
            return_value=client_mock,
        ):
            with (
                mock.patch(
                    "hetdesrun.adapters.blob_storage.service.get_blob_adapter_config",
                    return_value=mock.Mock(allow_bucket_creation=False),
                ),
                pytest.raises(AdapterConnectionError, match=r"bucket.* does not exist"),
            ):
                ensure_bucket_exists(
                    s3_client=client_mock,
                    bucket_name=BucketName("bucket_name"),
                )

            ensure_bucket_exists(
                s3_client=client_mock,
                bucket_name=BucketName("bucket_name"),
            )


@pytest.mark.asyncio
async def test_blob_storage_service_get_object_key_strings_in_bucket() -> None:
    with mock_s3():
        client_mock = boto3.client("s3", region_name="eu-central-1")
        client_mock.create_bucket(
            Bucket="bucket-without-objects-name",
            CreateBucketConfiguration={"LocationConstraint": "eu-central-1"},
        )
        client_mock.create_bucket(
            Bucket="bucket-with-objects-name",
            CreateBucketConfiguration={"LocationConstraint": "eu-central-1"},
        )
        client_mock.put_object(Bucket="bucket-with-objects-name", Key="key")
        with mock.patch(
            "hetdesrun.adapters.blob_storage.service.get_s3_client",
            return_value=client_mock,
        ):
            with (
                mock.patch(
                    "hetdesrun.adapters.blob_storage.service.get_blob_adapter_config",
                    return_value=mock.Mock(allow_bucket_creation=False),
                ),
                pytest.raises(AdapterConnectionError, match=r"bucket.* does not exist"),
            ):
                await get_object_key_strings_in_bucket(BucketName("non_existent_bucket_name"))

            empty_object_key_string_list = await get_object_key_strings_in_bucket(
                BucketName("bucket-without-objects-name")
            )
            assert empty_object_key_string_list == []

            object_key_string_list = await get_object_key_strings_in_bucket(
                BucketName("bucket-with-objects-name")
            )
            assert object_key_string_list == ["key"]

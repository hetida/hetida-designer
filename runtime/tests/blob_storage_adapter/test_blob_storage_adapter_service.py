from unittest import mock

import boto3
import pytest
from moto import mock_s3

from hetdesrun.adapters.blob_storage.authentication import Credentials
from hetdesrun.adapters.blob_storage.exceptions import BucketNotFound, InvalidS3Endpoint
from hetdesrun.adapters.blob_storage.service import (
    get_object_key_strings_in_bucket,
    get_s3_client,
    get_session,
)


def test_blob_storage_service_get_session():
    with mock.patch(
        "hetdesrun.adapters.blob_storage.service.get_credentials",
        return_value=Credentials(
            access_key_id="some_id",
            secret_access_key="some_key",
            session_token="some_token",
        ),
    ):
        with mock_s3():
            session = get_session()
            boto3_credentials = session.get_credentials()
            assert boto3_credentials.access_key == "some_id"
            assert boto3_credentials.secret_key == "some_key"
            assert boto3_credentials.token == "some_token"
            assert session.region_name == "eu-central-1"


def test_blob_storage_service_get_s3_resource():
    with mock_s3():
        with mock.patch(
            "hetdesrun.adapters.blob_storage.service.get_session",
            return_value=boto3.Session(
                aws_access_key_id="some_key_id",
                aws_secret_access_key="some_key",
                aws_session_token="some_token",
                region_name="eu-central-1",
            ),
        ):
            with mock.patch(
                "hetdesrun.adapters.blob_storage.service.get_blob_adapter_config",
                return_value=mock.Mock(endpoint_url="invalid_endpoint_url"),
            ):
                with pytest.raises(InvalidS3Endpoint) as exc_info:
                    get_s3_client()
                assert (
                    "The string 'invalid_endpoint_url' is no valid endpoint url!"
                    in str(exc_info.value)
                )

            with mock.patch(
                "hetdesrun.adapters.blob_storage.service.get_blob_adapter_config",
                return_value=mock.Mock(endpoint_url="http://localhost:9000"),
            ):
                get_s3_client()


def test_blob_storage_service_get_object_key_strings_in_bucket():
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
            with pytest.raises(BucketNotFound) as exc_info:
                get_object_key_strings_in_bucket("non_existent_bucket_name")
            assert "The bucket 'non_existent_bucket_name' does not exist!" in str(
                exc_info.value
            )

            empty_object_key_string_list = get_object_key_strings_in_bucket("bucket-without-objects-name")
            assert empty_object_key_string_list == []

            object_key_string_list = get_object_key_strings_in_bucket("bucket-with-objects-name")
            assert object_key_string_list == ["key"]

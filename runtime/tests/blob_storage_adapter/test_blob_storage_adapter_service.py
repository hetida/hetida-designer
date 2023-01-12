from unittest import mock

import boto3
import pytest
from moto import mock_s3

from hetdesrun.adapters.blob_storage.authentication import Credentials
from hetdesrun.adapters.blob_storage.service import (
    get_object_key_strings_in_bucket,
    get_s3_resource,
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
            get_s3_resource()


def test_blob_storage_service_get_object_key_strings_in_bucket():
    with mock_s3():
        with mock.patch(
            "hetdesrun.adapters.blob_storage.service.get_s3_resource",
            return_value=boto3.Session(
                aws_access_key_id="some_key_id",
                aws_secret_access_key="some_key",
                aws_session_token="some_token",
                region_name="eu-central-1",
            ).resource("s3"),
        ):
            oks = get_object_key_strings_in_bucket("bucket_name")
            assert oks == []

from logging import getLogger
from typing import List

import boto3
from botocore.client import Config
from mypy_boto3_s3.service_resource import S3ServiceResource

from hetdesrun.adapters.blob_storage.config import get_blob_adapter_config
from hetdesrun.adapters.blob_storage.models import BucketName, IdString
from hetdesrun.webservice.auth_outgoing import create_or_get_named_access_token_manager
from hetdesrun.webservice.config import get_config

logger = getLogger(__name__)


def get_access_token() -> str:
    service_credentials = get_config().internal_auth_client_credentials
    assert service_credentials is not None  # for mypy
    access_token_manager = create_or_get_named_access_token_manager(
        "blob_adapter_auth", service_credentials
    )
    access_token = access_token_manager.sync_get_access_token()
    return access_token


def get_resource() -> S3ServiceResource:
    sts_client = boto3.client(
        "sts",
        region_name=get_blob_adapter_config().region_name,
        use_ssl=False,
        endpoint_url=get_blob_adapter_config().endpoint_url,
    )

    response = sts_client.assume_role_with_web_identity(
        # Amazon Resource Name (ARN)
        RoleArn="arn:aws:iam::123456789012:user/svc-internal-api",
        RoleSessionName="test",
        WebIdentityToken=get_access_token(),
        DurationSeconds=3600,
    )

    s3_resource = boto3.resource(
        "s3",
        endpoint_url=get_blob_adapter_config().endpoint_url,
        aws_access_key_id=response["Credentials"]["AccessKeyId"],
        aws_secret_access_key=response["Credentials"]["SecretAccessKey"],
        aws_session_token=response["Credentials"]["SessionToken"],
        config=Config(signature_version="s3v4"),
        region_name=get_blob_adapter_config().region_name,
    )
    return s3_resource


def get_object_key_strings_in_bucket(bucket_name: BucketName) -> List[IdString]:
    resource = get_resource()
    bucket = resource.Bucket(bucket_name)
    object_key_strings = [
        IdString(obj_summary.key) for obj_summary in bucket.objects.all()
    ]
    return object_key_strings

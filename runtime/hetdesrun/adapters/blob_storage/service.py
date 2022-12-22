from logging import getLogger
from typing import List

import boto3
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


def get_session() -> boto3.Session:
    sts_client = boto3.client(
        "sts",
        region_name=get_blob_adapter_config().region_name,
        use_ssl=False,
        endpoint_url=get_blob_adapter_config().endpoint_url,
    )

    response = sts_client.assume_role_with_web_identity(
        # Amazon Resource Name (ARN)
        # arn:partition:service:region:account-id:(resource-type/)resource-id
        RoleArn=(
            f"arn:aws:iam::{get_blob_adapter_config().account_id}"
            f":{get_blob_adapter_config().resource_id}"
        ),
        RoleSessionName="get-credentials",
        WebIdentityToken=get_access_token(),
        DurationSeconds=3600,
    )
    credentials = response["Credentials"]
    session = boto3.Session(
        aws_access_key_id=credentials["AccessKeyId"],
        aws_secret_access_key=credentials["SecretAccessKey"],
        aws_session_token=credentials["SessionToken"],
        region_name=get_blob_adapter_config().region_name,
    )
    return session


def get_s3_resource() -> S3ServiceResource:
    return get_session().resource(
        "s3", endpoint_url=get_blob_adapter_config().endpoint_url
    )


def get_object_key_strings_in_bucket(bucket_name: BucketName) -> List[IdString]:
    bucket = get_s3_resource().Bucket(bucket_name)
    object_key_strings = [
        IdString(obj_summary.key) for obj_summary in bucket.objects.all()
    ]
    return object_key_strings

from logging import getLogger
from typing import List

import boto3
from mypy_boto3_s3.service_resource import S3ServiceResource

from hetdesrun.adapters.blob_storage.authenticaton import get_credentials
from hetdesrun.adapters.blob_storage.config import get_blob_adapter_config
from hetdesrun.adapters.blob_storage.models import BucketName, IdString

logger = getLogger(__name__)


def get_session() -> boto3.Session:
    credentials = get_credentials()
    session = boto3.Session(
        aws_access_key_id=credentials.access_key_id,
        aws_secret_access_key=credentials.secret_access_key,
        aws_session_token=credentials.session_token,
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

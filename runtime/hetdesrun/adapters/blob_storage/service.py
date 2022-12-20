from functools import cache
from logging import getLogger
from typing import List

import boto3
from botocore.client import Config
from mypy_boto3_s3.service_resource import S3ServiceResource

from hetdesrun.adapters.blob_storage.config import get_blob_adapter_config
from hetdesrun.adapters.blob_storage.models import BucketName, IdString

logger = getLogger(__name__)


@cache
def get_resource() -> S3ServiceResource:
    s3_resource = boto3.resource(
        "s3",
        endpoint_url=get_blob_adapter_config().endpoint_url,
        aws_access_key_id=get_blob_adapter_config().aws_access_key_id,
        aws_secret_access_key=get_blob_adapter_config().aws_secret_access_key,
        aws_session_token=get_blob_adapter_config().aws_session_token,
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

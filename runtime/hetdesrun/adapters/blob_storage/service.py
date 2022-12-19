from functools import cache
from logging import getLogger
from typing import List

from boto3 import Session
from mypy_boto3_s3.service_resource import S3ServiceResource

from hetdesrun.adapters.blob_storage.models import BucketName, IdString

logger = getLogger(__name__)


@cache
def get_resource() -> S3ServiceResource:
    resource = Session().resource("s3")
    return resource


def get_object_key_strings_in_bucket(bucket_name: BucketName) -> List[IdString]:
    resource = get_resource()
    bucket = resource.Bucket(bucket_name)
    object_key_strings = [
        IdString(obj_summary.key) for obj_summary in bucket.objects.all()
    ]
    return object_key_strings

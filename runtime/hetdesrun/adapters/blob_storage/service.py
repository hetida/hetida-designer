from logging import getLogger
from typing import List

import boto3
from mypy_boto3_s3 import S3Client

from hetdesrun.adapters.blob_storage.authentication import get_credentials
from hetdesrun.adapters.blob_storage.config import get_blob_adapter_config
from hetdesrun.adapters.blob_storage.exceptions import BucketNotFound, InvalidS3Endpoint
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
    logger.info("Started a new S3 session")
    return session


def get_s3_client() -> S3Client:
    endpoint_url = get_blob_adapter_config().endpoint_url
    try:
        client = get_session().client("s3", endpoint_url=endpoint_url)
    except ValueError as error:
        msg = f"The string '{endpoint_url}' is no valid endpoint url!"
        logger.error(msg)
        raise InvalidS3Endpoint(msg) from error
    return client


def get_object_key_strings_in_bucket(bucket_name: BucketName) -> List[IdString]:
    s3_client = get_s3_client()
    try:
        s3_response = s3_client.list_objects_v2(Bucket=bucket_name)
    except s3_client.exceptions.NoSuchBucket as error:
        msg = f"The bucket '{bucket_name}' does not exist!"
        logger.error(msg)
        raise BucketNotFound(msg) from error

    if s3_response["KeyCount"] == 0:
        return []

    object_key_strings = [
        IdString(obj_summary["Key"]) for obj_summary in s3_response["Contents"]
    ]
    return object_key_strings

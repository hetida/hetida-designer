from logging import getLogger

import boto3
from mypy_boto3_s3 import S3Client

from hetdesrun.adapters.blob_storage.authentication import get_credentials
from hetdesrun.adapters.blob_storage.config import get_blob_adapter_config
from hetdesrun.adapters.blob_storage.exceptions import (
    InvalidEndpointError,
    StorageAuthenticationError,
)
from hetdesrun.adapters.blob_storage.models import BucketName, IdString
from hetdesrun.adapters.exceptions import AdapterConnectionError

logger = getLogger(__name__)


async def get_session() -> boto3.Session:
    try:
        credentials = await get_credentials()
    except StorageAuthenticationError as error:
        raise AdapterConnectionError(error) from error
    session = boto3.Session(
        aws_access_key_id=credentials.access_key_id,
        aws_secret_access_key=credentials.secret_access_key,
        aws_session_token=credentials.session_token,
        region_name=get_blob_adapter_config().region_name,
    )
    logger.info("Started a new S3 session")
    return session


async def get_s3_client() -> S3Client:
    endpoint_url = get_blob_adapter_config().endpoint_url
    try:
        session = await get_session()
    except AdapterConnectionError as error:
        raise error
    try:
        client = session.client("s3", endpoint_url=endpoint_url)
    except ValueError as error:
        msg = f"The string '{endpoint_url}' is no valid endpoint url!"
        logger.error(msg)
        raise InvalidEndpointError(msg) from error
    return client


async def get_object_key_strings_in_bucket(bucket_name: BucketName) -> list[IdString]:
    try:
        s3_client = await get_s3_client()
    except (AdapterConnectionError, InvalidEndpointError) as error:
        raise error
    try:
        s3_response = s3_client.list_objects_v2(Bucket=bucket_name)
    except s3_client.exceptions.NoSuchBucket as error:
        msg = f"The bucket '{bucket_name}' does not exist!"
        logger.error(msg)
        raise AdapterConnectionError(msg) from error

    if s3_response["KeyCount"] == 0:
        return []

    object_key_strings = [
        IdString(obj_summary["Key"]) for obj_summary in s3_response["Contents"]
    ]
    return object_key_strings

from logging import getLogger

import boto3
from botocore import UNSIGNED
from botocore.client import Config
from botocore.exceptions import ClientError
from mypy_boto3_s3 import S3Client

from hetdesrun.adapters.blob_storage.authentication import get_credentials
from hetdesrun.adapters.blob_storage.config import get_blob_adapter_config
from hetdesrun.adapters.blob_storage.exceptions import StorageAuthenticationError
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
    """Get S3 client.

    A AdapterConnectionError raised in get_session may occur.
    """
    endpoint_url = get_blob_adapter_config().endpoint_url

    try:
        if get_blob_adapter_config().anonymous is True:
            client = boto3.client(
                "s3",
                endpoint_url=endpoint_url,
                config=Config(signature_version=UNSIGNED),
            )
        else:
            session = await get_session()
            client = session.client("s3", endpoint_url=endpoint_url)
    except ValueError as error:
        msg = f"The string '{endpoint_url}' is no valid endpoint url!"
        logger.error(msg)
        raise StorageAuthenticationError(msg) from error
    return client


def ensure_bucket_exists(s3_client: S3Client, bucket_name: BucketName) -> None:
    try:
        s3_client.head_bucket(Bucket=bucket_name)
    except ClientError as client_error:
        error_code = client_error.response["Error"]["Code"]
        if error_code != "404":
            msg = (
                "Unexpected ClientError occured for head_bucket call with bucket "
                f"{bucket_name}:\n{error_code}"
            )
            logger.error(msg)
            raise AdapterConnectionError(msg) from client_error
        if get_blob_adapter_config().allow_bucket_creation:
            try:
                s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={
                        "LocationConstraint": get_blob_adapter_config().region_name
                    },
                )
            except ClientError as another_client_error:
                error_code = client_error.response["Error"]["Code"]
                msg = (
                    "Unexpected ClientError occured for create_bucket call with bucket "
                    f"{bucket_name}:\n{error_code}"
                )
                raise AdapterConnectionError(msg) from another_client_error
        else:
            msg = f"The bucket '{bucket_name}' does not exist!"
            logger.error(msg)
            raise AdapterConnectionError(msg) from client_error


async def get_object_key_strings_in_bucket(bucket_name: BucketName) -> list[IdString]:
    """Get the object key strings of all objects in the given bucket.

    A AdapterConnectionError or StorageAuthenticationError raised in get_s3_client may occur.
    """
    s3_client = await get_s3_client()

    ensure_bucket_exists(s3_client, bucket_name)

    s3_response = s3_client.list_objects_v2(Bucket=bucket_name)

    if s3_response["KeyCount"] == 0:
        return []

    object_key_strings = [IdString(obj_summary["Key"]) for obj_summary in s3_response["Contents"]]
    return object_key_strings

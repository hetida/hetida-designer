import logging
import pickle
from typing import Any

from botocore.exceptions import ClientError

from hetdesrun.adapters.blob_storage.config import get_blob_adapter_config
from hetdesrun.adapters.blob_storage.models import IdString
from hetdesrun.adapters.blob_storage.service import get_s3_client
from hetdesrun.adapters.blob_storage.structure import (
    get_source_by_thing_node_id_and_metadata_key,
)
from hetdesrun.adapters.exceptions import (
    AdapterClientWiringInvalidError,
    AdapterConnectionError,
    AdapterHandlingException,
)
from hetdesrun.models.data_selection import FilteredSource

logger = logging.getLogger(__name__)


async def load_blob_from_storage(thing_node_id: str, metadata_key: str) -> Any:
    """Load BLOB from storage.

    Note, that StructureObjectNotFound, StructureObjectNotUnique, MissingHierarchyError,
    StorageAuthenticationError, and AdapterConnectionError raised from
    get_source_by_thing_node_id_and_metadata_key or get_s3_client may occur.
    """
    logger.info(
        "Identify source with thing node id '%s' and metadata key '%s'",
        thing_node_id,
        metadata_key,
    )
    source = await get_source_by_thing_node_id_and_metadata_key(
        IdString(thing_node_id), metadata_key
    )

    logger.info("Get bucket name and object key from source with id %s", source.id)
    structure_bucket, object_key = source.to_structure_bucket_and_object_key()

    logger.info(
        "Load data for source '%s' from storage in bucket '%s' under object key '%s'",
        source.id,
        structure_bucket.name,
        object_key.string,
    )
    s3_client = await get_s3_client()

    try:
        s3_client.head_bucket(Bucket=structure_bucket.name)
    except ClientError as client_error:
        error_code = client_error.response["Error"]["Code"]
        if error_code != "404":
            msg = (
                "Unexpected ClientError occured for head_bucket call with bucket "
                f"{structure_bucket.name}:\n{error_code}"
            )
            logger.error(msg)
            raise AdapterConnectionError(msg) from client_error
        if get_blob_adapter_config().allow_bucket_creation:
            s3_client.create_bucket(
                Bucket=structure_bucket.name,
                CreateBucketConfiguration={
                    "LocationConstraint": get_blob_adapter_config().region_name
                },
            )
        else:
            msg = f"The bucket '{structure_bucket.name}' does not exist!"
            logger.error(msg)
            raise AdapterConnectionError(msg) from client_error

    try:
        response = s3_client.get_object(
            Bucket=structure_bucket.name, Key=object_key.string, ChecksumMode="ENABLED"
        )
    except s3_client.exceptions.NoSuchKey as error:
        raise AdapterConnectionError(
            f"The bucket '{structure_bucket.name}' contains no object "
            f"with the key '{object_key.string}'!"
        ) from error

    try:
        data = pickle.load(response["Body"])
    except ModuleNotFoundError as error:
        msg = f"Cannot load module to unpickle file object:\n{error}"
        logger.error(msg)
        raise AdapterHandlingException(msg) from error

    return data


async def load_data(
    wf_input_name_to_filtered_source_mapping_dict: dict[str, FilteredSource],
    adapter_key: str,  # noqa: ARG001
) -> dict[str, Any]:
    """Load data for filtered sources from BLOB storage.

    A AdapterHandlingException or AdapterConnectionError raised in
    load_blob_from_storage may occur.
    """
    wf_input_name_to_data_dict: dict[str, Any] = {}

    for (
        wf_input_name,
        filtered_source,
    ) in wf_input_name_to_filtered_source_mapping_dict.items():
        if filtered_source.ref_id is None or filtered_source.ref_key is None:
            msg = (
                "To use the BLOB storage adapter each filtered "
                "source must have 'ref_id' and 'ref_key' set!\n"
                f"That is not the case for {filtered_source.json()}"
            )
            logger.error(msg)
            raise AdapterClientWiringInvalidError(msg)

        wf_input_name_to_data_dict[wf_input_name] = await load_blob_from_storage(
            filtered_source.ref_id, filtered_source.ref_key
        )

    return wf_input_name_to_data_dict

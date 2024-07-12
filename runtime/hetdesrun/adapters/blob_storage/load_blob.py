import logging
import pickle
from io import BytesIO
from typing import Any

import h5py
from mypy_boto3_s3 import S3Client
from mypy_boto3_s3.type_defs import GetObjectOutputTypeDef

from hetdesrun.adapters.blob_storage.config import get_blob_adapter_config
from hetdesrun.adapters.blob_storage.exceptions import StructureObjectNotFound
from hetdesrun.adapters.blob_storage.models import (
    FileExtension,
    IdString,
    ObjectKey,
    get_structure_bucket_and_object_key_prefix_from_id,
)
from hetdesrun.adapters.blob_storage.service import ensure_bucket_exists, get_s3_client
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


def get_object(
    s3_client: S3Client, bucket_name: str, object_key_string: str
) -> GetObjectOutputTypeDef:
    if get_blob_adapter_config().checksum_algorithm == "":  # noqa: PLC1901
        return s3_client.get_object(Bucket=bucket_name, Key=object_key_string)

    return s3_client.get_object(Bucket=bucket_name, Key=object_key_string, ChecksumMode="ENABLED")


async def load_blob_from_storage(thing_node_id: str, metadata_key: str) -> Any:
    """Load BLOB from storage.

    Note, that StructureObjectNotFound, MissingHierarchyError, StorageAuthenticationError, and
    AdapterConnectionError raised from get_source_by_thing_node_id_and_metadata_key or
    get_s3_client may occur.
    """
    logger.info(
        "Identify source with thing node id '%s' and metadata key '%s'",
        thing_node_id,
        metadata_key,
    )
    try:
        source = await get_source_by_thing_node_id_and_metadata_key(
            IdString(thing_node_id), metadata_key
        )
    except StructureObjectNotFound as error:
        raise AdapterClientWiringInvalidError(error) from error

    logger.info("Get bucket name and object key from source with id %s", source.id)
    bucket, object_key_string = get_structure_bucket_and_object_key_prefix_from_id(source.id)
    # This must work because otherwise get_source_by_thing_node_id_and_metadata_key
    # would have raised a StructureObjectNotFound error already.
    object_key = ObjectKey.from_string(object_key_string)

    logger.info(
        "Load data for source '%s' from storage in bucket '%s' under object key '%s'",
        source.id,
        bucket.name,
        object_key.string,
    )
    s3_client = await get_s3_client()

    ensure_bucket_exists(s3_client=s3_client, bucket_name=bucket.name)

    try:
        response = get_object(
            s3_client=s3_client,
            bucket_name=bucket.name,
            object_key_string=object_key.string,
        )
    except s3_client.exceptions.NoSuchKey as error:
        raise AdapterConnectionError(
            f"The bucket '{bucket.name}' contains no object " f"with the key '{object_key.string}'!"
        ) from error

    if object_key.file_extension == FileExtension.H5:
        try:
            import tensorflow as tf
        except ModuleNotFoundError as error:
            msg = (
                "To load a model from a BLOB in the hdf5 format, "
                f"add tensorflow to the runtime dependencies:\n{error}"
            )
            logger.error(msg)
            raise AdapterHandlingException(msg) from error
        else:
            logger.info("Successfully imported tensorflow version %s", tf.__version__)
            file_object = BytesIO(response["Body"].read())
            custom_objects: dict[str, Any] | None = None
            custom_objects_object_key = object_key.to_custom_objects_object_key()
            try:
                custom_objects_response = get_object(
                    s3_client=s3_client,
                    bucket_name=bucket.name,
                    object_key_string=custom_objects_object_key.string,
                )
            except s3_client.exceptions.NoSuchKey:
                pass
            else:
                custom_objects = pickle.load(  # noqa: S301
                    custom_objects_response["Body"]
                )
            with h5py.File(file_object, "r") as f:
                data = tf.keras.saving.load_model(f, custom_objects=custom_objects)
    else:
        data = pickle.load(response["Body"])  # noqa: S301

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

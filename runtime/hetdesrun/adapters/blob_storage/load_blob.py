import logging
import pickle
from typing import Any

import h5py

from hetdesrun.adapters.blob_storage.exceptions import StructureObjectNotFound
from hetdesrun.adapters.blob_storage.models import (
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
    bucket, object_key_string = get_structure_bucket_and_object_key_prefix_from_id(
        source.id
    )
    # This must work because otherwise get_source_by_thing_node_id_and_metadata_key
    # would have raised a StructureObjectNotFound error already.
    object_key = ObjectKey.from_string(object_key_string)

    logger.info(
        "Load data for source '%s' from storage in bucket '%s' under object key '%s'",
        source.id,
        bucket.name,
        object_key_string,
    )
    s3_client = await get_s3_client()

    ensure_bucket_exists(s3_client=s3_client, bucket_name=bucket.name)

    try:
        response = s3_client.get_object(
            Bucket=bucket.name, Key=object_key_string, ChecksumMode="ENABLED"
        )
    except s3_client.exceptions.NoSuchKey as error:
        raise AdapterConnectionError(
            f"The bucket '{bucket.name}' contains no object "
            f"with the key '{object_key_string}'!"
        ) from error

    try:
        if object_key.file_extension == ".h5":
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
                logger.info(
                    "Successfully imported tensorflow version %s", tf.__version__
                )
                with h5py.File(response["Body"], "r") as f:
                    data = tf.keras.models.load_model(f)
        else:
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

import logging
import pickle
from io import BytesIO
from typing import Any

import h5py
from botocore.exceptions import ClientError, ParamValidationError

from hetdesrun.adapters.blob_storage.exceptions import StructureObjectNotFound
from hetdesrun.adapters.blob_storage.models import (
    BlobStorageStructureSink,
    IdString,
    ObjectKey,
    StructureBucket,
    get_structure_bucket_and_object_key_prefix_from_id,
)
from hetdesrun.adapters.blob_storage.service import ensure_bucket_exists, get_s3_client
from hetdesrun.adapters.blob_storage.structure import (
    get_sink_by_thing_node_id_and_metadata_key,
    get_thing_node_by_id,
)
from hetdesrun.adapters.exceptions import (
    AdapterClientWiringInvalidError,
    AdapterConnectionError,
    AdapterHandlingException,
)
from hetdesrun.models.data_selection import FilteredSink
from hetdesrun.runtime.logging import _get_job_id_context

logger = logging.getLogger(__name__)


def get_sink_and_bucket_and_object_key_from_thing_node_and_metadata_key(
    thing_node_id: str, metadata_key: str, file_extension: str
) -> tuple[BlobStorageStructureSink, StructureBucket, ObjectKey]:
    """Get sink, bucket, and object key from thing node id and metadata key.

    Note, that StructureObjectNotFound, StructureObjectNotUnique, MissingHierarchyError, and
    AdapterClientWiringInvalidError raised from get_sink_by_thing_node_id_and_metadata_key or
    get_thing_node_by_id may occur.
    """
    try:
        sink = get_sink_by_thing_node_id_and_metadata_key(
            IdString(thing_node_id), metadata_key
        )
    except StructureObjectNotFound:
        try:
            thing_node = get_thing_node_by_id(IdString(thing_node_id))
        except StructureObjectNotFound as error:
            raise AdapterClientWiringInvalidError(error) from error
        sink = BlobStorageStructureSink.from_thing_node(thing_node)
        try:
            structure_bucket, _ = get_structure_bucket_and_object_key_prefix_from_id(
                IdString(thing_node_id)
            )
            object_key = ObjectKey.from_thing_node_id_and_metadata_key(
                thing_node_id=IdString(thing_node_id),
                metadata_key=metadata_key,
                file_extension=file_extension,
            )
        except ValueError as error:
            msg = (
                f"Cannot write BLOB to sink with thing node id {thing_node_id} and "
                f"metadata key {metadata_key}. No such sink exists and it is not possible "
                f"to generate bucket name and object key:\n{error}"
            )
            logger.error(msg)
            raise AdapterClientWiringInvalidError(msg) from error
    else:
        job_id_context = _get_job_id_context()
        job_id = job_id_context["currently_executed_job_id"]
        logger.info("Get bucket name and object key from sink with id %s", sink.id)
        structure_bucket, object_key = sink.to_structure_bucket_and_object_key(
            job_id=job_id, file_extension=file_extension
        )

    return sink, structure_bucket, object_key


async def write_blob_to_storage(
    data: Any, thing_node_id: str, metadata_key: str
) -> None:
    """Write BLOB to storage.

    Note, that StructureObjectNotFound, StructureObjectNotUnique, MissingHierarchyError, and
    AdapterClientWiringInvalidError raised from
    get_sink_and_bucket_and_object_key_from_thing_node_and_metadata_key or
    StorageAuthenticationError and AdapterConnectionError raised from get_s3_client may occur.
    """
    is_keras_model = False
    try:
        import tensorflow as tf
    except ModuleNotFoundError:
        msg = "To store a keras model, add tensorflow to the runtime dependencies."
        logger.debug(msg)
    else:
        logger.debug("Successfully imported tensorflow version %s", tf.__version__)
        is_keras_model = isinstance(
            data, (tf.keras.models.Model, tf.keras.models.Sequential)
        )
        if is_keras_model:
            logger.info("Identified object as tensorflow keras model")

    (
        sink,
        structure_bucket,
        object_key,
    ) = get_sink_and_bucket_and_object_key_from_thing_node_and_metadata_key(
        thing_node_id=thing_node_id,
        metadata_key=metadata_key,
        file_extension="h5" if is_keras_model else "",
    )

    logger.info(
        "Write data for sink '%s' to storage into bucket '%s' as BLOB with key '%s'",
        sink.id,
        structure_bucket.name,
        object_key.string,
    )
    s3_client = await get_s3_client()

    ensure_bucket_exists(s3_client=s3_client, bucket_name=structure_bucket.name)

    try:
        # head_object is as get_object but without the body
        s3_client.head_object(Bucket=structure_bucket.name, Key=object_key.string)
    except ClientError as client_error:
        error_code = client_error.response["Error"]["Code"]
        if error_code != "404":
            msg = (
                "Unexpected ClientError occured for head_object call with bucket "
                f"{structure_bucket.name} and object key {object_key.string}:\n{error_code}"
            )
            logger.error(msg)
            raise AdapterConnectionError(msg) from client_error

        # only write if the object does not yet exist
        with BytesIO() as file_object:
            if is_keras_model:
                with h5py.File(file_object, "w") as h5_file_object:
                    tf.keras.models.save_model(data, h5_file_object)
                file_object.seek(0)
            else:
                pickle.dump(data, file_object, protocol=pickle.HIGHEST_PROTOCOL)
                file_object.seek(0)

            logger.info(
                "Dumped data of size %i into BLOB", file_object.getbuffer().nbytes
            )
            try:
                s3_client.put_object(
                    Bucket=structure_bucket.name,
                    Key=object_key.string,
                    Body=file_object,
                    ChecksumAlgorithm="SHA1",
                    ContentType="application/octet-stream"
                )
            except (
                ParamValidationError
            ) as error:  # TODO: clarify if it makes sense to raise this here
                msg = (
                    "Parameter validation error for put_object call with bucket "
                    f"{structure_bucket.name} and object key {object_key.string}:\n{error}"
                )
                logger.error(msg)
                raise AdapterHandlingException(msg) from error

    else:
        msg = (
            f"The bucket '{structure_bucket.name}' already contains an object "
            f"with the key '{object_key.string}', write request will not be executed!"
        )
        logger.error(msg)
        raise AdapterConnectionError(msg)


async def send_data(
    wf_output_name_to_filtered_sink_mapping_dict: dict[str, FilteredSink],
    wf_output_name_to_value_mapping_dict: dict[str, Any],
    adapter_key: str,  # noqa: ARG001
) -> dict[str, Any]:
    """Send data for filtered sinks from BLOB storage.

    A AdapterHandlingException or AdapterConnectionError raised in
    write_blob_to_storage may occur.
    """
    for (
        wf_output_name,
        filtered_sink,
    ) in wf_output_name_to_filtered_sink_mapping_dict.items():
        if filtered_sink.ref_id is None or filtered_sink.ref_key is None:
            msg = (
                "To use the BLOB storage adapter each filtered "
                "sink must have 'ref_id' and 'ref_key' set!"
                f"That is not the case for {filtered_sink.json()}"
            )
            logger.error(msg)
            raise AdapterClientWiringInvalidError(msg)

        blob = wf_output_name_to_value_mapping_dict[wf_output_name]
        await write_blob_to_storage(blob, filtered_sink.ref_id, filtered_sink.ref_key)
    return {}

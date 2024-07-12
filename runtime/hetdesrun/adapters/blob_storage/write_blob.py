import logging
import pickle
from io import BytesIO
from typing import Any, cast
from uuid import UUID

import h5py
from botocore.exceptions import ClientError
from mypy_boto3_s3 import S3Client
from mypy_boto3_s3.type_defs import PutObjectOutputTypeDef

from hdutils import WrappedModelWithCustomObjects
from hetdesrun.adapters.blob_storage import (
    HIERARCHY_END_NODE_NAME_SEPARATOR,
    OBJECT_KEY_DIR_SEPARATOR,
)
from hetdesrun.adapters.blob_storage.config import get_blob_adapter_config
from hetdesrun.adapters.blob_storage.exceptions import StructureObjectNotFound
from hetdesrun.adapters.blob_storage.models import (
    BlobStorageStructureSink,
    FileExtension,
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
)
from hetdesrun.models.data_selection import FilteredSink
from hetdesrun.runtime.logging import _get_job_id_context

logger = logging.getLogger(__name__)


def get_sink_and_bucket_and_object_key_from_thing_node_and_metadata_key(
    thing_node_id: str, metadata_key: str, file_extension: FileExtension
) -> tuple[BlobStorageStructureSink, StructureBucket, ObjectKey]:
    """Get sink, bucket, and object key from thing node id and metadata key.

    Note, that StructureObjectNotFound, StructureObjectNotUnique, MissingHierarchyError, and
    AdapterClientWiringInvalidError raised from get_sink_by_thing_node_id_and_metadata_key or
    get_thing_node_by_id may occur.
    """
    try:
        sink = get_sink_by_thing_node_id_and_metadata_key(IdString(thing_node_id), metadata_key)
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
        job_id = cast(UUID, job_id_context["currently_executed_job_id"])
        logger.info("Get bucket name and object key from sink with id %s", sink.id)
        structure_bucket, object_key = sink.to_structure_bucket_and_object_key(
            job_id=job_id, file_extension=file_extension
        )

    return sink, structure_bucket, object_key


def put_object(
    s3_client: S3Client, bucket_name: str, object_key_string: str, file_object: Any
) -> PutObjectOutputTypeDef:
    checksum_algorithm = get_blob_adapter_config().checksum_algorithm
    if checksum_algorithm == "":
        return s3_client.put_object(
            Bucket=bucket_name,
            Key=object_key_string,
            Body=file_object,
            ContentType="application/octet-stream",
        )
    return s3_client.put_object(
        Bucket=bucket_name,
        Key=object_key_string,
        Body=file_object,
        ChecksumAlgorithm=checksum_algorithm,
        ContentType="application/octet-stream",
    )


async def write_custom_objects_to_storage(
    s3_client: S3Client,
    custom_objects: dict[str, Any],
    structure_bucket: StructureBucket,
    object_key: ObjectKey,
) -> None:
    with BytesIO() as file_object:
        pickle.dump(
            custom_objects,
            file_object,
            protocol=pickle.HIGHEST_PROTOCOL,
        )
        file_object.seek(0)
        custom_objects_object_key = object_key.to_custom_objects_object_key()
        logger.info(
            "Dumped custom objects dictionary into another BLOB with object key %s",
            custom_objects_object_key.string,
        )

        try:
            put_object(
                s3_client=s3_client,
                bucket_name=structure_bucket.name,
                object_key_string=custom_objects_object_key.string,
                file_object=file_object,
            )
        except ClientError as client_error:
            error_code = client_error.response["Error"]["Code"]
            msg = (
                "Unexpected ClientError occured for put_object call with bucket "
                f"{structure_bucket.name} and object key {object_key.string}:\n{error_code}"
            )
            logger.error(msg)
            raise AdapterConnectionError(msg) from client_error


def apply_filters_to_metadata_key(
    thing_node_id: str, metadata_key: str, filters: dict[str, str]
) -> str:
    """Apply filters sent with the output wiring to the medatadata key if applicable.

    The free text filter `object_key_suffix` requires that the metadata key is set to a
    new value which contains the filter value.
    An exception is raised if that metadata key does not yield a valid object key.
    """
    if "object_key_suffix" in filters and len(filters["object_key_suffix"]) > 0:
        logger.debug("Apply 'object_key_suffix' filter.")
        object_key_suffix = filters["object_key_suffix"]
        sink_name = thing_node_id.rsplit(OBJECT_KEY_DIR_SEPARATOR, maxsplit=1)[1]
        metadata_key = sink_name + HIERARCHY_END_NODE_NAME_SEPARATOR + object_key_suffix
        try:
            ObjectKey.from_thing_node_id_and_metadata_key(
                IdString(thing_node_id),
                metadata_key,
                file_extension=FileExtension.Pickle,
            )
        except ValueError as error:
            msg = (
                f"Provided value '{object_key_suffix}' for the filter 'object_key_suffix' "
                f"at thingnode '{thing_node_id}' invalid! It must consist of a timestamp with "
                f'UTC timezone followed by " - " and a UUID: "<UTC timestamp> - <UUID>":\n{error}'
            )
            logger.error(msg)
            raise AdapterClientWiringInvalidError(msg) from error
        return metadata_key
    return metadata_key


async def write_blob_to_storage(
    data: Any, thing_node_id: str, metadata_key: str, filters: dict[str, str]
) -> None:
    """Write BLOB to storage.

    Note, that StructureObjectNotFound, StructureObjectNotUnique, MissingHierarchyError, and
    AdapterClientWiringInvalidError raised from
    get_sink_and_bucket_and_object_key_from_thing_node_and_metadata_key or
    StorageAuthenticationError and AdapterConnectionError raised from get_s3_client may occur.
    """
    is_keras_model = False
    is_keras_model_with_custom_objects = False
    try:
        import tensorflow as tf
    except ModuleNotFoundError:
        logger.debug("To store a keras model, add tensorflow to the runtime dependencies.")
    else:
        logger.debug("Successfully imported tensorflow version %s", tf.__version__)
        is_keras_model = isinstance(data, tf.keras.models.Model | tf.keras.models.Sequential)
        if is_keras_model:
            logger.debug("Identified object as tensorflow keras model")
        is_keras_model_with_custom_objects = isinstance(data, WrappedModelWithCustomObjects)
        if is_keras_model_with_custom_objects:
            logger.debug("Identified object as tensorflow keras model with custom objects")

    (
        sink,
        structure_bucket,
        object_key,
    ) = get_sink_and_bucket_and_object_key_from_thing_node_and_metadata_key(
        thing_node_id=thing_node_id,
        metadata_key=apply_filters_to_metadata_key(thing_node_id, metadata_key, filters),
        file_extension=FileExtension.H5
        if is_keras_model or is_keras_model_with_custom_objects
        else FileExtension.Pickle,
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
            if is_keras_model or is_keras_model_with_custom_objects:
                with h5py.File(file_object, "w") as h5_file_object:
                    tf.keras.saving.save_model(
                        data if is_keras_model else data.model, h5_file_object
                    )
                file_object.seek(0)
            else:
                pickle.dump(data, file_object, protocol=pickle.HIGHEST_PROTOCOL)
                file_object.seek(0)

            logger.info("Dumped data of size %i into BLOB", file_object.getbuffer().nbytes)

            try:
                put_object(
                    s3_client=s3_client,
                    bucket_name=structure_bucket.name,
                    object_key_string=object_key.string,
                    file_object=file_object,
                )
            except ClientError as error:
                error_code = error.response["Error"]["Code"]
                msg = (
                    "Unexpected ClientError occured for put_object call with bucket "
                    f"{structure_bucket.name} and object key {object_key.string}:\n{error_code}"
                )
                logger.error(msg)
                raise AdapterConnectionError(msg) from error
        if is_keras_model_with_custom_objects:
            await write_custom_objects_to_storage(
                s3_client=s3_client,
                custom_objects=data.custom_objects,
                structure_bucket=structure_bucket,
                object_key=object_key.to_custom_objects_object_key(),
            )
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
        await write_blob_to_storage(
            blob, filtered_sink.ref_id, filtered_sink.ref_key, filtered_sink.filters
        )
    return {}

import logging
import pickle
from io import BytesIO
from typing import Any

from botocore.exceptions import ClientError, ParamValidationError

from hetdesrun.adapters.blob_storage.models import IdString
from hetdesrun.adapters.blob_storage.service import get_s3_client
from hetdesrun.adapters.blob_storage.structure import (
    get_sink_by_thing_node_id_and_metadata_key,
)
from hetdesrun.adapters.exceptions import (
    AdapterClientWiringInvalidError,
    AdapterConnectionError,
    AdapterHandlingException,
)
from hetdesrun.models.data_selection import FilteredSink
from hetdesrun.runtime.logging import _get_job_id_context

logger = logging.getLogger(__name__)


async def write_blob_to_storage(
    data: Any, thing_node_id: str, metadata_key: str
) -> None:
    """Write BLOB to storage.

    Note, that StructureObjectNotFound, StructureObjectNotUnique, and MissingHierarchyError,
    raised from get_sink_by_thing_node_id_and_metadata_key or StorageAuthenticationError and
    AdapterConnectionError get_s3_client may occur.
    """
    sink = get_sink_by_thing_node_id_and_metadata_key(
        IdString(thing_node_id), metadata_key
    )
    job_id_context = _get_job_id_context()
    job_id = job_id_context["currently_executed_job_id"]
    logger.info("Get bucket name and object key from sink with id %s", sink.id)
    structure_bucket, object_key = sink.to_structure_bucket_and_object_key(job_id)

    logger.info(
        "Write data for sink '%s' to storage into bucket '%s' as blob with key '%s'",
        sink.id,
        structure_bucket.name,
        object_key.string,
    )
    s3_client = await get_s3_client()
    try:
        # head_object is as get_object but without the body
        s3_client.head_object(Bucket=structure_bucket.name, Key=object_key.string)
    except s3_client.exceptions.NoSuchBucket as error:
        raise AdapterConnectionError(
            f"The bucket '{structure_bucket.name}' does not exist!"
        ) from error
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
        try:
            file_object = BytesIO()
            pickle.dump(data, file_object, protocol=pickle.HIGHEST_PROTOCOL)
            file_object.seek(0)

            logger.info(
                "Dumped data of size %i into BLOB", file_object.getbuffer().nbytes
            )
            s3_client.put_object(
                Bucket=structure_bucket.name,
                Key=object_key.string,
                Body=file_object,
                ChecksumAlgorithm="SHA1",
            )
        except ParamValidationError as error:
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

import logging
from io import BytesIO
from typing import Any

import joblib

from hetdesrun.adapters.blob_storage.exceptions import (
    InvalidEndpointError,
    MissingHierarchyError,
    StructureObjectNotFound,
    StructureObjectNotUnique,
)
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


def load_blob_from_storage(thing_node_id: str, metadata_key: str) -> Any:
    logger.info(
        "Identify source with thing node id '%s' and metadata key '%s'",
        thing_node_id,
        metadata_key,
    )
    try:
        source = get_source_by_thing_node_id_and_metadata_key(
            IdString(thing_node_id), metadata_key
        )
    except (
        StructureObjectNotFound,
        StructureObjectNotUnique,
        MissingHierarchyError,
        InvalidEndpointError,
        AdapterConnectionError,
    ) as error:
        raise error

    logger.info("Get bucket name and object key from source with id %s", source.id)
    structure_bucket, object_key = source.to_structure_bucket_and_object_key()

    logger.info(
        "Load data for source '%s' from storage in bucket '%s' under object key '%s'",
        source.id,
        structure_bucket.name,
        object_key.string,
    )
    try:
        s3_client = get_s3_client()
    except (AdapterConnectionError, InvalidEndpointError) as error:
        raise error
    try:
        response = s3_client.get_object(
            Bucket=structure_bucket.name, Key=object_key.string, ChecksumMode="ENABLED"
        )
    except s3_client.exceptions.NoSuchBucket as error:
        raise AdapterConnectionError(
            f"The bucket '{structure_bucket.name}' does not exist!"
        ) from error
    except s3_client.exceptions.NoSuchKey as error:
        raise AdapterConnectionError(
            f"The bucket '{structure_bucket.name}' contains no object "
            f"with the key '{object_key.string}'!"
        ) from error

    data_bytes = response["Body"].read()

    file_object = BytesIO(data_bytes)
    logger.info("Got BLOB of size %i", file_object.getbuffer().nbytes)

    try:
        data = joblib.load(file_object)
    except ModuleNotFoundError as error:
        msg = f"Cannot load module to unpickle file object:\n{error}"
        logger.error(msg)
        raise AdapterHandlingException(msg) from error

    return data


async def load_data(
    wf_input_name_to_filtered_source_mapping_dict: dict[str, FilteredSource],
    adapter_key: str,  # noqa: ARG001
) -> dict[str, Any]:
    wf_input_name_to_data_dict: dict[str, Any] = {}

    for (
        wf_input_name,
        filtered_source,
    ) in wf_input_name_to_filtered_source_mapping_dict.items():
        if filtered_source.ref_id is None or filtered_source.ref_key is None:
            msg = ""
            logger.error(msg)
            raise AdapterClientWiringInvalidError(msg)

        try:
            wf_input_name_to_data_dict[wf_input_name] = load_blob_from_storage(
                filtered_source.ref_id, filtered_source.ref_key
            )
        except (AdapterHandlingException, AdapterConnectionError) as error:
            raise error

    return wf_input_name_to_data_dict

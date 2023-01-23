import logging
from typing import Any, Dict

from botocore.exceptions import ClientError

from hetdesrun.adapters.blob_storage.exceptions import (
    BucketNotFound,
    InvalidS3Endpoint,
    ObjectExists,
    SinkNotFound,
    SinkNotUnique,
    UnexpectedClientError,
)
from hetdesrun.adapters.blob_storage.models import IdString
from hetdesrun.adapters.blob_storage.service import get_s3_client
from hetdesrun.adapters.blob_storage.structure import (
    get_sink_by_thing_node_id_and_metadata_key,
)
from hetdesrun.models.data_selection import FilteredSink

logger = logging.getLogger(__name__)


def write_blob_to_storage(data: Any, thing_node_id: str, metadata_key: str) -> None:
    try:
        sink = get_sink_by_thing_node_id_and_metadata_key(
            IdString(thing_node_id), metadata_key
        )
    except SinkNotFound as error:
        raise error
    except SinkNotUnique as error:
        raise error

    logger.info("Get bucket name and object key from sink with id %s", sink.id)
    structure_bucket, object_key = sink.to_structure_bucket_and_object_key()

    logger.info(
        "Write data for sink '%s' to storage into bucket '%s' as blob with key '%s'",
        sink.id,
        structure_bucket.name,
        object_key.string,
    )
    try:
        s3_client = get_s3_client()
    except InvalidS3Endpoint as error:
        raise error
    try:
        # head_object is as get_object but without the body
        s3_client.head_object(Bucket=structure_bucket.name, Key=object_key.string)
    except s3_client.exceptions.NoSuchBucket as error:
        raise BucketNotFound(
            f"The bucket '{structure_bucket.name}' does not exist!"
        ) from error
    except ClientError as error:
        error_code = error.response["Error"]["Code"]
        if error_code !="404":
            msg = (
                "Unexpected ClientError occured for head_object call with bucket "
                f"{structure_bucket.name} and object key {object_key.string}:\n{error_code}"
            )
            logger.error(msg)
            raise UnexpectedClientError(msg)

        # only write if the object does not yet exist
        s3_client.put_object(
            Bucket=structure_bucket.name, Key=object_key.string, Body=data
        )
        
    else:
        msg = (
            f"The bucket '{structure_bucket.name}' already contains an object "
            f"with the key '{object_key.string}', write request will not be executed!"
        )
        logger.error(msg)
        raise ObjectExists(msg)


async def send_data(
    wf_output_name_to_filtered_sink_mapping_dict: Dict[str, FilteredSink],
    wf_output_name_to_value_mapping_dict: Dict[str, Any],
    adapter_key: str,  # pylint: disable=unused-argument
) -> Dict[str, Any]:
    try:
        for (
            wf_output_name,
            filtered_sink,
        ) in wf_output_name_to_filtered_sink_mapping_dict.items():
            if filtered_sink.ref_id is not None and filtered_sink.ref_key is not None:
                blob = wf_output_name_to_value_mapping_dict[wf_output_name]
                write_blob_to_storage(blob, filtered_sink.ref_id, filtered_sink.ref_key)
    except (
        SinkNotFound,
        SinkNotUnique,
        InvalidS3Endpoint,
        BucketNotFound,
        UnexpectedClientError,
    ) as error:
        raise error
    return {}

import logging
from typing import Any, Dict

from botocore.exceptions import ClientError

from hetdesrun.adapters.blob_storage.exceptions import SourceNotFound, SourceNotUnique
from hetdesrun.adapters.blob_storage.models import IdString
from hetdesrun.adapters.blob_storage.service import get_s3_client
from hetdesrun.adapters.blob_storage.structure import (
    get_source_by_thing_node_id_and_metadata_key,
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
    except SourceNotFound as error:
        # TODO: define behavior for SourceNotFound in load_blob_from_storage
        raise error
    except SourceNotUnique as error:
        # TODO: define behavior for SourceNotFound in load_blob_from_storage
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
        response = get_s3_client().get_object(
            Bucket=structure_bucket.name, Key=object_key.string
        )
    except ClientError as error:
        # TODO: define behavior for ClientError in load_blob_from_storage
        raise error
    return response["Body"].read()


async def load_data(
    wf_input_name_to_filtered_source_mapping_dict: Dict[str, FilteredSource],
    adapter_key: str,  # pylint: disable=unused-argument
) -> Dict[str, Any]:
    return {
        wf_input_name: load_blob_from_storage(
            filtered_source.ref_id, filtered_source.ref_key
        )
        for wf_input_name, filtered_source in wf_input_name_to_filtered_source_mapping_dict.items()
        if filtered_source.ref_id is not None and filtered_source.ref_key is not None
    }

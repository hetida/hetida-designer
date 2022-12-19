import logging
from typing import Any, Dict

from hetdesrun.adapters.blob_storage.models import IdString
from hetdesrun.adapters.blob_storage.service import get_resource
from hetdesrun.adapters.blob_storage.structure import (
    get_source_by_thing_node_id_and_metadata_key,
)
from hetdesrun.models.data_selection import FilteredSource

logger = logging.getLogger(__name__)


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


def load_blob_from_storage(thing_node_id: str, metadata_key: str) -> Any:
    logger.info(
        "Identify source with thing node id %s and metadata key %s",
        thing_node_id,
        metadata_key,
    )
    source = get_source_by_thing_node_id_and_metadata_key(
        IdString(thing_node_id), metadata_key
    )

    logger.info("Get bucket name and object key from source with id %s", source.id)
    structure_bucket, object_key = source.to_structure_bucket_and_object_key()

    logger.info(
        "Load data for source id %s from storage in bucket %s under object key %s",
        source.id,
        structure_bucket.name,
        object_key.string,
    )
    resource = get_resource()
    blob = resource.Bucket(structure_bucket.name).Object(object_key.string)
    blob.get()
    return blob

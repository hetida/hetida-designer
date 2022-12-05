import logging
from typing import Any, Dict

from hetdesrun.adapters.blob_storage.models import IdString
from hetdesrun.adapters.blob_storage.structure import get_source_by_id
from hetdesrun.models.data_selection import FilteredSource

logger = logging.getLogger(__name__)


async def load_data(
    wf_input_name_to_filtered_source_mapping_dict: Dict[str, FilteredSource],
    adapter_key: str,  # pylint: disable=unused-argument
) -> Dict[str, Any]:
    return {
        wf_input_name: load_blob_from_storage(filtered_source.ref_id)
        for wf_input_name, filtered_source in wf_input_name_to_filtered_source_mapping_dict.items()
        if filtered_source.ref_id is not None
    }


def load_blob_from_storage(source_id: str) -> Any:
    source = get_source_by_id(IdString(source_id))
    bucket_name, object_key = source.to_bucket_name_and_object_key()
    logger.info(
        "Load data for source id %s from storage in bucket %s under object key %s",
        source_id,
        bucket_name,
        object_key,
    )
    return {source_id}

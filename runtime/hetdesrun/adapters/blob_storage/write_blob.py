import logging
from typing import Any, Dict

from hetdesrun.adapters.blob_storage.models import IdString
from hetdesrun.adapters.blob_storage.structure import get_sink_by_id
from hetdesrun.models.data_selection import FilteredSink

logger = logging.getLogger(__name__)


async def send_data(
    wf_output_name_to_filtered_sink_mapping_dict: Dict[str, FilteredSink],
    wf_output_name_to_value_mapping_dict: Dict[str, Any],
    adapter_key: str,  # pylint: disable=unused-argument
) -> Dict[str, Any]:
    for (
        wf_output_name,
        filtered_sink,
    ) in wf_output_name_to_filtered_sink_mapping_dict.items():
        if filtered_sink.ref_id is not None:
            blob = wf_output_name_to_value_mapping_dict[wf_output_name]
            write_blob_to_storage(blob, filtered_sink.ref_id)
    return {}


def write_blob_to_storage(data: Any, thing_node_id: str) -> None:
    # deepest level thing nodes have the same ids as their corresponding sinks
    sink = get_sink_by_id(IdString(thing_node_id))

    bucket_name, object_key = sink.to_bucket_name_and_object_key()
    logger.info(
        "Write data %s for sink_id %s to storage into bucket %s as blob with key %s",
        str(data),
        thing_node_id,
        bucket_name,
        object_key,
    )

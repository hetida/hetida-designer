from logging import getLogger
from typing import Any, Dict, List

from hetdesrun.adapters.blob_storage.load_blob import load_blob_from_storage
from hetdesrun.adapters.blob_storage.utils import setup_adapter
from hetdesrun.adapters.blob_storage.write_blob import write_blob_to_storage
from hetdesrun.models.data_selection import FilteredSink, FilteredSource

logger = getLogger(__name__)

try:
    with open("VERSION", "r", encoding="utf8") as version_file:
        VERSION = version_file.read().strip()
except FileNotFoundError:
    VERSION = "dev snapshot"


tns, srcs, snks = setup_adapter()


async def load_data(
    wf_input_name_to_filtered_source_mapping_dict: Dict[str, FilteredSource],
    adapter_key: str,  # pylint: disable=unused-argument
) -> Dict[str, Any]:
    return {
        wf_input_name: load_blob_from_storage(filtered_source.ref_id)
        for wf_input_name, filtered_source in wf_input_name_to_filtered_source_mapping_dict.items()
        if filtered_source.ref_id is not None
    }


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

from typing import Any

from hetdesrun.adapters.local_file.load_file import load_file_from_id
from hetdesrun.adapters.local_file.write_file import write_to_file
from hetdesrun.models.data_selection import FilteredSink, FilteredSource

try:
    with open("VERSION", encoding="utf8") as version_file:
        VERSION = version_file.read().strip()
except FileNotFoundError:
    VERSION = "dev snapshot"


async def load_data(
    wf_input_name_to_filtered_source_mapping_dict: dict[str, FilteredSource],
    adapter_key: str,  # noqa: ARG001
) -> dict[str, Any]:
    return {
        wf_input_name: load_file_from_id(str(filtered_source.ref_id))
        for wf_input_name, filtered_source in wf_input_name_to_filtered_source_mapping_dict.items()
    }


async def send_data(
    wf_output_name_to_filtered_sink_mapping_dict: dict[str, FilteredSink],
    wf_output_name_to_value_mapping_dict: dict[str, Any],
    adapter_key: str,  # noqa: ARG001
) -> dict[str, Any]:
    for (
        wf_output_name,
        filtered_sink,
    ) in wf_output_name_to_filtered_sink_mapping_dict.items():
        df = wf_output_name_to_value_mapping_dict[wf_output_name]
        write_to_file(df, str(filtered_sink.ref_id))
    return {}

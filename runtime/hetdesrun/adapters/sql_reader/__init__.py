from typing import Any

from hetdesrun.adapters.sql_reader.load_table import load_table_from_provided_source_id
from hetdesrun.models.data_selection import FilteredSource

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
        wf_input_name: load_table_from_provided_source_id(
            str(
                filtered_source.ref_key
                if filtered_source.ref_key is not None
                else filtered_source.ref_id
            ),
            filtered_source.filters,
        )
        for wf_input_name, filtered_source in wf_input_name_to_filtered_source_mapping_dict.items()
    }

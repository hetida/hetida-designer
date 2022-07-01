"""Source Adapter for direct data providing

This adapter is used when data is provided directly during workflow
execution, i.e. when it is provided as part of the execution request.
"""

from typing import Any, Dict

from hetdesrun.adapters.exceptions import AdapterClientWiringInvalidError
from hetdesrun.models.data_selection import FilteredSource


def load_directly_provisioned_data(
    wf_input_name_to_filtered_source_mapping_dict: Dict[str, FilteredSource],
    adapter_key: str,  # pylint: disable=unused-argument
) -> Dict[str, Any]:

    try:
        return {
            wf_inp_name: direct_provisioning_filtered_source.filters["value"]
            for (
                wf_inp_name,
                direct_provisioning_filtered_source,
            ) in wf_input_name_to_filtered_source_mapping_dict.items()
        }
    except KeyError as e:
        raise AdapterClientWiringInvalidError(
            "Direct Input Provisioning without 'value' field in filters"
        ) from e

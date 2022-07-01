"""Sink Adapter for direct data providing

This adapter is used when data is emitted directly during workflow
execution, i.e. when it is returned as part of the execution response.
"""

from typing import Any, Dict

from hetdesrun.models.data_selection import FilteredSink


def send_directly_provisioned_data(
    wf_output_name_to_filtered_sink_mapping_dict: Dict[
        str, FilteredSink
    ],  # pylint: disable=unused-argument
    wf_output_name_to_value_mapping_dict: Dict[str, Any],
    adapter_key: str,  # pylint: disable=unused-argument
) -> Dict[str, Any]:
    # Direct provisioning when sending works by simply returning the data.
    # A custom adapter with a true data sink would instead return None.
    return {
        key: wf_output_name_to_value_mapping_dict[key]
        for key in wf_output_name_to_filtered_sink_mapping_dict.keys()
    }

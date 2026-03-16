"""Sink Adapter for drop

This adapter is used when data should simply be dropped.
"""

from typing import Any

from hetdesrun.models.data_selection import FilteredSink


def send_drop_data(
    wf_output_name_to_filtered_sink_mapping_dict: dict[str, FilteredSink],  # noqa: ARG001
    wf_output_name_to_value_mapping_dict: dict[str, Any],  # noqa: ARG001
    adapter_key: str,  # noqa: ARG001
) -> dict[str, Any]:
    # Dropping is done by simply doing nothing and returning nothing
    return {}

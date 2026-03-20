"""Sink Adapter for plot

This adapter is used when data should simply be plotted.
"""

from typing import Any

from hdutils import DataType
from hetdesrun.adapters.plot_adapter.default_plots import (
    provide_plotly_fig_json_for_arbitrary_value,
)
from hetdesrun.models.data_selection import FilteredSink


def send_plot_data(
    wf_output_name_to_filtered_sink_mapping_dict: dict[str, FilteredSink],  # noqa: ARG001
    wf_output_name_to_value_mapping_dict: dict[str, Any],  # noqa: ARG001
    adapter_key: str,  # noqa: ARG001
) -> dict[str, Any]:

    plots = {
        outp_name: provide_plotly_fig_json_for_arbitrary_value(
            wf_output_name_to_value_mapping_dict[outp_name],
            data_type
            if isinstance(
                data_type := wf_output_name_to_filtered_sink_mapping_dict[outp_name].type, DataType
            )
            else (DataType(data_type) if isinstance(data_type, str) else DataType.Any),
        )
        for outp_name in wf_output_name_to_filtered_sink_mapping_dict
    }

    return plots

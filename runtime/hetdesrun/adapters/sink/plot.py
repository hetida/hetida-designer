"""Sink Adapter for plot

This adapter is used when data should simply be plotted.
"""

from typing import Any

from hdutils import DataType
from hetdesrun.adapters.plot_adapter.default_plots import (
    provide_plotly_fig_json_for_arbitrary_value,
)
from hetdesrun.models.data_selection import FilteredSink
from hetdesrun.models.run import ConfigurationInput
from hetdesrun.runtime.configuration import execution_config


def send_plot_data(
    wf_output_name_to_filtered_sink_mapping_dict: dict[str, FilteredSink],  # noqa: ARG001
    wf_output_name_to_value_mapping_dict: dict[str, Any],  # noqa: ARG001
    adapter_key: str,  # noqa: ARG001
) -> dict[str, Any]:

    exe_context_config = execution_config.get(ConfigurationInput())

    plots = {
        outp_name: (
            provide_plotly_fig_json_for_arbitrary_value(
                wf_output_name_to_value_mapping_dict[outp_name],
                data_type
                if isinstance(
                    data_type := wf_output_name_to_filtered_sink_mapping_dict[outp_name].type,
                    DataType,
                )
                else (DataType(data_type) if isinstance(data_type, str) else DataType.Any),
            )
            if exe_context_config.run_pure_plot_operators
            else {}  # do not output plots if run_pure_plot_operators is False
        )
        for outp_name in wf_output_name_to_filtered_sink_mapping_dict
    }

    return plots

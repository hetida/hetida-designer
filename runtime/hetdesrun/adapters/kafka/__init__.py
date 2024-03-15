from typing import Any

from hetdesrun.adapters.kafka.producing import produce_data_to_kafka_sink
from hetdesrun.models.data_selection import FilteredSink


async def send_data(
    wf_output_name_to_filtered_sink_mapping_dict: dict[str, FilteredSink],
    wf_output_name_to_value_mapping_dict: dict[str, Any],
    adapter_key: str,  # noqa: ARG001
) -> dict[str, Any]:
    for (
        wf_output_name,
        filtered_sink,
    ) in wf_output_name_to_filtered_sink_mapping_dict.items():
        data = wf_output_name_to_value_mapping_dict[wf_output_name]

        id_to_use = (
            filtered_sink.ref_key
            if filtered_sink.ref_key is not None
            else filtered_sink.ref_id
        )

        await produce_data_to_kafka_sink(data, str(id_to_use))

    return {}

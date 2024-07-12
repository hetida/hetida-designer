from uuid import UUID

from hetdesrun.models.wiring import InputWiring, OutputWiring
from hetdesrun.structure.structure_service import (
    get_collection_of_sinks_from_db,
    get_collection_of_sources_from_db,
)


def get_actual_sources_and_sinks_for_virtual_sources_and_sinks(
    input_id_list: list[str], output_id_list: list[str]
) -> tuple[dict[str, InputWiring], dict[str, OutputWiring]]:
    actual_sources = get_collection_of_sources_from_db(
        [UUID(input_id) for input_id in input_id_list]
    )
    actual_sinks = get_collection_of_sinks_from_db(
        [UUID(output_id) for output_id in output_id_list]
    )

    actual_input_wirings = {
        str(src_id): InputWiring.from_structure_source(src)
        for src_id, src in actual_sources.items()
    }

    actual_output_wirings = {
        str(sink_id): OutputWiring.from_structure_sink(sink)
        for sink_id, sink in actual_sinks.items()
    }

    return actual_input_wirings, actual_output_wirings


def get_enumerated_ids_of_vst_sources_or_sinks(
    wirings: list[InputWiring] | list[OutputWiring],
) -> list[tuple[int, str]]:
    return [
        (i, wiring.ref_id)
        for i, wiring in enumerate(wirings)
        if wiring.adapter_id == "virtual-structure-adapter"
    ]

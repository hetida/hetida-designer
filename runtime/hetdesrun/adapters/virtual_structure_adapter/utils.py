import logging
from uuid import UUID

from hetdesrun.models.wiring import InputWiring, OutputWiring
from hetdesrun.structure.db.source_sink_service import (
    fetch_collection_of_sinks_from_db_by_id,
    fetch_collection_of_sources_from_db_by_id,
)
from hetdesrun.structure.models import StructureServiceSink, StructureServiceSource

logger = logging.getLogger(__name__)


def get_virtual_sources_and_sinks_from_structure_service(
    input_id_list: list[str], output_id_list: list[str]
) -> tuple[dict[UUID, StructureServiceSource], dict[UUID, StructureServiceSink]]:
    referenced_sources = fetch_collection_of_sources_from_db_by_id(
        [UUID(input_id) for input_id in input_id_list]
    )
    referenced_sinks = fetch_collection_of_sinks_from_db_by_id(
        [UUID(output_id) for output_id in output_id_list]
    )

    return referenced_sources, referenced_sinks


def get_enumerated_ids_of_vst_sources_or_sinks(
    wirings: list[InputWiring] | list[OutputWiring],
) -> tuple[list[int], list[str]]:
    """Takes a wiring and finds the index of all sources or sinks of the virtual structure adapter.

    Returns:
    - A list of said indices and a list of the corresponding source or sink ids.
    """
    indices, ref_ids = [], []
    for i, wiring in enumerate(wirings):
        if wiring.adapter_id == "virtual-structure-adapter":  # type: ignore[attr-defined]
            indices.append(i)
            ref_ids.append(wiring.ref_id)  # type: ignore[attr-defined]
    return indices, ref_ids

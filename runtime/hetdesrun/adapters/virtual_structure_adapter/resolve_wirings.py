from hetdesrun.adapters.exceptions import AdapterHandlingException
from hetdesrun.adapters.virtual_structure_adapter.utils import (
    get_enumerated_ids_of_vst_sources_or_sinks,
    get_virtual_sources_and_sinks_from_structure_service,
)
from hetdesrun.models.adapter_data import RefIdType
from hetdesrun.models.wiring import InputWiring, OutputWiring, WorkflowWiring
from hetdesrun.structure.db.exceptions import DBNotFoundError
from hetdesrun.structure.models import StructureServiceSink, StructureServiceSource


def update_wirings(
    wiring: InputWiring | OutputWiring,
    source_or_sink: StructureServiceSource | StructureServiceSink,
) -> InputWiring | OutputWiring:
    """Replaces vst source or sink info with that of their referenced source or sink.

    Returns:
    - Updated InputWiring or OutputWiring instance.
    """
    # Update adapter_id
    wiring.adapter_id = source_or_sink.adapter_key

    # Update ref_id
    if wiring.type == "metadata(any)":
        wiring.ref_id = source_or_sink.ref_id
        # Update ref_key and ref_id_type
        wiring.ref_key = source_or_sink.ref_key
        wiring.ref_id_type = RefIdType.THINGNODE
    else:
        wiring.ref_id = (
            source_or_sink.source_id
            if isinstance(source_or_sink, StructureServiceSource)
            else source_or_sink.sink_id
        )

    # Merge passed through filters with preset filters
    wiring.filters = wiring.filters | source_or_sink.preset_filters  # type: ignore

    return wiring


def resolve_virtual_structure_wirings(
    workflow_wiring: WorkflowWiring,
) -> None:
    """Resolves vst sources and sinks to their referenced sources and sinks.

    The WorkflowWiring object is modified in place.
    """

    # Retrieve IDs of wirings referencing vst-adapter
    # and keep track of the indices for easier replacement later on
    input_indices_to_be_updated, input_ref_ids = get_enumerated_ids_of_vst_sources_or_sinks(
        workflow_wiring.input_wirings
    )
    output_indices_to_be_updated, output_ref_ids = get_enumerated_ids_of_vst_sources_or_sinks(
        workflow_wiring.output_wirings
    )

    if input_ref_ids or output_ref_ids:
        try:
            virtual_sources, virtual_sinks = get_virtual_sources_and_sinks_from_structure_service(
                input_ref_ids, output_ref_ids
            )
        except DBNotFoundError as e:
            raise AdapterHandlingException(
                "Atleast one source or sink referenced in the wirings was not found "
                f"in the structure service database, during the wiring resolution: {str(e)}"
            ) from e

        # Update input wirings
        for idx, virtual_source in zip(
            input_indices_to_be_updated, virtual_sources.values(), strict=True
        ):
            workflow_wiring.input_wirings[idx] = update_wirings(
                workflow_wiring.input_wirings[idx], virtual_source
            )  # type: ignore

        # Update output wirings
        for idx, virtual_sink in zip(
            output_indices_to_be_updated, virtual_sinks.values(), strict=True
        ):
            workflow_wiring.output_wirings[idx] = update_wirings(
                workflow_wiring.output_wirings[idx], virtual_sink
            )  # type: ignore

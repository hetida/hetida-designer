from collections import defaultdict
from typing import Any

from hetdesrun.adapters import load_data_from_adapter, send_data_with_adapter
from hetdesrun.adapters.virtual_structure_adapter.utils import (
    get_actual_sources_and_sinks_for_virtual_sources_and_sinks,
    get_enumerated_ids_of_vst_sources_or_sinks,
)
from hetdesrun.models.data_selection import FilteredSink, FilteredSource
from hetdesrun.models.wiring import InputWiring, OutputWiring, WorkflowWiring


# TODO Think about it, maybe make this a classmethod for WorkflowWiring or sth
def replace_wirings(
    input_ids: list[tuple[int, str]],
    output_ids: list[tuple[int, str]],
    actual_input_wirings: dict[str, InputWiring],
    actual_output_wirings: dict[str, OutputWiring],
    workflow_wiring: WorkflowWiring,
) -> None:
    for idx, ref_id in input_ids:
        new_input_wiring = actual_input_wirings[ref_id]
        wf_input_name = workflow_wiring.input_wirings[idx].workflow_input_name
        new_input_wiring.workflow_input_name = wf_input_name
        new_input_wiring.filters = (
            new_input_wiring.filters | workflow_wiring.input_wirings[idx].filters
        )
        workflow_wiring.input_wirings[idx] = new_input_wiring

    for idx, ref_id in output_ids:
        new_output_wiring = actual_output_wirings[ref_id]
        wf_output_name = workflow_wiring.output_wirings[idx].workflow_output_name
        new_output_wiring.workflow_output_name = wf_output_name
        new_output_wiring.filters = (
            new_output_wiring.filters | workflow_wiring.output_wirings[idx].filters
        )
        workflow_wiring.output_wirings[idx] = new_output_wiring


# TODO Probably make it async later
def resolve_virtual_structure_wirings(
    workflow_wiring: WorkflowWiring,
) -> None:
    # Retrieve IDs of wirings referencing vst-adapter
    # and keep track of the indices for easier replacement later on
    input_ref_ids = get_enumerated_ids_of_vst_sources_or_sinks(workflow_wiring.input_wirings)
    output_ref_ids = get_enumerated_ids_of_vst_sources_or_sinks(workflow_wiring.output_wirings)

    if input_ref_ids or output_ref_ids:
        actual_input_wirings, actual_output_wirings = (
            get_actual_sources_and_sinks_for_virtual_sources_and_sinks(
                [id_tuple[1] for id_tuple in input_ref_ids],
                [id_tuple[1] for id_tuple in output_ref_ids],
            )
        )

        replace_wirings(
            input_ref_ids,
            output_ref_ids,
            actual_input_wirings,
            actual_output_wirings,
            workflow_wiring,
        )


async def resolve_and_load_data_from_wiring(
    workflow_wiring: WorkflowWiring,
) -> dict[str, Any]:
    """Loads data from sources and provides it as a dict with the workflow input names as keys

    Data is loaded in batches per adapter.
    """

    wirings_by_adapter = defaultdict(list)

    for input_wiring in workflow_wiring.input_wirings:
        if input_wiring.use_default_value is False:
            wirings_by_adapter[input_wiring.adapter_id].append(input_wiring)

    loaded_data = {}

    # data is loaded adapter-wise:
    for adapter_key, input_wirings_of_adapter in wirings_by_adapter.items():
        # call adapter with these wirings / sources
        loaded_data_from_adapter: dict = await load_data_from_adapter(
            adapter_key,
            {
                input_wiring.workflow_input_name: FilteredSource(
                    ref_id=input_wiring.ref_id,
                    ref_id_type=input_wiring.ref_id_type,
                    ref_key=input_wiring.ref_key,
                    type=input_wiring.type,
                    filters=input_wiring.filters,
                )
                for input_wiring in input_wirings_of_adapter
            },
        )

        loaded_data.update(loaded_data_from_adapter)
    return loaded_data


async def resolve_and_send_data_from_wiring(
    workflow_wiring: WorkflowWiring, result_data: dict[str, Any]
) -> dict[str, Any]:
    """Sends data to sinks

    Data that is not send to a sink by the workflow wiring is returned.
    """

    wirings_by_adapter = defaultdict(list)

    for output_wiring in workflow_wiring.output_wirings:
        wirings_by_adapter[output_wiring.adapter_id].append(output_wiring)

    all_data_not_send_by_adapter = {}
    # data is loaded adapter-wise:
    for adapter_key, output_wirings_of_adapter in wirings_by_adapter.items():
        # call adapter with these wirings / sources
        data_not_send_by_adapter: dict[str, Any] | None = await send_data_with_adapter(
            adapter_key,
            {
                output_wiring.workflow_output_name: FilteredSink(
                    ref_id=output_wiring.ref_id,
                    ref_id_type=output_wiring.ref_id_type,
                    ref_key=output_wiring.ref_key,
                    type=output_wiring.type,
                    filters=output_wiring.filters,
                )
                for output_wiring in output_wirings_of_adapter
            },
            result_data,
        )

        if data_not_send_by_adapter is not None:
            all_data_not_send_by_adapter.update(data_not_send_by_adapter)
    return all_data_not_send_by_adapter

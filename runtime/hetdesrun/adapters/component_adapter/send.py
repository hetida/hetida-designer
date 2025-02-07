import asyncio
import logging
from typing import Any

from hetdesrun.adapters.component_adapter.utils import (
    to_component_trafo_rev,
    wf_exec_input_from_component_trafo_revision,
    workflow_wiring_from_sink_filters,
)
from hetdesrun.adapters.exceptions import AdapterHandlingException
from hetdesrun.models.data_selection import FilteredSink
from hetdesrun.runtime.logging import execution_context_filter
from hetdesrun.runtime.service import runtime_service

logger = logging.getLogger(__name__)


async def send_data(
    wf_output_name_to_filtered_sink_mapping_dict: dict[str, FilteredSink],
    wf_output_name_to_value_mapping_dict: dict[str, Any],
    adapter_key: str,  # noqa: ARG001
) -> dict[str, Any]:
    """Send data from component via adapter sinks by executing them with this data

    Send the data to the 'data' input of the sink component. Other inputs are filled
    from filters.
    """

    code_modules = execution_context_filter.get_value("current_code_modules")
    component_revisions = execution_context_filter.get_value("current_components")

    code_modules_by_id = {str(code_module.uuid): code_module for code_module in code_modules}
    component_revisions_by_id = {str(comp_rev.uuid): comp_rev for comp_rev in component_revisions}

    fetch_tasks = {}
    try:
        async with asyncio.TaskGroup() as tg:
            # The await is implicit when the context manager exits.
            for (
                outp_name,
                filtered_component_adapter_snk,
            ) in wf_output_name_to_filtered_sink_mapping_dict.items():
                # obtain component revision and code module
                referenced_component_id = (
                    ref_key
                    if (ref_key := filtered_component_adapter_snk.ref_key) is not None
                    else filtered_component_adapter_snk.ref_id
                )
                if referenced_component_id not in component_revisions_by_id:
                    raise ValueError(f"ComponentRevision {referenced_component_id} NOT PRESENT")

                code_module_uuid = str(
                    component_revisions_by_id[referenced_component_id].code_module_uuid
                )
                if code_module_uuid not in code_modules_by_id:
                    raise ValueError(f"CODE MODULE {code_module_uuid} NOT PRESENT")

                component_rev = component_revisions_by_id[str(referenced_component_id)]

                if len(component_rev.outputs) != 0:
                    raise ValueError(
                        f"Component  {referenced_component_id} used for component adapter as"
                        " sink does itself have outputs. This is not allowed."
                    )

                if len([inp for inp in component_rev.inputs if inp.name == "data"]) != 1:
                    raise ValueError(
                        f"Component {referenced_component_id} used for component adapter as"
                        ' sink does not have exactly one input named "data".'
                    )

                code_module = code_modules_by_id[str(code_module_uuid)]

                component_trafo_rev = to_component_trafo_rev(component_rev, code_module)

                component_rev_inputs_by_name = {inp.name: inp for inp in component_rev.inputs}

                wf_exec_input = wf_exec_input_from_component_trafo_revision(
                    component_trafo_rev,
                    workflow_wiring_from_sink_filters(
                        filtered_component_adapter_snk,
                        value=wf_output_name_to_value_mapping_dict[outp_name],
                        component_rev_inputs_by_name=component_rev_inputs_by_name,
                    ),
                )

                task = tg.create_task(runtime_service(runtime_input=wf_exec_input))
                fetch_tasks[outp_name] = task

        # tasks are awaited when leaving async with context of task group
        # since they are actual task, they get their own execution context etc.
    except Exception as e:
        msg = f"Failed sending data via component adapter. Error was {str(e)}"
        logger.error(msg)
        raise AdapterHandlingException(msg) from e

    # Obtain results:

    results_by_outp_name = {outp_name: task.result() for outp_name, task in fetch_tasks.items()}

    # find errors and raise as adapter handling errors with relevant infos:

    errors_by_outp_name = {
        outp_name: result.error
        for outp_name, result in results_by_outp_name.items()
        if result.error is not None
    }

    if len(errors_by_outp_name) > 0:
        raise AdapterHandlingException(
            "Errors when running components for component adapter wired outputs:\n"
            + str(errors_by_outp_name)
            + "\nfiltered component adapter sinks by output name where:\n"
            + str(
                {
                    outp_name: filtered_sink
                    for outp_name, filtered_sink in (
                        wf_output_name_to_filtered_sink_mapping_dict.items()
                    )
                    if outp_name in errors_by_outp_name
                }
            )
        )

    return {}

import asyncio
import logging
from typing import Any

from hetdesrun.adapters.component_adapter.utils import (
    to_component_trafo_rev,
    wf_exec_input_from_component_trafo_revision,
    workflow_wiring_from_source_filters,
)
from hetdesrun.adapters.exceptions import AdapterHandlingException
from hetdesrun.models.data_selection import FilteredSource
from hetdesrun.models.run import WorkflowExecutionError
from hetdesrun.runtime.logging import execution_context_filter
from hetdesrun.runtime.service import runtime_service

logger = logging.getLogger(__name__)


async def load_data(
    wf_input_name_to_filtered_source_mapping_dict: dict[str, FilteredSource],
    adapter_key: str,  # noqa: ARG001
) -> dict[str, Any]:
    """Load data from component adapter sources by executing them"""

    code_modules = execution_context_filter.get_value("current_code_modules")
    component_revisions = execution_context_filter.get_value("current_components")

    code_modules_by_id = {str(code_module.uuid): code_module for code_module in code_modules}
    component_revisions_by_id = {str(comp_rev.uuid): comp_rev for comp_rev in component_revisions}

    fetch_tasks = {}
    try:
        async with asyncio.TaskGroup() as tg:
            # The await is implicit when the context manager exits.
            for (
                inp_name,
                filtered_component_adapter_src,
            ) in wf_input_name_to_filtered_source_mapping_dict.items():
                # obtain component revision and code module
                referenced_component_id = (
                    ref_key
                    if (ref_key := filtered_component_adapter_src.ref_key) is not None
                    else filtered_component_adapter_src.ref_id
                )
                if referenced_component_id not in component_revisions_by_id:
                    raise ValueError(f"ComponentRevision {referenced_component_id} NOT PRESENT")

                code_module_uuid = str(
                    component_revisions_by_id[referenced_component_id].code_module_uuid
                )
                if code_module_uuid not in code_modules_by_id:
                    raise ValueError(f"CODE MODULE {code_module_uuid} NOT PRESENT")

                component_rev = component_revisions_by_id[str(referenced_component_id)]

                if len(component_rev.outputs) != 1:
                    raise ValueError(
                        "Component used for component adapter as source does "
                        "not have exactly one output"
                    )

                code_module = code_modules_by_id[str(code_module_uuid)]

                component_trafo_rev = to_component_trafo_rev(component_rev, code_module)

                component_rev_inputs_by_name = {inp.name: inp for inp in component_rev.inputs}

                wf_exec_input = wf_exec_input_from_component_trafo_revision(
                    component_trafo_rev,
                    workflow_wiring_from_source_filters(
                        filtered_component_adapter_src, component_rev_inputs_by_name
                    ),
                )

                task = tg.create_task(runtime_service(runtime_input=wf_exec_input))
                fetch_tasks[inp_name] = task

        # tasks are awaited when leaving async with context of task group
        # since they are actual task, they get their own execution context etc.
    except Exception as e:
        msg = f"Failed loading data via component adapter. Error was {str(e)}"
        logger.error(msg)
        raise AdapterHandlingException(msg) from e

    # Obtain results:

    results_by_inp_name = {inp_name: task.result() for inp_name, task in fetch_tasks.items()}

    # find errors and raise as adapter handling errors with relevant infos:

    errors_by_inp_name: dict[str, str | WorkflowExecutionError] = {
        inp_name: result.error
        for inp_name, result in results_by_inp_name.items()
        if result.error is not None
    }

    if len(errors_by_inp_name) > 0:
        raise AdapterHandlingException(
            "Errors when running components for component adapter wired inputs:\n"
            + str(errors_by_inp_name)
            + "\nfiltered component adapter sources by input name where:\n"
            + str(
                {
                    inp_name: filtered_source
                    for inp_name, filtered_source in (
                        wf_input_name_to_filtered_source_mapping_dict.items()
                    )
                    if inp_name in errors_by_inp_name
                }
            )
        )

    # Return by inp_name

    return {
        inp_name: next(iter(result.output_results_by_output_name.values()), None)
        # has exactly one output, this gets this only value of the dict
        for inp_name, result in results_by_inp_name.items()
    }

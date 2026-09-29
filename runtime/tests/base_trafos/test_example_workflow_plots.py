import json

import pytest

from hdutils import DataType
from hetdesrun.exportimport.importing import import_transformations_from_dir
from hetdesrun.models.execution import ExecByIdInput
from hetdesrun.trafoutils.io.load import load_transformation_revisions_from_directory
from hetdesrun.utils import State, Type


@pytest.mark.asyncio
async def test_example_workflows_with_plot_outputs_produce_plots(
    mocked_clean_test_db_session, async_test_client
):
    """Example workflows with plot outputs must run with their test wiring and yield plots

    Most base visualization components have no tests of their own. Running the example
    workflows exercises them with realistic data, which e.g. detects visualization
    components breaking on plotly upgrades.
    """
    import_transformations_from_dir("./transformations", directly_into_db=True)

    trafo_dict, path_dict = load_transformation_revisions_from_directory(
        "./transformations/workflows"
    )
    plot_workflows = [
        trafo
        for trafo in trafo_dict.values()
        if trafo.type is Type.WORKFLOW
        and trafo.state is not State.DISABLED
        and any(outp.data_type is DataType.PlotlyJson for outp in trafo.io_interface.outputs)
    ]

    assert len(plot_workflows) > 5

    failures = []
    async with async_test_client as ac:
        for workflow in plot_workflows:
            exec_input = ExecByIdInput(
                id=workflow.id, wiring=workflow.test_wiring, run_pure_plot_operators=True
            )
            resp = await ac.post(
                "/api/transformations/execute", json=json.loads(exec_input.model_dump_json())
            )
            resp_json = resp.json()

            workflow_info = (
                f"{workflow.name} ({workflow.version_tag}) from {path_dict[workflow.id]}"
            )
            if resp.status_code != 200 or resp_json["error"] is not None:
                failures.append(f"{workflow_info}: {resp.status_code} {resp_json.get('error')}")
                continue

            for output_name, output_type in resp_json["output_types_by_output_name"].items():
                plot = resp_json["output_results_by_output_name"][output_name]
                if output_type == DataType.PlotlyJson and not (
                    isinstance(plot, dict) and len(plot.get("data", [])) > 0
                ):
                    failures.append(f"{workflow_info}: no plot for output {output_name}")

    assert not failures, "Example workflows failed to produce plots:\n" + "\n".join(failures)

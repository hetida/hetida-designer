import pytest

from hetdesrun.models.run import WorkflowExecutionInput
from hetdesrun.runtime.engine.plain.parsing import parse_workflow_input


@pytest.mark.asyncio
async def test_plain_wf_parsing_and_execution(input_json_with_wiring):
    wf_exe_inp = WorkflowExecutionInput.parse_obj(input_json_with_wiring)
    parsed_wf = parse_workflow_input(
        wf_exe_inp.workflow, wf_exe_inp.components, wf_exe_inp.code_modules
    )

    assert len(parsed_wf.sub_nodes) == 3  # (2 operators + 1 constant provider node)

    res = await parsed_wf.result  # workflow execution

    assert "z" in res.keys()
    assert res["z"] == 4.0

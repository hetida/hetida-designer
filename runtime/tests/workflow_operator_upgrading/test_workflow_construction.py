import os

from hetdesrun.trafoutils.trafo_collection import TrafoCollection
from hetdesrun.trafoutils.workflow_construction import WorkflowConstructor


def test_workflow_construction():
    with TrafoCollection() as tc:
        name_series_component = tc.add_from_json_file(
            os.path.join(
                "tests",
                "data",
                "components",
                "name-series_100.json",
            )
        )
        with WorkflowConstructor(tc, autoarrange=True, name="Test WF") as wf:
            op_1 = wf.op(name_series_component)
            op_2 = wf.op(name_series_component)
            assert op_1.operator.id != op_2.operator.id

            wf.link(op_1.o.output, op_2.i.input)

            wf.output("second_op_output", op_2.o.output)
            wf.input("second_str_inp", op_2.i.name)
            wf.input("first_series_inp", op_1.i.input, optional=True, default_value=[1, 2, 3, 67])
            wf.constant(op_1.i.name, value="FIRST NAME")

    assert wf.result
    print(wf.result.json())

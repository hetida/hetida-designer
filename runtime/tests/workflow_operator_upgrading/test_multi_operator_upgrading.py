import os
from uuid import UUID

import pytest

from hetdesrun.trafoutils.trafo_collection import TrafoCollection
from hetdesrun.trafoutils.upgrade_operators import upgrade_operators_in_workflow
from hetdesrun.trafoutils.workflow_construction import WorkflowConstructor


@pytest.fixture
def workflow_upgrade():
    raise NotImplementedError


@pytest.mark.asyncio
async def test_multi_operator_upgrading(mocked_clean_test_db_session):
    with TrafoCollection(save_to_db=True) as tc:
        pt_any = tc.add_from_json_file(
            os.path.join(
                "transformations",
                "components",
                "connectors",
                "pass-through_100_1946d5f8-44a8-724c-176f-16f3e49963af.json",
            )
        )
        pt_series = tc.add_from_json_file(
            os.path.join(
                "transformations",
                "components",
                "connectors",
                "pass-through-series_100_bfa27afc-dea8-b8aa-4b15-94402f0739b6.json",
            )
        )
        pt_string = tc.add_from_json_file(
            os.path.join(
                "transformations",
                "components",
                "connectors",
                "pass-through-string_100_2b1b474f-ddf5-1f4d-fec4-17ef9122112b.json",
            )
        )

        with WorkflowConstructor(
            trafo_collector=tc,
            name="Test Wf",
            version_tag="0.1.0",
            id="3e7c180d-79dd-4416-95f2-185b9e7b36d7",
            auto_release=True,
        ) as wf:
            any_op = wf.op(pt_any, "any_pass_through")
            series_op = wf.op(pt_series, "series_pass_through")
            wf.input("any_in", any_op.i["input"])
            wf.input("series_in", series_op.i["input"])
            wf.output("any_out", any_op.o["output"])
            wf.output("series_out", series_op.o["output"])

        base_workflow = wf.result.copy(deep=True)

        with wf:  # extend Workflow
            wf.id = UUID("82be1fc1-d5cf-4ad2-912e-05baacdaa963")
            wf.version_tag = "0.1.1"
            string_op = wf.op(pt_string, "string_pass_through")
            wf.input("string_in", string_op.i["input"])
            wf.output("string_out", string_op.o["output"])

        upgraded_wf = wf.result.copy(deep=True)

        with WorkflowConstructor(
            trafo_collector=tc,
            name="Wf to upgrade",
            version_tag="0.1.0",
        ) as wf:
            base_1 = wf.op(base_workflow)
            base_2 = wf.op(base_workflow)

            wf.link(base_1.o["series_out"], base_2.i["series_in"])
            wf.link(base_1.o["any_out"], base_2.i["any_in"])

        wf_to_upgrade = wf.result

    upgraded_wf = upgrade_operators_in_workflow(wf_to_upgrade, only_check_deprecated=False)

    occuring_trafos_in_operators = {op.transformation_id for op in upgraded_wf.content.operators}

    # only new version is present:
    assert len(occuring_trafos_in_operators) == 1
    assert UUID("82be1fc1-d5cf-4ad2-912e-05baacdaa963") in occuring_trafos_in_operators

    # links still present:
    assert len(upgraded_wf.content.links) == 2

import json
import logging
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from hdutils import DataType
from hetdesrun.backend.execution import execute_transformation_revision
from hetdesrun.backend.models.info import ExecutionResponseFrontendDto
from hetdesrun.models.execution import ExecByIdBase, ExecByIdInput
from hetdesrun.models.repr_reference import ReproducibilityReference
from hetdesrun.models.run import WorkflowExecutionResult
from hetdesrun.persistence.dbservice.revision import (
    store_single_transformation_revision,
)
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.reference_context import (
    get_deepcopy_of_reproducibility_reference_context,
    get_reproducibility_reference_context,
    set_reproducibility_reference_context,
)


def test_utc_validation():
    with pytest.raises(ValueError, match="The execution start timestamp must be timezone-aware"):
        _ = ReproducibilityReference(
            exec_start_timestamp=datetime.now()  # noqa: DTZ005
        )

    with pytest.raises(ValueError, match="The execution start timestamp must be in UTC"):
        __ = ReproducibilityReference(
            exec_start_timestamp=datetime.now(tz=timezone(timedelta(hours=1)))
        )


def test_context_var_setting_and_getting():
    # Test getter
    assert get_reproducibility_reference_context() == ReproducibilityReference()

    # Test setter
    rr1 = ReproducibilityReference(exec_start_timestamp=datetime(1949, 5, 23, tzinfo=timezone.utc))
    set_reproducibility_reference_context(rr1)
    assert get_reproducibility_reference_context() == rr1

    # Test whether deepcopy getter returns an actual deepcopy
    rr2 = get_deepcopy_of_reproducibility_reference_context()
    assert rr2 == rr1
    assert rr2 is not rr1
    assert rr2.exec_start_timestamp == rr1.exec_start_timestamp


def test_default_factories():
    exec_resp_frontend = ExecutionResponseFrontendDto(
        result="nf",
        output_results_by_output_name={"nf": 23},
        output_types_by_output_name={"nf": DataType.Integer},
        job_id=uuid4(),
    )
    exec_by_id_obj = ExecByIdBase(id=uuid4())
    wf_result = WorkflowExecutionResult(
        result="failure", output_results_by_output_name={"nf": 23}, job_id=uuid4()
    )

    # Check that at points where marshalling is done
    # a (deep) copy is created.
    assert exec_resp_frontend.resolved_reproducibility_references is not None
    assert (
        exec_resp_frontend.resolved_reproducibility_references
        is not get_reproducibility_reference_context()
    )

    assert exec_by_id_obj.resolved_reproducibility_references is not None
    assert (
        exec_by_id_obj.resolved_reproducibility_references
        is not get_reproducibility_reference_context()
    )

    assert wf_result.resolved_reproducibility_references is not None
    assert (
        wf_result.resolved_reproducibility_references is not get_reproducibility_reference_context()
    )


@pytest.fixture()
def _db_with_two_trafos(mocked_clean_test_db_session):
    # Load a regular transformation revision with state RELEASED
    with open(
        "transformations/components/connectors/pass-through-string_100_2b1b474f-ddf5-1f4d-fec4-17ef9122112b.json"
    ) as f:
        trafo_data = json.load(f)
    store_single_transformation_revision(TransformationRevision(**trafo_data))

    # Load a transformation revision to provoke an Error
    with open(
        "tests/data/components/raise-exception_010_c4dbcc42-eaec-4587-a362-ce6567f21d92.json"
    ) as f:
        trafo_data = json.load(f)
    store_single_transformation_revision(TransformationRevision(**trafo_data))


@pytest.mark.asyncio
async def test_for_reference_in_response(_db_with_two_trafos):  # noqa: PT019
    rr = ReproducibilityReference(exec_start_timestamp=datetime(1949, 5, 23, tzinfo=timezone.utc))

    exec_by_id_input = ExecByIdInput(
        id="2b1b474f-ddf5-1f4d-fec4-17ef9122112b",
        wiring={
            "input_wirings": [
                {
                    "adapter_id": "direct_provisioning",
                    "filters": {"value": "Test exec"},
                    "use_default_value": False,
                    "workflow_input_name": "input",
                }
            ],
            "output_wirings": [],
        },
        run_pure_plot_operators=False,
        resolved_reproducibility_references=rr,
    )
    execution_response = await execute_transformation_revision(exec_by_id_input)

    assert execution_response.result == "ok"

    assert get_reproducibility_reference_context() == rr

    assert (
        execution_response.resolved_reproducibility_references
        == get_reproducibility_reference_context()
    )


@pytest.mark.asyncio
async def test_if_reference_in_response_after_exception(
    _db_with_two_trafos,  # noqa: PT019
    caplog,
):
    rr = ReproducibilityReference(exec_start_timestamp=datetime(1949, 5, 23, tzinfo=timezone.utc))

    exec_by_id_input = ExecByIdInput(
        id="c4dbcc42-eaec-4587-a362-ce6567f21d92",
        run_pure_plot_operators=False,
        resolved_reproducibility_references=rr,
    )

    # Execute a transformation revision that should cause a runtime execution error
    with caplog.at_level(logging.INFO):
        execution_response = await execute_transformation_revision(exec_by_id_input)

    # Test whether the execution failed as planned
    assert any(
        record.levelname == "INFO" and "Runtime Execution Error" in record.message
        for record in caplog.records
    )
    assert execution_response.result == "failure"

    assert (
        execution_response.resolved_reproducibility_references
        == get_reproducibility_reference_context()
    )

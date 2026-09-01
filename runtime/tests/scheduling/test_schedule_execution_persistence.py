"""Persistence guards for the scheduling execution result.

Regression coverage for the separated backend/runtime deployment: with a separate runtime the
direct-provisioning outputs are relayed to the backend as raw json bytes (carried on the excluded
``ExecutionResponseFrontendDto.raw_output_results_json`` field) while the model's
``output_results_by_output_name`` stays empty. The schedule result view reads the ``exec_result``
that ``ScheduleExecution.to_orm_model`` stores in the JSON db column, so that dump must materialize
the relayed outputs instead of dropping them.
"""

import json
from uuid import UUID

import msgspec

from hetdesrun.backend.models.info import ExecutionResponseFrontendDto
from hetdesrun.persistence.models.schedule import ScheduledJobState, ScheduleExecution

JOB_ID = "00000000-0000-0000-0000-000000000001"
TR_ID = "00000000-0000-0000-0000-000000000002"
SCHEDULE_ID = "00000000-0000-0000-0000-000000000003"
EXEC_ID = "00000000-0000-0000-0000-000000000004"


def _relayed_dto(raw_outputs: bytes) -> ExecutionResponseFrontendDto:
    """A DTO in the state produced by a *separate* runtime: outputs only as raw json bytes."""
    dto = ExecutionResponseFrontendDto(
        result="ok",
        output_results_by_output_name={},
        output_types_by_output_name={"output": "STRING"},
        job_id=JOB_ID,
        tr_id=TR_ID,
        tr_name="t",
        tr_tag="1.0.0",
    )
    dto.raw_output_results_json = raw_outputs
    return dto


def _schedule_execution(dto: ExecutionResponseFrontendDto) -> ScheduleExecution:
    return ScheduleExecution(
        id=UUID(EXEC_ID),
        schedule_id=UUID(SCHEDULE_ID),
        transformation_id=UUID(TR_ID),
        state=ScheduledJobState.SUCCESS,
        trafo_exec_job_id=UUID(JOB_ID),
        exec_result=dto,
    )


def test_to_orm_model_persists_relayed_direct_provisioning_outputs() -> None:
    dto = _relayed_dto(msgspec.json.encode({"output": "test"}))

    orm_model = _schedule_execution(dto).to_orm_model()

    # The stored result must carry the outputs, not the empty model field.
    assert orm_model.exec_result["output_results_by_output_name"] == {"output": "test"}
    # The db JSON column serializes with json.dumps, which must not choke on the stored value
    # (i.e. no msgspec.Raw placeholder leaked into the storable dict).
    assert json.loads(json.dumps(orm_model.exec_result))["output_results_by_output_name"] == {
        "output": "test"
    }


def test_to_orm_model_same_service_outputs_unchanged() -> None:
    # Same-service deployment: outputs already sit on the model field; storage is unchanged.
    dto = ExecutionResponseFrontendDto(
        result="ok",
        output_results_by_output_name={"output": "test"},
        output_types_by_output_name={"output": "STRING"},
        job_id=JOB_ID,
        tr_id=TR_ID,
        tr_name="t",
        tr_tag="1.0.0",
    )

    orm_model = _schedule_execution(dto).to_orm_model()

    assert orm_model.exec_result["output_results_by_output_name"] == {"output": "test"}

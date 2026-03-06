import datetime
from uuid import UUID

from apscheduler.triggers.cron import CronTrigger
from pydantic import AwareDatetime, BaseModel, Field, ValidationError, computed_field
from sqlalchemy import Row, RowMapping

from hetdesrun.backend.models.info import ExecutionResponseFrontendDto
from hetdesrun.models.execution import ExecByIdInput
from hetdesrun.models.wiring import WorkflowWiring
from hetdesrun.persistence.dbmodels import (
    ScheduleDBModel,
    ScheduledJobState,
    ScheduleExecutionDBModel,
)
from hetdesrun.persistence.dbservice.exceptions import DBIntegrityError
from hetdesrun.utils import State, Type


class Schedule(BaseModel):
    id: UUID
    name: str = Field("New Schedule")
    active: bool = True
    cron_expression: str = Field("*/5 * * * *")
    transformation_id: UUID | None = None
    wiring: WorkflowWiring | None = None

    @computed_field
    def cron_expression_valid(self) -> bool:
        try:
            CronTrigger.from_crontab(self.cron_expression, timezone=datetime.UTC)
            return True
        except ValueError:  # pragma: no cover
            return False

    def to_orm_model(self) -> ScheduleDBModel:
        return ScheduleDBModel(
            id=self.id,
            name=self.name,
            active=self.active,
            cron_expression=self.cron_expression,
            transformation_id=self.transformation_id,
            wiring=self.wiring.model_dump() if self.wiring is not None else None,
        )

    @classmethod
    def from_orm_model(cls, orm_model: ScheduleDBModel) -> "Schedule":
        try:
            return Schedule(
                id=orm_model.id,
                name=orm_model.name,
                active=orm_model.active,
                cron_expression=orm_model.cron_expression,
                transformation_id=orm_model.transformation_id,
                wiring=orm_model.wiring,
            )
        except ValidationError as error:  # pragma: no cover
            msg = (
                f"Could not validate db entry for schedule with id {orm_model.id}. "
                f"Validation error was:\n{str(error)}"
            )
            raise DBIntegrityError(msg) from error


class ScheduledJobInformation(BaseModel):
    state: ScheduledJobState
    schedule_job_id: str
    schedule_name: str
    trafo_exec_job_id: str
    error_message: str | None = None
    exec_result: ExecutionResponseFrontendDto | None = None


class ScheduleExecution(BaseModel):
    id: UUID
    schedule_id: UUID
    last_state_update: AwareDatetime | None = None
    start: AwareDatetime | None = None
    end: AwareDatetime | None = None
    transformation_id: UUID
    transformation_name: str | None = None
    transformation_version_tag: str | None = None
    transformation_type: Type | None = None
    transformation_state: State | None = None
    state: ScheduledJobState
    trafo_exec_job_id: UUID
    exec_input: ExecByIdInput | None = None
    exec_result: ExecutionResponseFrontendDto | None = None
    error_message: str | None = None

    def to_orm_model(self) -> ScheduleExecutionDBModel:
        return ScheduleExecutionDBModel(
            id=self.id,
            schedule_id=self.schedule_id,
            last_state_update=self.last_state_update,
            start=self.start,
            end=self.end,
            transformation_id=self.transformation_id,
            transformation_name=self.transformation_name,
            transformation_version_tag=self.transformation_version_tag,
            transformation_type=self.transformation_type,
            transformation_state=self.transformation_state,
            state=self.state,
            trafo_exec_job_id=self.trafo_exec_job_id,
            exec_input=self.exec_input.model_dump(mode="json") if self.exec_input else None,
            exec_result=self.exec_result.model_dump(mode="json") if self.exec_result else None,
            error_message=self.error_message,
        )

    @classmethod
    def from_orm_model(
        cls, orm_model: RowMapping | Row[tuple[ScheduleExecutionDBModel]] | ScheduleExecutionDBModel
    ) -> "ScheduleExecution":
        try:
            return ScheduleExecution(
                id=orm_model.id,
                schedule_id=orm_model.schedule_id,
                last_state_update=orm_model.last_state_update.replace(tzinfo=datetime.timezone.utc)
                if orm_model.last_state_update is not None
                else None,
                start=orm_model.start.replace(tzinfo=datetime.timezone.utc)
                if orm_model.start is not None
                else None,
                end=orm_model.end.replace(tzinfo=datetime.timezone.utc)
                if orm_model.end is not None
                else None,
                transformation_id=orm_model.transformation_id,
                transformation_name=orm_model.transformation_name,
                transformation_version_tag=orm_model.transformation_version_tag,
                transformation_type=orm_model.transformation_type,
                transformation_state=orm_model.transformation_state,
                state=orm_model.state,
                trafo_exec_job_id=orm_model.trafo_exec_job_id,
                exec_input=orm_model.exec_input if hasattr(orm_model, "exec_input") else None,
                exec_result=orm_model.exec_result if hasattr(orm_model, "exec_result") else None,
                error_message=orm_model.error_message,
            )
        except ValidationError as error:  # pragma: no cover
            msg = (
                f"Could not validate db entry for schedule execution with id {orm_model.id}. "
                f"Validation error was:\n{str(error)}"
            )
            raise DBIntegrityError(msg) from error

import datetime
from enum import StrEnum
from uuid import UUID

from apscheduler.triggers.cron import CronTrigger
from pydantic import BaseModel, Field, ValidationError, computed_field

from hetdesrun.backend.models.info import ExecutionResponseFrontendDto
from hetdesrun.models.wiring import WorkflowWiring
from hetdesrun.persistence.dbmodels import ScheduleDBModel
from hetdesrun.persistence.dbservice.exceptions import DBIntegrityError


class Schedule(BaseModel):
    id: UUID
    name: str = Field("New Schedule")
    active: bool = True
    cron_expression: str = Field("*/5 * * * *")
    transformation_id: UUID | None
    wiring: WorkflowWiring | None

    @computed_field
    def cron_expression_valid(self) -> bool:
        try:
            CronTrigger.from_crontab(self.cron_expression, timezone=datetime.UTC)
            return True
        except ValueError:
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
        except ValidationError as error:
            msg = (
                f"Could not validate db entry for schedule with id {orm_model.id}. "
                f"Validation error was:\n{str(error)}"
            )
            raise DBIntegrityError(msg) from error


class ScheduledJobState(StrEnum):
    STARTED = "STARTED"
    INVOCATION_ERROR = "INVOCATION_ERROR"
    EXECUTION_ERROR = "EXECUTION_ERROR"
    SUCCESS = "SUCCESS"


class ScheduledJobInformation(BaseModel):
    state: ScheduledJobState
    schedule_job_id: str
    schedule_name: str
    trafo_exec_job_id: str
    error_message: str | None = None
    exec_result: ExecutionResponseFrontendDto | None = None

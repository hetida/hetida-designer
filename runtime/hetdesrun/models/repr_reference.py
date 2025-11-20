import datetime

from pydantic import AwareDatetime, BaseModel, Field, field_validator


class ReproducibilityReference(BaseModel):
    exec_start_timestamp: AwareDatetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC),
        description=(
            "UTC-Timestamp referencing the start time of an execution."
            " If not provided this will be calculated once, probably in the backend."
            " This should be used when 'now' is resolved."
        ),
    )

    @field_validator("exec_start_timestamp")
    @classmethod
    def ensure_utc(cls, ts: AwareDatetime) -> AwareDatetime:
        if ts.tzinfo != datetime.timezone.utc:
            raise ValueError("The execution start timestamp must be in UTC")
        return ts

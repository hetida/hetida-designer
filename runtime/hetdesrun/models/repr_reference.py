import datetime

from pydantic import BaseModel, Field, field_validator


class ReproducibilityReference(BaseModel):
    exec_start_timestamp: datetime.datetime | None = Field(
        None, description="UTC-Timestamp referencing the start time of an execution."
    )

    # TODO With Pydantic V2 this can probably be solved using AwareDatetime
    # instead of a custom validator
    @field_validator("exec_start_timestamp")
    @classmethod
    def ensure_utc(cls, ts: datetime.datetime | None) -> datetime.datetime | None:
        if ts is not None:
            if ts.tzinfo is None:
                raise ValueError("The execution start timestamp must be timezone-aware")
            if ts.tzinfo != datetime.timezone.utc:
                raise ValueError("The execution start timestamp must be in UTC")
        return ts

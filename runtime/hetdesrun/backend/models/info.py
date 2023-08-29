from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator

from hetdesrun.backend.service.utils import to_camel
from hetdesrun.datatypes import AdvancedTypesOutputSerializationConfig
from hetdesrun.models.run import AllMeasuredSteps, Trace, WorkflowExecutionError
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.utils import State, Type


class BasicInformation(BaseModel):
    id: UUID = Field(default_factory=uuid4)  # noqa: A003
    group_id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., max_length=60)
    description: str
    category: str = Field(..., max_length=60)
    type: Type  # noqa: A003
    state: State
    tag: str = Field(..., max_length=20)

    @validator("tag")
    def tag_not_latest(cls, tag: str) -> str:
        if tag != "latest":
            return tag
        raise ValueError("'latest' is a tag value for internal use only!")

    class Config:
        alias_generator = to_camel


class DocumentationFrontendDto(BaseModel):
    id: UUID  # noqa: A003
    document: str

    @classmethod
    def from_transformation_revision(
        cls, transformation_revision: TransformationRevision
    ) -> "DocumentationFrontendDto":
        return DocumentationFrontendDto(
            id=transformation_revision.id,
            document=transformation_revision.documentation,
        )


class ExecutionResponseFrontendDto(BaseModel):
    error: WorkflowExecutionError | None
    output_results_by_output_name: dict = {}
    output_types_by_output_name: dict = {}
    result: str
    traceback: str | None
    traces: list[Trace] | None
    job_id: UUID

    measured_steps: AllMeasuredSteps = AllMeasuredSteps()
    process_id: int | None = Field(
        None,
        description=(
            "Process Id (PID) of the process handling the request, "
            "if advanced performance measuring is configured."
        ),
    )

    Config = AdvancedTypesOutputSerializationConfig  # enable Serialization of some advanced types

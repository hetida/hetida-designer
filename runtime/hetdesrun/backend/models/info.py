from collections import deque
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from hetdesrun.backend.service.utils import to_camel
from hetdesrun.datatypes import DataType
from hetdesrun.models.repr_reference import ReproducibilityReference
from hetdesrun.models.run import WorkflowExecutionInfo
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.runtime.logging import SimplifiedLogRecord
from hetdesrun.utils import State, Type
from hetdesrun.webservice.config import get_config


class BasicInformation(BaseModel):
    id: UUID = Field(default_factory=uuid4)  # noqa: A003
    group_id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., max_length=60)
    description: str
    category: str = Field(..., max_length=60)
    type: Type  # noqa: A003
    state: State
    tag: str = Field(..., max_length=20)

    @field_validator("tag")
    @classmethod
    def tag_not_latest(cls, tag: str) -> str:
        if tag != "latest":
            return tag
        raise ValueError("'latest' is a tag value for internal use only!")

    model_config = ConfigDict(alias_generator=to_camel)


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


class ExecutionResponseFrontendDto(WorkflowExecutionInfo):
    result: str
    output_results_by_output_name: dict[str, Any] = {}
    output_types_by_output_name: dict[str, DataType | None] = {}
    resolved_reproducibility_references: ReproducibilityReference = Field(
        default_factory=ReproducibilityReference,
        description="Resolved references to information needed to reproduce an execution result."
        "The provided data can be used to replace data that would usually be produced at runtime.",
    )
    process_id: int | None = Field(
        None,
        description=(
            "Process Id (PID) of the process handling the request, "
            "if advanced performance measuring is configured."
        ),
    )

    gathered_component_code_logs: deque[SimplifiedLogRecord] = deque(
        maxlen=get_config().user_component_code_logs_max_len
    )

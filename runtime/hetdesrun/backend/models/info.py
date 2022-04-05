from uuid import UUID, uuid4
from typing import Optional

# pylint: disable=no-name-in-module
from pydantic import BaseModel, Field, validator

from hetdesrun.utils import State, Type

from hetdesrun.backend.service.utils import to_camel

from hetdesrun.models.wiring import WorkflowWiring

from hetdesrun.persistence.models.transformation import TransformationRevision

from hetdesrun.datatypes import AdvancedTypesOutputSerializationConfig


class BasicInformation(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    group_id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., max_length=60)
    description: str
    category: str = Field(..., max_length=60)
    type: Type
    state: State
    tag: str = Field(..., max_length=20)

    @validator("tag")
    # pylint: disable=no-self-argument,no-self-use
    def tag_not_latest(cls, tag: str) -> str:
        if tag != "latest":
            return tag
        raise ValueError("'latest' is a tag value for internal use only!")

    class Config:
        alias_generator = to_camel


class DocumentationFrontendDto(BaseModel):
    id: UUID
    document: str

    @classmethod
    def from_transformation_revision(
        cls, transformation_revision: TransformationRevision
    ) -> "DocumentationFrontendDto":
        return DocumentationFrontendDto(
            id=transformation_revision.id,
            document=transformation_revision.documentation,
        )


class ExecutionLatestInput(BaseModel):
    """Payload for execute-latest kafka endpoint

    WARNING: Even when this input is not changed, the execution response might change if a new latest
    transformation revision exists.

    WARNING: The inputs and outputs may be different for different revisions. In such a case,
    executing the last revision with the same input as before will not work, but will result in errors.

    The latest transformation will be determined by the released_timestamp of the released revisions
    of the revision group which are stored in the database.

    This transformation will be loaded from the DB and executed with the wiring sent with this payload.
    """

    revision_group_id: UUID
    wiring: WorkflowWiring
    run_pure_plot_operators: bool = Field(
        False, description="Whether pure plot components should be run."
    )


class ExecutionResponseFrontendDto(BaseModel):
    error: Optional[str]
    execution_id: Optional[UUID]
    output_results_by_output_name: dict = {}
    output_types_by_output_name: dict = {}
    response: Optional[str]
    result: str
    traceback: Optional[str]
    job_id: UUID

    Config = AdvancedTypesOutputSerializationConfig  # enable Serialization of some advanced types

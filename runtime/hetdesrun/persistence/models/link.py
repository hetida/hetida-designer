from typing import Self
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator

from hetdesrun.datatypes import DataType
from hetdesrun.models.workflow import WorkflowConnection
from hetdesrun.persistence.models.io import (
    Connector,
    OperatorInput,
    OperatorOutput,
    Position,
    WorkflowContentConstantInput,
    WorkflowContentDynamicInput,
    WorkflowContentOutput,
)


class Vertex(BaseModel):
    """Represents start or end point of a link."""

    operator: UUID | None = None
    connector: Connector = Field(
        ...,
        description=(
            "Full connector including name and data type "
            "instead of only the id to simplify execution of the workflow"
        ),
    )


class Link(BaseModel):
    """Links determine how parameter values are passed through the workflow.

    Note: The data types at both sides must match, i.e. be the same or
    at least one must be of type ANY.
    A link cannot start and end at the same connector.
    """

    id: UUID = Field(default_factory=uuid4)  # noqa: A003
    start: Vertex
    end: Vertex
    path: list[Position] = []

    @field_validator("start")
    @classmethod
    def check_start_connector_has_right_class(cls, start: Vertex) -> Vertex:
        if isinstance(start.connector, OperatorInput | WorkflowContentOutput):
            raise ValueError(
                "Instances of OperatorInput or WorkflowContentOutput "
                "can only be the end connector of a link."
            )
        return start

    @field_validator("end")
    @classmethod
    def check_end_connector_has_right_class(cls, end: Vertex) -> Vertex:
        if isinstance(
            end.connector,
            OperatorOutput | WorkflowContentConstantInput | WorkflowContentDynamicInput,
        ):
            raise ValueError(
                "Instances of OperatorOutput, WorkflowContentConstantInput, or "
                "WorkflowContentDynamicInput can only be the start connector of a link."
            )
        return end

    @model_validator(mode="after")
    def types_match(self) -> Self:
        start: Vertex = self.start
        end: Vertex = self.end

        if not (
            start.connector.data_type == end.connector.data_type  # noqa: PLR1714
            or start.connector.data_type == DataType.Any
            or end.connector.data_type == DataType.Any
        ):
            raise ValueError("data types of both link ends must be the same!")

        return self

    @model_validator(mode="after")
    def no_self_reference(self) -> Self:
        start: Vertex = self.start
        end: Vertex = self.end

        if start.operator == end.operator:
            raise ValueError("Start and end of a connection must differ from each other.")
        return self

    @model_validator(mode="after")
    def no_link_without_operator(self) -> Self:
        start: Vertex = self.start
        end: Vertex = self.end

        if start.operator is None and end.operator is None:
            raise ValueError(
                "Both start and end operator are None, this indicates that "
                "neither link start nor link end are connected to an operator. "
                "Such a link is not allowed."
            )
        return self

    def to_connection(self) -> WorkflowConnection:
        return WorkflowConnection(
            input_in_workflow_id=str(self.start.operator),
            input_name=self.start.connector.name,
            output_in_workflow_id=str(self.end.operator),
            output_name=self.end.connector.name,
        )

    model_config = ConfigDict(validate_assignment=True)

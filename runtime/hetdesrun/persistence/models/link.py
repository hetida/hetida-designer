from uuid import UUID, uuid4

from pydantic import BaseModel, Field, root_validator, validator

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

    operator: UUID | None
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

    @validator("start")
    def check_start_connector_has_right_class(cls, start: Vertex) -> Vertex:
        if isinstance(start.connector, OperatorInput | WorkflowContentOutput):
            raise ValueError(
                "Instances of OperatorInput or WorkflowContentOutput "
                "can only be the end connector of a link."
            )
        return start

    @validator("end")
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

    @root_validator()
    def types_match(cls, values: dict) -> dict:
        try:
            start: Vertex = values["start"]
            end: Vertex = values["end"]
        except KeyError as error:
            raise ValueError(
                "Cannot validate that types of link ends match if any of the attributes "
                "'start', 'end' is missing!"
            ) from error
        if not (
            start.connector.data_type == end.connector.data_type  # noqa: PLR1714
            or start.connector.data_type == DataType.Any
            or end.connector.data_type == DataType.Any
        ):
            raise ValueError("data types of both link ends must be the same!")
        return values

    @root_validator()
    def no_self_reference(cls, values: dict) -> dict:
        try:
            start: Vertex = values["start"]
            end: Vertex = values["end"]
        except KeyError as error:
            raise ValueError(
                "Cannot validate that link is no self reference if any of the attributes "
                "'start', 'end' is missing!"
            ) from error
        if start.operator == end.operator:
            raise ValueError("Start and end of a connection must differ from each other.")
        return values

    @root_validator()
    def no_link_without_operator(cls, values: dict) -> dict:
        try:
            start: Vertex = values["start"]
            end: Vertex = values["end"]
        except KeyError as error:
            raise ValueError(
                "Cannot validate that link is connected to an operator if any of the attributes "
                "'start', 'end' is missing!"
            ) from error
        if start.operator is None and end.operator is None:
            raise ValueError(
                "Both start and end operator are None, this indicates that "
                "neither link start nor link end are connected to an operator. "
                "Such a link is not allowed."
            )
        return values

    def to_connection(self) -> WorkflowConnection:
        return WorkflowConnection(
            input_in_workflow_id=str(self.start.operator),
            input_name=self.start.connector.name,
            output_in_workflow_id=str(self.end.operator),
            output_name=self.end.connector.name,
        )

    class Config:
        validate_assignment = True

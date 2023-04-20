from uuid import UUID, uuid4

from pydantic import BaseModel, Field, root_validator

from hetdesrun.datatypes import DataType
from hetdesrun.models.workflow import WorkflowConnection
from hetdesrun.persistence.models.io import OperatorIO, Position


class Vertex(BaseModel):
    """Represents start or end point of a link."""

    operator: UUID | None
    connector: OperatorIO = Field(
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

    @root_validator()
    def types_match(cls, values: dict) -> dict:
        try:
            start = values["start"]
            end = values["end"]
        except KeyError as e:
            raise ValueError(
                "Cannot validate that types of link ends match if any of the attributes "
                "'start', 'end' is missing!"
            ) from e
        if not (
            start.connector.data_type == end.connector.data_type
            or start.connector.data_type == DataType.Any
            or end.connector.data_type == DataType.Any
        ):
            raise ValueError("data types of both link ends must be the same!")
        return values

    @root_validator()
    def no_self_reference(cls, values: dict) -> dict:
        try:
            start = values["start"]
            end = values["end"]
        except KeyError as e:
            raise ValueError(
                "Cannot validate that link is no self reference if any of the attributes "
                "'start', 'end' is missing!"
            ) from e
        if start.operator == end.operator:
            raise ValueError(
                "Start and end of a connection must differ from each other."
            )
        return values

    def to_connection(self) -> WorkflowConnection:
        return WorkflowConnection(
            input_in_workflow_id=str(self.start.operator),
            input_name=self.start.connector.name,
            output_in_workflow_id=str(self.end.operator),
            output_name=self.end.connector.name,
        )

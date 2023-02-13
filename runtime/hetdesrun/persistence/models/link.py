from typing import List, Optional
from uuid import UUID, uuid4

# pylint: disable=no-name-in-module
from pydantic import BaseModel, Field, root_validator

from hetdesrun.datatypes import DataType
from hetdesrun.models.workflow import WorkflowConnection
from hetdesrun.persistence.models.io import Connector, Position


class Vertex(BaseModel):
    """Represents start or end point of a link."""

    operator: Optional[UUID]
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

    id: UUID = Field(default_factory=uuid4)
    start: Vertex
    end: Vertex
    path: List[Position] = []

    # pylint: disable=no-self-argument
    @root_validator()
    def types_match(cls, values: dict) -> dict:
        try:
            start = values["start"]
        except KeyError as e:
            raise ValueError(
                "Cannot validate that types of link ends match if attribute 'start' is missing"
            ) from e
        try:
            end = values["end"]
        except KeyError as e:
            raise ValueError(
                "Cannot validate that data types of link ends match if attribute 'end' is missing"
            ) from e
        if not (
            start.connector.data_type == end.connector.data_type
            or start.connector.data_type == DataType.Any
            or end.connector.data_type == DataType.Any
        ):
            raise ValueError("data types of both link ends must be the same!")
        return values

    # pylint: disable=no-self-argument
    @root_validator()
    def no_self_reference(cls, values: dict) -> dict:
        if values["start"].operator == values["end"].operator:
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

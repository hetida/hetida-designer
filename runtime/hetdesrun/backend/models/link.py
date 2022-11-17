from typing import List
from uuid import UUID, uuid4

# pylint: disable=no-name-in-module
from pydantic import BaseModel, Field, root_validator

from hetdesrun.backend.models.io import ConnectorFrontendDto
from hetdesrun.backend.service.utils import to_camel
from hetdesrun.persistence.models.link import Link, Point, Vertex


class PointFrontendDto(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    pos_x: int
    pos_y: int

    class Config:
        alias_generator = to_camel


class WorkflowLinkFrontendDto(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    from_operator: UUID
    from_connector: UUID
    to_operator: UUID
    to_connector: UUID
    path: List[PointFrontendDto] = []

    @root_validator()
    # pylint: disable=no-self-argument
    def no_self_reference(cls, values: dict) -> dict:
        if values["to_operator"] == values["from_operator"]:
            raise ValueError(
                "Start and end of a connection must differ from each other."
            )
        return values

    @classmethod
    def from_link(cls, link: Link, workflow_id: UUID) -> "WorkflowLinkFrontendDto":
        return WorkflowLinkFrontendDto(
            id=link.id,
            fromOperator=link.start.operator
            if link.start.operator is not None
            else workflow_id,
            fromConnector=link.start.connector.id,
            toOperator=link.end.operator
            if link.end.operator is not None
            else workflow_id,
            toConnector=link.end.connector.id,
            path=[
                PointFrontendDto(id=point.id, posX=point.x, posY=point.y)
                for point in link.path
            ],
        )

    def to_link(
        self,
        from_connector: ConnectorFrontendDto,
        to_connector: ConnectorFrontendDto,
        workflow_id: UUID,
    ) -> Link:
        return Link(
            id=self.id,
            start=Vertex(
                operator=self.from_operator
                if self.from_operator != workflow_id
                else None,
                connector=from_connector.to_connector(),
            ),
            end=Vertex(
                operator=self.to_operator if self.to_operator != workflow_id else None,
                connector=to_connector.to_connector(),
            ),
            path=[
                Point(id=point.id, x=point.pos_x, y=point.pos_y) for point in self.path
            ],
        )

    class Config:
        alias_generator = to_camel

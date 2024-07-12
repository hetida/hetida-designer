from uuid import UUID, uuid4

from pydantic import BaseModel, Field, root_validator

from hetdesrun.backend.models.io import ConnectorFrontendDto
from hetdesrun.backend.service.utils import to_camel
from hetdesrun.persistence.models.io import Position
from hetdesrun.persistence.models.link import Link, Vertex


class PointFrontendDto(BaseModel):
    id: UUID = Field(default_factory=uuid4)  # noqa: A003
    pos_x: int
    pos_y: int

    class Config:
        alias_generator = to_camel


class WorkflowLinkFrontendDto(BaseModel):
    id: UUID = Field(default_factory=uuid4)  # noqa: A003
    from_operator: UUID
    from_connector: UUID
    to_operator: UUID
    to_connector: UUID
    path: list[PointFrontendDto] = []

    @root_validator()
    def no_self_reference(cls, values: dict) -> dict:
        try:
            to_operator = values["to_operator"]
            from_operator = values["from_operator"]
        except KeyError as e:
            raise ValueError(
                "Cannot check link for self reference if any of the attributes "
                "'to_operators', 'from_operator' is missing!"
            ) from e
        if to_operator == from_operator:
            raise ValueError("Start and end of a connection must differ from each other.")
        return values

    @classmethod
    def from_link(cls, link: Link, workflow_id: UUID) -> "WorkflowLinkFrontendDto":
        return WorkflowLinkFrontendDto(
            id=link.id,
            fromOperator=link.start.operator if link.start.operator is not None else workflow_id,
            fromConnector=link.start.connector.id,
            toOperator=link.end.operator if link.end.operator is not None else workflow_id,
            toConnector=link.end.connector.id,
            path=[PointFrontendDto(posX=position.x, posY=position.y) for position in link.path],
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
                operator=self.from_operator if self.from_operator != workflow_id else None,
                connector=from_connector.to_connector(),
            ),
            end=Vertex(
                operator=self.to_operator if self.to_operator != workflow_id else None,
                connector=to_connector.to_connector(),
            ),
            path=[Position(x=point.pos_x, y=point.pos_y) for point in self.path],
        )

    class Config:
        alias_generator = to_camel

from typing import List
from uuid import UUID

# pylint: disable=no-name-in-module
from pydantic import Field, root_validator

from hetdesrun.utils import State

from hetdesrun.backend.service.utils import to_camel

from hetdesrun.backend.models.info import BasicInformation
from hetdesrun.backend.models.io import ConnectorFrontendDto
from hetdesrun.persistence.models.io import Position
from hetdesrun.persistence.models.operator import Operator


class WorkflowOperatorFrontendDto(BasicInformation):
    transformation_id: UUID = Field(..., alias="itemId")
    inputs: List[ConnectorFrontendDto] = []
    outputs: List[ConnectorFrontendDto] = []
    pos_x: int = 0
    pos_y: int = 0

    @root_validator()
    # pylint: disable=no-self-argument,no-self-use
    def is_not_draft(cls, values: dict) -> dict:
        if values["state"] == State.DRAFT:
            raise ValueError(
                f"Only released components/workflows can be dragged into a workflow! "
                f'Operator with id {values["id"]} of type {values["type"]}'
                f' has state {values["state"]} '
            )
        return values

    def to_operator(self) -> Operator:
        return Operator(
            id=self.id,
            revision_group_id=self.group_id,
            name=self.name,
            description=self.description,
            category=self.category,
            type=self.type,
            state=self.state,
            version_tag=self.tag,
            transformation_id=self.transformation_id,
            inputs=[connector.to_connector() for connector in self.inputs],
            outputs=[connector.to_connector() for connector in self.outputs],
            position=Position(x=self.pos_x, y=self.pos_y),
        )

    @classmethod
    def from_operator(
        cls, operator: Operator, category: str = "Other", description: str = ""
    ) -> "WorkflowOperatorFrontendDto":
        return WorkflowOperatorFrontendDto(
            id=operator.id,
            groupId=operator.revision_group_id,
            name=operator.name,
            description=description,
            category=category,
            type=operator.type,
            state=operator.state,
            tag=operator.version_tag,
            itemId=operator.transformation_id,
            inputs=[
                ConnectorFrontendDto.from_connector(connector)
                for connector in operator.inputs
            ],
            outputs=[
                ConnectorFrontendDto.from_connector(connector)
                for connector in operator.outputs
            ],
            posX=operator.position.x,
            posY=operator.position.y,
        )

    class Config:
        alias_generator = to_camel

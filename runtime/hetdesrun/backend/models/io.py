from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator

from hetdesrun.backend.service.utils import to_camel
from hetdesrun.datatypes import DataType
from hetdesrun.models.util import valid_python_identifier
from hetdesrun.persistence.models.io import (
    IO,
    Connector,
    Position,
    WorkflowContentConstantInput,
    WorkflowContentIO,
)


class WorkflowIoFrontendDto(BaseModel):
    id: UUID = Field(default_factory=uuid4)  # noqa: A003
    name: str | None = None
    pos_x: int = 0
    pos_y: int = 0
    type: DataType  # noqa: A003
    operator: UUID
    connector: UUID
    constant_value: dict | None = None
    constant: bool = False

    @validator("name")
    def name_valid_python_identifier(cls, name: str | None) -> str | None:
        if name is None or name == "":
            return name
        return valid_python_identifier(cls, name)

    def to_workflow_content_io(self, operator_name: str, connector_name: str) -> WorkflowContentIO:
        return WorkflowContentIO(
            id=self.id,
            name=self.name,
            data_type=self.type,
            operator_id=self.operator,
            connector_id=self.connector,
            operator_name=operator_name,
            connector_name=connector_name,
            position=Position(x=self.pos_x, y=self.pos_y),
        )

    def to_constant(self, operator_name: str, connector_name: str) -> WorkflowContentConstantInput:
        return WorkflowContentConstantInput(
            id=self.id,
            data_type=self.type,
            operator_id=self.operator,
            connector_id=self.connector,
            operator_name=operator_name,
            connector_name=connector_name,
            position=Position(x=self.pos_x, y=self.pos_y),
            value=self.constant_value["value"]
            if isinstance(self.constant_value, dict) and "value" in self.constant_value
            else None,
        )

    def to_io(self) -> IO:
        return IO(
            id=self.id,
            name=self.name,
            data_type=self.type,
        )

    @classmethod
    def from_workflow_content_io(
        cls,
        workflow_content_io: WorkflowContentIO,
    ) -> "WorkflowIoFrontendDto":
        return WorkflowIoFrontendDto(
            id=workflow_content_io.id,
            name=workflow_content_io.name,
            posX=workflow_content_io.position.x,
            posY=workflow_content_io.position.y,
            type=workflow_content_io.data_type,
            operator=workflow_content_io.operator_id,
            connector=workflow_content_io.connector_id,
            constant=False,
            constantValue={"value": ""},
        )

    @classmethod
    def from_workflow_content_constant_input(
        cls,
        constant: WorkflowContentConstantInput,
    ) -> "WorkflowIoFrontendDto":
        return WorkflowIoFrontendDto(
            id=constant.id,
            posX=constant.position.x,
            posY=constant.position.y,
            type=constant.data_type,
            operator=constant.operator_id,
            connector=constant.connector_id,
            constant=True,
            constantValue={"value": constant.value},
        )

    class Config:
        alias_generator = to_camel


class ConnectorFrontendDto(BaseModel):
    id: UUID = Field(default_factory=uuid4)  # noqa: A003
    name: str | None
    pos_x: int = 0
    pos_y: int = 0
    type: DataType  # noqa: A003

    @validator("name")
    def name_valid_python_identifier(cls, name: str) -> str:
        if name is None or name == "":
            return name
        return valid_python_identifier(cls, name)

    def to_connector(self) -> Connector:
        return Connector(
            id=self.id,
            name=self.name,
            data_type=self.type,
            position=Position(x=self.pos_x, y=self.pos_y),
        )

    def to_io(self) -> IO:
        return IO(id=self.id, name=self.name, data_type=self.type)

    @classmethod
    def from_connector(cls, connector: Connector) -> "ConnectorFrontendDto":
        return ConnectorFrontendDto(
            id=connector.id,
            name=connector.name,
            posX=connector.position.x,
            posY=connector.position.y,
            type=connector.data_type,
        )

    @classmethod
    def from_io(cls, io: IO, posX: int = 0, posY: int = 0) -> "ConnectorFrontendDto":
        return ConnectorFrontendDto(
            id=io.id,
            name=io.name,
            posX=posX,
            posY=posY,
            type=io.data_type,
        )

    class Config:
        alias_generator = to_camel

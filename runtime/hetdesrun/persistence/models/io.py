from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, root_validator, validator

from hetdesrun.datatypes import DataType
from hetdesrun.models.component import ComponentInput, ComponentOutput
from hetdesrun.models.util import names_unique, valid_python_identifier
from hetdesrun.models.workflow import WorkflowInput, WorkflowOutput


class IO(BaseModel):
    id: UUID = Field(default_factory=uuid4)  # noqa: A003
    name: str | None = Field(
        None,
        description="Must be a valid python identifier because it will be used for computation",
    )
    data_type: DataType

    @validator("name")
    def name_valid_python_identifier(cls, name: str) -> str:
        if name is None or name == "":
            return name
        return valid_python_identifier(cls, name)

    def to_component_output(self) -> ComponentOutput:
        return ComponentOutput(id=self.id, type=self.data_type, name=self.name)


class InputType(str, Enum):
    REQUIRED = "required"
    OPTIONAL = "optional"


class Input(IO):
    type: InputType  # noqa: A003
    value: Any

    @validator("name")
    def name_valid_python_identifier(cls, name: str) -> str:
        if name is None or name == "":
            return name
        return valid_python_identifier(cls, name)

    def to_component_input(self) -> ComponentInput:
        return ComponentInput(id=self.id, type=self.data_type, name=self.name)


class IOInterface(BaseModel):
    """Represents combination of inputs and outputs.

    Note: The names in the list of inputs and outputs must be unique, respectively.
    """

    inputs: list[Input] = []
    outputs: list[IO] = []

    @validator("inputs", "outputs", each_item=False)
    def io_names_unique(cls, ios: list[IO]) -> list[IO]:
        ios_with_name = [io for io in ios if not (io.name is None or io.name == "")]

        names_unique(cls, ios_with_name)

        return ios


class Position(BaseModel):
    x: int
    y: int


class Connector(IO):
    position: Position

    @classmethod
    def from_io(cls, io: IO, pos_x: int = 0, pos_y: int = 0) -> "Connector":
        return Connector(
            id=io.id,
            name=io.name,
            data_type=io.data_type,
            position=Position(x=pos_x, y=pos_y),
        )


class OperatorInputConnector(Input):
    position: Position

    @classmethod
    def from_input(
        cls, io: Input, pos_x: int = 0, pos_y: int = 0
    ) -> "OperatorInputConnector":
        return OperatorInputConnector(
            id=io.id,
            name=io.name,
            data_type=io.data_type,
            position=Position(x=pos_x, y=pos_y),
        )


class IOConnector(IO):
    operator_id: UUID
    connector_id: UUID
    operator_name: str
    connector_name: str
    position: Position = Position(x=0, y=0)

    def to_io(self) -> IO:
        return IO(
            id=self.id,
            name=self.name,
            data_type=self.data_type,
            operator_id=self.operator_id,
            connector_id=self.connector_id,
        )

    def to_connector(self) -> Connector:
        return Connector(
            id=self.id,
            name=self.name,
            data_type=self.data_type,
            position=self.position,
        )

    def to_workflow_output(
        self, operator_id: UUID, connector_name: str
    ) -> WorkflowOutput:
        return WorkflowOutput(
            id=self.id,
            name=self.name,
            type=self.data_type,
            id_of_sub_node=str(operator_id),
            name_in_subnode=connector_name,
        )

    @classmethod
    def from_connector(
        cls, connector: Connector, operator_id: UUID, operator_name: str
    ) -> "IOConnector":
        return IOConnector(
            name=connector.name,
            data_type=connector.data_type,
            operator_id=operator_id,
            connector_id=connector.id,
            operator_name=operator_name,
            connector_name=connector.name,
            position=Position(x=0, y=0),
        )


class InputConnector(Input):
    operator_id: UUID
    connector_id: UUID
    operator_name: str
    connector_name: str
    position: Position = Position(x=0, y=0)

    def to_input(self) -> Input:
        return Input(
            id=self.id,
            name=self.name,
            data_type=self.data_type,
            operator_id=self.operator_id,
            connector_id=self.connector_id,
        )

    def to_operator_input_connector(self) -> OperatorInputConnector:
        return OperatorInputConnector(
            id=self.id,
            name=self.name,
            data_type=self.data_type,
            position=self.position,
        )

    def to_workflow_input(
        self, operator_id: UUID, connector_name: str
    ) -> WorkflowInput:
        return WorkflowInput(
            id=self.id,
            name=self.name,
            type=self.data_type,
            id_of_sub_node=str(operator_id),
            name_in_subnode=connector_name,
            constantValue=None,
            constant=False,
        )

    @classmethod
    def from_operator_input_connector(
        cls, connector: OperatorInputConnector, operator_id: UUID, operator_name: str
    ) -> "InputConnector":
        return InputConnector(
            name=connector.name,
            data_type=connector.data_type,
            operator_id=operator_id,
            connector_id=connector.id,
            operator_name=operator_name,
            connector_name=connector.name,
            position=Position(x=0, y=0),
        )


class Constant(IOConnector):
    """Represents a fixed workflow input value

    Note: The name of the underlying connector must be an empty string.
    """

    # the frontend requires a string for the constant value
    # the runtime will take care of the correct data type before execution
    value: str

    @root_validator()
    def name_none(cls, values: dict) -> dict:
        if not ("name" not in values or values["name"] is None or values["name"] == ""):
            raise ValueError("Constants must have an empty string as name.")
        return values

    def to_operator_input_connector(self) -> OperatorInputConnector:
        return OperatorInputConnector(
            id=self.id, name=self.name, data_type=self.data_type, position=self.position
        )

    def to_workflow_input(
        self, operator_id: UUID, connector_name: str
    ) -> WorkflowInput:
        return WorkflowInput(
            id=self.id,
            name=None,
            type=self.data_type,
            id_of_sub_node=str(operator_id),
            constantValue={"value": self.value},
            constant=True,
            name_in_subnode=connector_name,
        )

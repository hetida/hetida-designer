from typing import Any, List, Optional
from uuid import UUID, uuid4

# pylint: disable=no-name-in-module
from pydantic import BaseModel, Field, validator, root_validator

from hetdesrun.datatypes import DataType, parse_dynamically_single_value

from hetdesrun.models.util import valid_python_identifier
from hetdesrun.models.util import names_unique
from hetdesrun.models.component import ComponentInput, ComponentOutput
from hetdesrun.models.workflow import WorkflowInput, WorkflowOutput


class IO(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: Optional[str] = Field(
        None,
        description="Must be a valid python identifier because it will be used for computation",
    )
    data_type: DataType

    # pylint: disable=no-self-argument,no-self-use
    @validator("name")
    def name_valid_python_identifier(cls, name: str) -> str:
        if name is None or name == "":
            return name
        return valid_python_identifier(cls, name)

    def to_component_input(self) -> ComponentInput:
        return ComponentInput(id=self.id, type=self.data_type, name=self.name)

    def to_component_output(self) -> ComponentOutput:
        return ComponentOutput(id=self.id, type=self.data_type, name=self.name)


class IOInterface(BaseModel):
    """
    The names in the list of inputs and outputs must be unique, respectively
    """

    inputs: List[IO] = []
    outputs: List[IO] = []

    # pylint: disable=no-self-argument,no-self-use
    @validator("inputs", "outputs", each_item=False)
    def io_names_unique(cls, ios: List[IO]) -> List[IO]:
        ios_with_name = [io for io in ios if io.name is not None]

        names_unique(cls, ios_with_name)

        return ios


class Position(BaseModel):
    x: int
    y: int


class Connector(IO):
    position: Position

    def to_io(self) -> IO:
        return IO(id=self.id, name=self.name, data_type=self.data_type)

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
    def from_io(cls, io: IO, pos_x: int = 0, pos_y: int = 0) -> "Connector":
        return Connector(
            id=io.id,
            name=io.name,
            data_type=io.data_type,
            position=Position(x=pos_x, y=pos_y),
        )


class Constant(Connector):
    """
    The name of a constant must be an empty string.
    """

    value: Any

    # pylint: disable=no-self-argument,no-self-use
    @validator("value")
    def parse_value_into_correct_datatype(cls, v: Any, values: dict) -> Any:
        try:
            data_type = values["data_type"]
        except KeyError as e:
            raise ValueError(
                "Missing data_type attribute makes it impossible to parse constant value."
            ) from e

        return parse_dynamically_single_value(v, data_type).value  # type: ignore

    @root_validator()
    def name_none(cls, values: dict) -> dict:
        if not ("name" not in values or values["name"] is None or values["name"] == ""):
            raise ValueError("Constants must have an empty string as name.")
        return values

    def to_connector(self) -> Connector:
        return Connector(
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

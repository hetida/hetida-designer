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
    REQUIRED = "REQUIRED"
    OPTIONAL = "OPTIONAL"


class Input(IO):
    type: InputType = InputType.REQUIRED  # noqa: A003
    value: Any | None = None

    @validator("value")
    def value_set_only_for_optional_input(
        cls, value: Any | None, values: dict
    ) -> Any | None:
        try:
            type = values["type"]  # noqa: A001
        except KeyError as e:
            raise ValueError(
                "Cannot check if value is set correctly if any of the attributes 'type' is missing!"
            ) from e
        if type == InputType.REQUIRED and value is not None:
            raise ValueError(
                f"The value of an input must not be set if its type is '{InputType.REQUIRED}'!"
            )

        return value

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
        """Transform transformation revision output into operator output.

        Needed to transform a component into an operator which can be wrapped into an workflow
        for execution.
        """
        return Connector(
            id=io.id,
            name=io.name,
            data_type=io.data_type,
            position=Position(x=pos_x, y=pos_y),
        )


class OperatorInputConnector(Input):
    position: Position
    exposed: bool = False

    @validator("exposed")
    def required_inputs_exposed(cls, exposed: bool, values: dict) -> bool:
        try:
            type = values["type"]  # noqa: A001
        except KeyError as error:
            raise ValueError(
                "Cannot set 'exposed' to true for required inputs "
                "if the input type is missing!"
            ) from error
        if type == InputType.REQUIRED:
            return True

        return exposed

    def to_connector(self) -> Connector:
        """Transform OperatorInputConnector into Conenctor

        Needed for compatibility with the end Vertex of a Link.
        """
        return Connector(
            id=self.id,
            name=self.name,
            data_type=self.data_type,
            position=self.position,
        )

    @classmethod
    def from_input(
        cls, input: Input, pos_x: int = 0, pos_y: int = 0  # noqa: A002
    ) -> "OperatorInputConnector":
        """Transform transformation revision input into operator input.

        Needed to transform a component into an operator which can be wrapped into an workflow
        for execution.
        """
        return OperatorInputConnector(
            id=input.id,
            name=input.name,
            data_type=input.data_type,
            type=input.type,
            value=input.value,
            position=Position(x=pos_x, y=pos_y),
        )


class IOConnector(IO):
    operator_id: UUID
    connector_id: UUID
    operator_name: str
    connector_name: str
    position: Position = Position(x=0, y=0)

    def to_io(self) -> IO:
        """Transform workflow output into transformation revision output.

        Needed to validate the equality of the outputs of the io_interface of the transformation
        revision and the outputs of the workflow content.
        """
        return IO(
            id=self.id,
            name=self.name,
            data_type=self.data_type,
        )

    def to_connector(self) -> Connector:
        """Transform workflow output into operator IO connector.

        Needed to create links when wrapping a component into a worklfow for execution, and when
        creating links to unnamed outputs during workflow validation.
        """
        return Connector(
            id=self.id,
            name=self.name,
            data_type=self.data_type,
            position=Position(x=0, y=0),
        )

    def to_workflow_output(self) -> WorkflowOutput:
        """Transform workflow output into workflow node output.

        Needed to transform a TransformationRevision into a WorkflowNode.
        """
        return WorkflowOutput(
            id=self.id,
            name=self.name,
            type=self.data_type,
            id_of_sub_node=str(self.operator_id),
            name_in_subnode=self.connector_name,
        )

    @classmethod
    def from_connector(
        cls, connector: Connector, operator_id: UUID, operator_name: str
    ) -> "IOConnector":
        """Transform operator output into workflow output.

        Needed to wrap a component into a workflow for execution.
        """
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
        """Transform workflow input into transformation revision input.

        Needed to validate the equality of the inputs of the io_interface of the transformation
        revision and the inputs of the workflow content.
        """
        return Input(
            id=self.id,
            name=self.name,
            data_type=self.data_type,
            type=self.type,
            value=self.value,
            operator_id=self.operator_id,
            connector_id=self.connector_id,
        )

    def to_connector(self) -> Connector:
        """Transform workflow input into operator IO connector.

        Needed to create links when wrapping a component into a worklfow for execution, and when
        creating links to unnamed inputs during workflow validation.
        """
        return Connector(
            id=self.id,
            name=self.name,
            data_type=self.data_type,
            position=Position(x=0, y=0),
        )

    def to_workflow_input(
        self,
    ) -> WorkflowInput:
        """Transform workflow input into workflow node input.

        Needed to transform a TransformationRevision into a WorkflowNode.
        """
        return WorkflowInput(
            id=self.id,
            name=self.name,
            type=self.data_type,
            id_of_sub_node=str(self.operator_id),
            name_in_subnode=self.connector_name,
            constantValue=None,
            constant=False,
        )

    @classmethod
    def from_operator_input_connector(
        cls,
        operator_input_connector: OperatorInputConnector,
        operator_id: UUID,
        operator_name: str,
    ) -> "InputConnector":
        """Transform operator input into workflow input.

        Needed to wrap a component into a workflow for execution.
        """
        return InputConnector(
            name=operator_input_connector.name,
            data_type=operator_input_connector.data_type,
            type=operator_input_connector.type,
            value=operator_input_connector.value,
            operator_id=operator_id,
            connector_id=operator_input_connector.id,
            operator_name=operator_name,
            connector_name=operator_input_connector.name,
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

    def to_workflow_input(self) -> WorkflowInput:
        """Transform constant workflow input into workflow node input.

        Needed to transform a TransformationRevision into a WorkflowNode.
        """
        return WorkflowInput(
            id=self.id,
            name=None,
            type=self.data_type,
            id_of_sub_node=str(self.operator_id),
            constantValue={"value": self.value},
            constant=True,
            name_in_subnode=self.connector_name,
        )

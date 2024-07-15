from enum import StrEnum
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


class TransformationOutput(IO):
    def to_component_output(self) -> ComponentOutput:
        return ComponentOutput(id=self.id, type=self.data_type, name=self.name)


class InputType(StrEnum):
    REQUIRED = "REQUIRED"
    OPTIONAL = "OPTIONAL"


class InputTypeMixIn(BaseModel):
    """MixIn for input classes.

    The InputTypeMixIn provides the additional attributes required for inputs to differentiate
    between optional inputs with default value and required inputs.
    Furthermore, it validates that no default value is set for required inputs.
    """

    type: InputType = InputType.REQUIRED  # noqa: A003
    value: Any | None = None

    @validator("value")
    def value_set_only_for_optional_input(cls, value: Any | None, values: dict) -> Any | None:
        try:
            type = values["type"]  # noqa: A001
        except KeyError as error:
            raise ValueError(
                "Cannot check if value is set correctly if any of the attributes 'type' is missing!"
            ) from error
        if type == InputType.REQUIRED and value is not None:
            raise ValueError(
                f"The value of an input must not be set if its type is '{InputType.REQUIRED}'!"
            )

        return value


class TransformationInput(InputTypeMixIn, IO):
    def to_component_input(self) -> ComponentInput:
        return ComponentInput(
            id=self.id,
            type=self.data_type,
            name=self.name,
            default=bool(self.type == InputType.OPTIONAL),
            default_value=self.value,
        )


class IOInterface(BaseModel):
    """Represents combination of inputs and outputs.

    Note: The names in the list of inputs and outputs must be unique, respectively.
    """

    inputs: list[TransformationInput] = []
    outputs: list[TransformationOutput] = []

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

    def matches_connector(self, other: "Connector") -> bool:
        return (
            self.id == other.id
            and self.name == other.name
            and self.data_type == other.data_type
            and self.position.x == other.position.x
            and self.position.y == other.position.y
        )

    def matches_io(self, other: IO) -> bool:
        return self.id == other.id and self.name == other.name and self.data_type == other.data_type


class OperatorOutput(Connector):
    @classmethod
    def from_transformation_output(
        cls, transformation_output: TransformationOutput, pos_x: int = 0, pos_y: int = 0
    ) -> "OperatorOutput":
        """Transform transformation revision output into operator output.

        Needed to transform a component into an operator which can be wrapped into an workflow
        for execution.
        """
        return OperatorOutput(
            id=transformation_output.id,
            name=transformation_output.name,
            data_type=transformation_output.data_type,
            position=Position(x=pos_x, y=pos_y),
        )


class OperatorInput(InputTypeMixIn, Connector):
    exposed: bool = False

    @validator("exposed", always=True)
    def required_inputs_exposed(cls, exposed: bool, values: dict) -> bool:
        try:
            type = values["type"]  # noqa: A001
        except KeyError as error:
            raise ValueError(
                "Cannot set 'exposed' to true for required inputs " "if the input type is missing!"
            ) from error
        if type == InputType.REQUIRED:
            return True

        return exposed

    @classmethod
    def from_transformation_input(
        cls,
        input: TransformationInput,  # noqa: A002
        pos_x: int = 0,
        pos_y: int = 0,
    ) -> "OperatorInput":
        """Transform transformation revision input into operator input.

        Needed to transform a component into an operator which can be wrapped into an workflow
        for execution.
        """
        return OperatorInput(
            id=input.id,
            name=input.name,
            data_type=input.data_type,
            type=input.type,
            value=input.value,
            position=Position(x=pos_x, y=pos_y),
            exposed=True,
        )


class WorkflowContentIO(Connector):
    """Represents in- and outputs of WorkflowContent.

    The attribute id inherited from IO will be used in a link connecting this in- or output to an
    operator.
    """

    operator_id: UUID = Field(
        ..., description="Id of the operator to which this IOConnector is connected"
    )
    connector_id: UUID = Field(
        ...,
        description="Id of the connector of the operator to which this IOConnector is connected",
    )
    operator_name: str = Field(
        ...,
        description=(
            "Name of the operator to which this IOConnector is connected. "
            "Is displayed in the IO dialog."
        ),
    )  # not needed in FE/BE/RT, kept for readability of jsons only
    connector_name: str = Field(
        ...,
        description=(
            "Name of the connector of the operator to which this IOConnector is connected. "
            "Is displayed in the IO dialog."
        ),
    )
    position: Position = Field(Position(x=0, y=0), description="Position of this IOConnector")

    def matches_operator_io(self, other: Connector) -> bool:
        return self.connector_id == other.id and (
            self.data_type == DataType.Any  # noqa: PLR1714
            or other.data_type == DataType.Any
            or self.data_type == other.data_type
        )


class WorkflowContentOutput(WorkflowContentIO):
    def matches_trafo_output(self, other: TransformationOutput) -> bool:
        return self.id == other.id and self.name == other.name and self.data_type == other.data_type

    def to_transformation_output(self) -> TransformationOutput:
        """Transform workflow output into transformation revision output.

        Needed to add missing puts to the io_interface of the transformation
        revision and wrap a component into a workflow for execution.
        """
        return TransformationOutput(
            id=self.id,
            name=self.name,
            data_type=self.data_type,
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
    def from_operator_output(
        cls, operator_output: OperatorOutput, operator_id: UUID, operator_name: str
    ) -> "WorkflowContentOutput":
        """Transform operator output into workflow output.

        Needed to wrap a component into a workflow for execution.
        """
        return WorkflowContentOutput(
            name=operator_output.name,
            data_type=operator_output.data_type,
            operator_id=operator_id,
            connector_id=operator_output.id,
            operator_name=operator_name,
            connector_name=operator_output.name,
            position=Position(x=0, y=0),
        )


class WorkflowContentDynamicInput(InputTypeMixIn, WorkflowContentIO):
    def matches_trafo_input(self, other: TransformationInput) -> bool:
        return (
            self.id == other.id
            and self.name == other.name
            and self.data_type == other.data_type
            and self.type == other.type
            and self.value == other.value
        )

    def to_transformation_input(self) -> TransformationInput:
        """Transform workflow input into transformation revision input.

        Needed to add missing inputs to the io_interface of the transformation
        revision and wrap a component into a workflow for execution.
        """
        return TransformationInput(
            id=self.id,
            name=self.name,
            data_type=self.data_type,
            type=self.type,
            value=self.value,
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
            default_value=self.value,
            default=bool(self.type == InputType.OPTIONAL),
        )

    @classmethod
    def from_operator_input(
        cls,
        operator_input: OperatorInput,
        operator_id: UUID,
        operator_name: str,
    ) -> "WorkflowContentDynamicInput":
        """Transform operator input into workflow input.

        Needed to wrap a component into a workflow for execution.
        """
        return WorkflowContentDynamicInput(
            name=operator_input.name,
            data_type=operator_input.data_type,
            type=operator_input.type,
            value=operator_input.value,
            operator_id=operator_id,
            connector_id=operator_input.id,
            operator_name=operator_name,
            connector_name=operator_input.name,
            position=Position(x=0, y=0),
        )


class WorkflowContentConstantInput(WorkflowContentIO):
    """Represents a fixed workflow input value

    Note: The name of the underlying connector must be an empty string.
    """

    # the frontend requires a string for the constant value
    # the runtime will take care of the correct data type before execution
    value: str = Field(..., description="Value of the Constant")

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

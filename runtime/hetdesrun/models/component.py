from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, validator

from hetdesrun.datatypes import DataType
from hetdesrun.models.base import AbstractNode
from hetdesrun.models.util import names_unique, valid_python_identifier


class UnnamedInput(BaseModel):
    """Base class for representing an input of a Component or a Workflow

    Note that this base class has no name attribute, since name can be null for
    workflow inputs which are constant, while name is mandatory for component inputs
    since there the name is the mean through which the input is mapped to a function parameter.
    """

    id: UUID  # noqa: A003
    type: DataType = Field(  # noqa: A003
        ...,
        description="one of " + ", ".join(['"' + x + '"' for x in list(DataType)]),
        example=DataType.Float,
    )


class ComponentInput(UnnamedInput):
    """Component Input

    Represents an input of a Component.
    """

    name: str = Field(..., example="x", description="must be a valid Python identifier")
    default: bool = Field(False, description="Whether this input has a default value")
    default_value: Any = Field(
        None,
        description=("The default value for this input if default is True."),
    )

    @validator("name")
    def name_valid_python_identifier(cls, name: str) -> str:
        return valid_python_identifier(cls, name)


class ComponentOutput(BaseModel):
    id: UUID  # noqa: A003

    name: str = Field(..., example="z", description="must be a valid Python identifier")
    type: DataType = Field(  # noqa: A003
        ...,
        description="one of " + ", ".join(['"' + x + '"' for x in list(DataType)]),
        example=DataType.Integer,
    )

    @validator("name")
    def name_valid_python_identifier(cls, name: str) -> str:
        return valid_python_identifier(cls, name)


class ComponentRevision(BaseModel):
    """Runtime representation of a component revision"""

    uuid: UUID
    name: str | None = Field(None, description="component name")
    tag: str
    code_module_uuid: UUID = Field(
        ...,
        description=(
            "Reference to the code module in which the components entrypoint function"
            " can be found."
        ),
    )
    function_name: str = Field(
        ...,
        example="main",
        title="Entry point function name",
        description="The name of the function in the provided code module"
        "which is the entrypoint for this component",
    )

    inputs: list[ComponentInput]
    outputs: list[ComponentOutput]

    @validator("function_name")
    def function_name_valid_python_identifier(cls, function_name: str) -> str:
        return valid_python_identifier(cls, function_name)

    @validator("inputs", each_item=False)
    def input_names_unique(cls, inputs: list[ComponentInput]) -> list[ComponentInput]:
        return names_unique(cls, inputs)

    @validator("outputs", each_item=False)
    def output_names_unique(cls, outputs: list[ComponentOutput]) -> list[ComponentOutput]:
        return names_unique(cls, outputs)


class ComponentNode(AbstractNode):
    component_uuid: str  # ref to the component
    name: str | None = Field(None, description="component node name")

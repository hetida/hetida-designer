from typing import Any, Union

from pydantic import BaseModel, Field, ValidationInfo, field_validator

from hetdesrun.models.base import AbstractNode
from hetdesrun.models.component import ComponentNode, ComponentOutput, UnnamedInput
from hetdesrun.models.util import valid_python_identifier


class WorkflowInput(UnnamedInput):
    name: str | None = Field(
        None,
        examples=["x"],
        description="Must be a valid Python identifier. Can be None if constant data is provided.",
    )
    id_of_sub_node: str = Field(
        ..., description="reference to the subnode of which the input is exposed"
    )
    constantValue: Any = Field(
        None,
        description=(
            "The constant value for this input if constant is True."
            """ in form of a single entry dictionary {"value": foo}"""
        ),
    )
    default_value: Any = Field(
        None,
        description=("The default value for this input if default is True."),
    )
    constant: bool = Field(
        False, description="Whether this input should be fed with a constant value"
    )
    default: bool = Field(False, description="Whether this input has a default value")
    name_in_subnode: str

    @field_validator("name")
    @classmethod
    def name_valid_python_identifier(cls, name: str | None) -> str | None:
        if name is None:
            return name
        return valid_python_identifier(cls, name)

    @field_validator("constant")
    @classmethod
    def name_or_constant_data_provided(  # type: ignore
        cls,
        v,
        info: ValidationInfo,
        **kwargs,  # noqa: ARG003
    ):
        if info.data["name"] is None and ((not v) or info.data["constantValue"] is None):
            raise ValueError("Either name or constant data must be provided for Workflow input.")

        if info.data["name"] is not None and v:
            raise ValueError("If name is specified constant must be false.")

        return v


class WorkflowOutput(ComponentOutput):
    id_of_sub_node: str = Field(
        ..., description="reference to the subnode of which the output is exposed"
    )
    name_in_subnode: str


class WorkflowConnection(BaseModel):
    input_in_workflow_id: str
    input_name: str
    output_in_workflow_id: str
    output_name: str


class WorkflowNode(AbstractNode):
    sub_nodes: list[Union["WorkflowNode", ComponentNode]] = Field(
        ..., examples=[[ComponentNode(component_uuid="1234", id="1000")]]
    )
    connections: list[WorkflowConnection]
    inputs: list[WorkflowInput]
    outputs: list[WorkflowOutput]
    name: str | None = Field(None, description="workflow node name")
    tr_id: str
    tr_name: str
    tr_tag: str


WorkflowNode.update_forward_refs()

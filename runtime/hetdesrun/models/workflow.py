from typing import Optional, Any, List, Union

from pydantic import BaseModel, Field, validator  # pylint: disable=no-name-in-module

from hetdesrun.models.component import UnnamedInput, ComponentOutput, ComponentNode
from hetdesrun.models.base import AbstractNode
from hetdesrun.models.util import valid_python_identifier


class WorkflowInput(UnnamedInput):
    name: Optional[str] = Field(
        None,
        example="x",
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
    constant: bool = Field(
        False, description="Whether this input should be fed with a constant value"
    )
    name_in_subnode: str

    # pylint: disable=no-self-argument,no-self-use
    @validator("name", always=True)
    def name_valid_python_identifier(cls, name: Optional[str]) -> Optional[str]:
        if name is None:
            return name
        return valid_python_identifier(cls, name)

    # pylint: disable=no-self-argument,no-self-use,unused-argument
    @validator("constant", always=True)
    def name_or_constant_data_provided(cls, v, values, **kwargs):  # type: ignore
        if values["name"] is None and ((not v) or values["constantValue"] is None):
            raise ValueError(
                "Either name or constant data must be provided for Workflow input."
            )

        if values["name"] is not None and v:
            raise ValueError("If name is specified constant must be false.")

        return v


class WorkflowOutput(ComponentOutput):
    id_of_sub_node: str = Field(
        ..., description="reference to the subnode of which the output is exposed"
    )
    name_in_subnode: str


class WorkflowConnection(BaseModel):
    input_in_workflow_id: str
    # input_id: UUID
    input_name: str
    output_in_workflow_id: str
    # output_id: UUID
    output_name: str


class WorkflowNode(AbstractNode):
    sub_nodes: List[Union["WorkflowNode", ComponentNode]] = Field(
        ..., example=[ComponentNode(component_uuid="1234", id="1000")]
    )
    connections: List[WorkflowConnection]
    inputs: List[WorkflowInput]
    outputs: List[WorkflowOutput]
    name: Optional[str] = Field(None, description="workflow node name")


WorkflowNode.update_forward_refs()

from typing import List, Union, Optional
from pydantic import BaseModel, Field, validator  # pylint: disable=no-name-in-module


from hetdesrun.models.util import valid_python_identifier

from hetdesrun.adapters import SOURCE_ADAPTERS, SINK_ADAPTERS


class OutputWiring(BaseModel):
    workflow_output_name: str = Field(..., alias="workflow_output_name")
    adapter_id: Union[int, str] = Field(..., alias="adapter_id")
    sink_id: Optional[str] = Field(None)

    # pylint: disable=no-self-argument,no-self-use
    @validator("adapter_id")
    def adapter_id_known(cls, v: Union[int, str]) -> Union[int, str]:
        if not v in SINK_ADAPTERS.keys():
            raise ValueError(
                f"Adapter with id {str(v)} is not known / not registered as sink adapter."
            )
        return v

    # pylint: disable=no-self-argument,no-self-use
    @validator("workflow_output_name")
    def name_valid_python_identifier(cls, workflow_output_name: str) -> str:
        return valid_python_identifier(cls, workflow_output_name)


class InputWiring(BaseModel):
    workflow_input_name: str = Field(..., alias="workflow_input_name")
    adapter_id: Union[int, str] = Field(..., alias="adapter_id")
    source_id: Optional[str] = Field(None)
    filters: dict

    # pylint: disable=no-self-argument,no-self-use
    @validator("adapter_id")
    def adapter_id_known(cls, v: Union[int, str]) -> Union[int, str]:
        if not v in SOURCE_ADAPTERS.keys():
            raise ValueError(
                f"Adapter with id {str(v)} is not known / not registered as source adapter."
            )
        return v

    # pylint: disable=no-self-argument,no-self-use
    @validator("workflow_input_name")
    def name_valid_python_identifier(cls, workflow_input_name: str) -> str:
        return valid_python_identifier(cls, workflow_input_name)


class WorkflowWiring(BaseModel):
    input_wirings: List[InputWiring]
    output_wirings: List[OutputWiring]

    # pylint: disable=no-self-argument,no-self-use
    @validator("input_wirings", each_item=False)
    def input_names_unique(cls, input_wirings: List[InputWiring]) -> List[InputWiring]:
        if len(set(iw.workflow_input_name for iw in input_wirings)) == len(
            input_wirings
        ):
            return input_wirings
        raise ValueError(
            "Duplicates in workflow input names occuring in the input wirings not allowed."
        )

    # pylint: disable=no-self-argument,no-self-use
    @validator("output_wirings", each_item=False)
    def output_names_unique(
        cls, output_wirings: List[OutputWiring]
    ) -> List[OutputWiring]:
        if len(set(ow.workflow_output_name for ow in output_wirings)) == len(
            output_wirings
        ):
            return output_wirings
        raise ValueError(
            "Duplicates in workflow output names occuring in the output wirings not allowed."
        )

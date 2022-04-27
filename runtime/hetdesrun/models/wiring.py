from typing import List, Union, Optional
from pydantic import (  # pylint: disable=no-name-in-module
    BaseModel,
    Field,
    validator,
    StrictStr,
    StrictInt,
)


from hetdesrun.models.util import valid_python_identifier

from hetdesrun.adapters import SOURCE_ADAPTERS, SINK_ADAPTERS

from hetdesrun.adapters.generic_rest.external_types import ExternalType, GeneralType
from hetdesrun.models.adapter_data import RefIdType

EXPORT_MODE = False


class OutputWiring(BaseModel):
    workflow_output_name: str = Field(..., alias="workflow_output_name")
    adapter_id: Union[StrictInt, StrictStr] = Field(..., alias="adapter_id")
    ref_id: Optional[str] = Field(
        None,
        description=(
            "Id referencing the sink in external systems."
            " Not necessary for direct provisioning."
        ),
    )
    ref_id_type: Optional[RefIdType] = Field(
        None,
        description="Required if type is specified and is a metadata type. "
        "Then describes to what kind of object in the tree the metadatum is attached. "
        "Must then be one of "
        ", ".join(['"' + x.value + '"' for x in list(RefIdType)]),
    )
    ref_key: Optional[str] = Field(
        None,
        description="Required if type is specified and is a metadata type. "
        "Then is the key of the metdatum.",
    )
    type: Optional[ExternalType] = Field(
        None,
        description="Type of data. If present then must be one of "
        + ", ".join(['"' + x.value + '"' for x in list(ExternalType)]),
    )

    # pylint: disable=no-self-argument,no-self-use
    @validator("adapter_id")
    def adapter_id_known(
        cls, v: Union[StrictInt, StrictStr]
    ) -> Union[StrictInt, StrictStr]:
        # pylint: disable=consider-iterating-dictionary
        if not EXPORT_MODE and (
            not v in SINK_ADAPTERS.keys() and not isinstance(v, str)
        ):
            raise ValueError(
                f"Adapter with id {str(v)} is not known / not registered as sink adapter."
            )
        return v

    # pylint: disable=no-self-argument,no-self-use
    @validator("workflow_output_name")
    def name_valid_python_identifier(cls, workflow_output_name: str) -> str:
        return valid_python_identifier(cls, workflow_output_name)

    # pylint: disable=no-self-argument,no-self-use
    @validator("type")
    def metadata_type_includes_additional_fields(
        cls, v: Optional[ExternalType], values: dict
    ) -> Optional[ExternalType]:
        if v is not None and (GeneralType(v.general_type) == GeneralType.METADATA):
            if values["ref_id_type"] is None or values["ref_key"] is None:
                raise ValueError(
                    "metadata datatype in OutputWiring requires additional fields "
                    '"ref_id_type" and "ref_key". At least one of them is missing.'
                )
        return v


class InputWiring(BaseModel):
    workflow_input_name: str = Field(..., alias="workflow_input_name")
    adapter_id: Union[StrictInt, StrictStr] = Field(..., alias="adapter_id")

    ref_id: Optional[str] = Field(
        None,
        description=(
            "Id referencing the source in external systems."
            " Not necessary for direct provisioning."
        ),
    )
    ref_id_type: Optional[RefIdType] = Field(
        None,
        description="Required if type is specified and is a metadata type. "
        "Then describes to what kind of object in the tree the metadatum is attached. "
        "Must then be one of "
        ", ".join(['"' + x.value + '"' for x in list(RefIdType)]),
    )
    ref_key: Optional[str] = None
    type: Optional[ExternalType] = Field(
        None,
        description="Type of data. If present then must be one of "
        + ", ".join(['"' + x.value + '"' for x in list(ExternalType)]),
    )
    filters: dict = {}

    # pylint: disable=no-self-argument,no-self-use
    @validator("adapter_id")
    def adapter_id_known(
        cls, v: Union[StrictInt, StrictStr]
    ) -> Union[StrictInt, StrictStr]:
        # pylint: disable=consider-iterating-dictionary
        if not EXPORT_MODE and (
            not v in SOURCE_ADAPTERS.keys() and not isinstance(v, str)
        ):
            raise ValueError(
                f"Adapter with id {str(v)} is not known / not registered as source adapter."
            )
        return v

    # pylint: disable=no-self-argument,no-self-use
    @validator("workflow_input_name")
    def name_valid_python_identifier(cls, workflow_input_name: str) -> str:
        return valid_python_identifier(cls, workflow_input_name)

    # pylint: disable=no-self-argument,no-self-use
    @validator("type")
    def metadata_type_includes_additional_fields(
        cls, v: Optional[ExternalType], values: dict
    ) -> Optional[ExternalType]:
        if v is not None and (GeneralType(v.general_type) == GeneralType.METADATA):
            if values["ref_id_type"] is None or values["ref_key"] is None:
                raise ValueError(
                    "metadata datatype in InputWiring requires additional fields "
                    '"ref_id_type" and "ref_key". At least one of them is missing.'
                )
        return v


class WorkflowWiring(BaseModel):
    input_wirings: List[InputWiring] = []
    output_wirings: List[OutputWiring] = []

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

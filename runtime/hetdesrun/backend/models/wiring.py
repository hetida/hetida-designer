from uuid import UUID, uuid4

from pydantic import BaseModel, Field, StrictInt, StrictStr, validator

from hetdesrun.adapters import SINK_ADAPTERS, SOURCE_ADAPTERS
from hetdesrun.adapters.generic_rest.external_types import ExternalType, GeneralType
from hetdesrun.backend.service.utils import to_camel
from hetdesrun.models.adapter_data import RefIdType
from hetdesrun.models.util import valid_python_identifier
from hetdesrun.models.wiring import InputWiring, OutputWiring, WorkflowWiring

ALLOW_UNCONFIGURED_ADAPTER_IDS_IN_WIRINGS = False


class IoWiringFrontendDto(BaseModel):
    id: UUID = Field(default_factory=uuid4)  # noqa: A003
    ref_id: str | None = None
    ref_id_type: RefIdType | None = None
    ref_key: str | None = None
    type: ExternalType | None = None  # noqa: A003

    @validator("type")
    def metadata_type_includes_additional_fields(
        cls, v: ExternalType | None, values: dict
    ) -> ExternalType | None:
        try:
            ref_id_type = values["ref_id_type"]
            ref_key = values["ref_key"]
        except KeyError as e:
            raise ValueError(
                "Cannot check if metadata type includes additional fields if any of the attributes "
                "'ref_id_type', 'ref_key' is missing!"
            ) from e
        if (
            (v is not None)
            and (GeneralType(v.general_type) == GeneralType.METADATA)
            and (ref_id_type is None or ref_key is None)
        ):
            raise ValueError(
                "metadata datatype in OutputWiring requires additional fields "
                '"ref_id_type" and "ref_key". At least one of them is missing.'
            )
        return v

    class Config:
        alias_generator = to_camel


class OutputWiringFrontendDto(IoWiringFrontendDto):
    workflow_output_name: str
    adapter_id: StrictInt | StrictStr

    @validator("workflow_output_name")
    def name_valid_python_identifier(cls, workflow_output_name: str) -> str:
        return valid_python_identifier(cls, workflow_output_name)

    @validator("adapter_id")
    def adapter_id_known(cls, v: StrictInt | StrictStr) -> StrictInt | StrictStr:
        if not ALLOW_UNCONFIGURED_ADAPTER_IDS_IN_WIRINGS and (
            not v in SINK_ADAPTERS and not isinstance(v, str)
        ):
            raise ValueError(
                f"Adapter with id {str(v)} is not known / not registered as sink adapter."
            )
        return v

    def to_output_wiring(self) -> OutputWiring:
        return OutputWiring(
            ref_id=self.ref_id,
            ref_id_type=self.ref_id_type,
            ref_key=self.ref_key,
            type=self.type,
            workflow_output_name=self.workflow_output_name,
            adapter_id=self.adapter_id,
        )

    @classmethod
    def from_output_wiring(cls, output_wiring: OutputWiring) -> "OutputWiringFrontendDto":
        return OutputWiringFrontendDto(
            refId=output_wiring.ref_id,
            refIdType=output_wiring.ref_id_type,
            refKey=output_wiring.ref_key,
            type=output_wiring.type,
            workflowOutputName=output_wiring.workflow_output_name,
            adapterId=output_wiring.adapter_id,
        )

    class Config:
        alias_generator = to_camel


class InputWiringFrontendDto(IoWiringFrontendDto):
    workflow_input_name: str
    adapter_id: StrictInt | StrictStr
    filters: dict = {}
    value: str | None = None

    @validator("workflow_input_name")
    def name_valid_python_identifier(cls, workflow_input_name: str) -> str:
        return valid_python_identifier(cls, workflow_input_name)

    @validator("adapter_id")
    def adapter_id_known(cls, v: StrictInt | StrictStr) -> StrictInt | StrictStr:
        if not ALLOW_UNCONFIGURED_ADAPTER_IDS_IN_WIRINGS and (
            not v in SOURCE_ADAPTERS and not isinstance(v, str)
        ):
            raise ValueError(
                f"Adapter with id {str(v)} is not known / not registered as source adapter."
            )
        return v

    def to_input_wiring(self) -> InputWiring:
        return InputWiring(
            ref_id=self.ref_id,
            ref_id_type=self.ref_id_type,
            ref_key=self.ref_key,
            type=self.type,
            workflow_input_name=self.workflow_input_name,
            adapter_id=self.adapter_id,
            filters=self.filters,
        )

    @classmethod
    def from_input_wiring(cls, input_wiring: InputWiring) -> "InputWiringFrontendDto":
        return InputWiringFrontendDto(
            refId=input_wiring.ref_id,
            refIdType=input_wiring.ref_id_type,
            refKey=input_wiring.ref_key,
            type=input_wiring.type,
            workflowInputName=input_wiring.workflow_input_name,
            adapterId=input_wiring.adapter_id,
            filters=input_wiring.filters,
        )

    class Config:
        alias_generator = to_camel


class WiringFrontendDto(BaseModel):
    id: UUID = Field(default_factory=uuid4)  # noqa: A003
    name: str = "STANDARD-WIRING"
    input_wirings: list[InputWiringFrontendDto]
    output_wirings: list[OutputWiringFrontendDto]

    @validator("input_wirings", each_item=False)
    def input_names_unique(
        cls, input_wirings: list[InputWiringFrontendDto]
    ) -> list[InputWiringFrontendDto]:
        if len({iw.workflow_input_name for iw in input_wirings}) == len(input_wirings):
            return input_wirings

        raise ValueError(
            "Duplicates in workflow input names occuring in the input wirings not allowed."
        )

    @validator("output_wirings", each_item=False)
    def output_names_unique(
        cls, output_wirings: list[OutputWiringFrontendDto]
    ) -> list[OutputWiringFrontendDto]:
        if len({ow.workflow_output_name for ow in output_wirings}) == len(output_wirings):
            return output_wirings

        raise ValueError(
            "Duplicates in workflow output names occuring in the output wirings not allowed."
        )

    def to_wiring(self) -> WorkflowWiring:
        return WorkflowWiring(
            input_wirings=[iw.to_input_wiring() for iw in self.input_wirings],
            output_wirings=[ow.to_output_wiring() for ow in self.output_wirings],
        )

    @classmethod
    def from_wiring(cls, wiring: WorkflowWiring, transformation_id: UUID) -> "WiringFrontendDto":
        return WiringFrontendDto(
            id=transformation_id,
            inputWirings=[
                InputWiringFrontendDto.from_input_wiring(iw) for iw in wiring.input_wirings
            ],
            outputWirings=[
                OutputWiringFrontendDto.from_output_wiring(ow) for ow in wiring.output_wirings
            ],
        )

    class Config:
        alias_generator = to_camel

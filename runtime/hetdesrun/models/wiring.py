import re
from enum import StrEnum

from pydantic import BaseModel, ConstrainedStr, Field, StrictInt, StrictStr, validator

from hetdesrun.adapters import SINK_ADAPTERS, SOURCE_ADAPTERS
from hetdesrun.adapters.generic_rest.external_types import ExternalType, GeneralType
from hetdesrun.models.adapter_data import RefIdType
from hetdesrun.models.util import valid_python_identifier

ALLOW_UNCONFIGURED_ADAPTER_IDS_IN_WIRINGS = False
RESERVED_FILTER_KEYS = ["from", "to", "id"]


class FilterKey(ConstrainedStr):
    min_length = 1
    regex = re.compile(r"^[a-zA-Z]\w+$", flags=re.ASCII)


class OutputWiring(BaseModel):
    workflow_output_name: str = Field(..., alias="workflow_output_name")
    adapter_id: StrictInt | StrictStr = Field("direct_provisioning", alias="adapter_id")
    ref_id: str | None = Field(
        None,
        description=(
            "Id referencing the sink in external systems." " Not necessary for direct provisioning."
        ),
    )
    ref_id_type: RefIdType | None = Field(
        None,
        description="Required if type is specified and is a metadata type. "
        "Then describes to what kind of object in the tree the metadatum is attached. "
        "Must then be one of "
        ", ".join(['"' + x.value + '"' for x in list(RefIdType)]),
    )
    ref_key: str | None = Field(
        None,
        description="Required if type is specified and is a metadata type. "
        "Then is the key of the metdatum.",
    )
    type: ExternalType | None = Field(  # noqa: A003
        None,
        description="Type of data. If present then must be one of "
        + ", ".join(['"' + x.value + '"' for x in list(ExternalType)]),  # type: ignore
    )
    filters: dict[FilterKey, str | None] = {}

    @validator("adapter_id")
    def adapter_id_known(cls, v: StrictInt | StrictStr) -> StrictInt | StrictStr:
        if not ALLOW_UNCONFIGURED_ADAPTER_IDS_IN_WIRINGS and (
            not v in SINK_ADAPTERS and not isinstance(v, str)
        ):
            raise ValueError(
                f"Adapter with id {str(v)} is not known / not registered as sink adapter."
            )
        return v

    @validator("workflow_output_name")
    def name_valid_python_identifier(cls, workflow_output_name: str) -> str:
        return valid_python_identifier(cls, workflow_output_name)

    @validator("type")
    def metadata_type_includes_additional_fields(
        cls, v: ExternalType | None, values: dict
    ) -> ExternalType | None:
        if (
            v is not None
            and (GeneralType(v.general_type) == GeneralType.METADATA)
            and (values["ref_id_type"] is None or values["ref_key"] is None)
        ):
            raise ValueError(
                "metadata datatype in OutputWiring requires additional fields "
                '"ref_id_type" and "ref_key". At least one of them is missing.'
            )
        return v

    @validator("ref_id")
    def ref_id_set_for_non_direct_provisioning(cls, v: str | None, values: dict) -> str | None:
        if values["adapter_id"] not in {"direct_provisioning", 1} and v is None:
            raise ValueError("ref_id must be provided for non direct_provisioning output wirings")
        return v

    @validator("filters")
    def no_reserved_filter_keys(
        cls, filters: dict[FilterKey, str | None]
    ) -> dict[FilterKey, str | None]:
        if any(reserved_key in filters for reserved_key in RESERVED_FILTER_KEYS):
            raise ValueError(f"The strings {RESERVED_FILTER_KEYS} are reserved filter keys!")

        return filters

    @validator("filters")
    def none_filter_value_to_empty_string(
        cls, filters: dict[FilterKey, str | None]
    ) -> dict[FilterKey, str | None]:
        for key, value in filters.items():
            if value is None:
                filters[key] = ""
        return filters


class InputWiring(BaseModel):
    workflow_input_name: str = Field(..., alias="workflow_input_name")
    adapter_id: StrictInt | StrictStr = Field("direct_provisioning", alias="adapter_id")

    ref_id: str | None = Field(
        None,
        description=(
            "Id referencing the source in external systems."
            " Not necessary for direct provisioning."
        ),
    )
    ref_id_type: RefIdType | None = Field(
        None,
        description="Required if type is specified and is a metadata type. "
        "Then describes to what kind of object in the tree the metadatum is attached. "
        "Must then be one of "
        ", ".join(['"' + x.value + '"' for x in list(RefIdType)]),
    )
    ref_key: str | None = None
    type: ExternalType | None = Field(  # noqa: A003
        None,
        description="Type of data. If present then must be one of "
        + ", ".join(['"' + x.value + '"' for x in list(ExternalType)]),  # type: ignore
    )
    use_default_value: bool = False
    filters: dict[FilterKey, str | None] = {}

    @validator("adapter_id")
    def adapter_id_known(cls, v: StrictInt | StrictStr) -> StrictInt | StrictStr:
        if not ALLOW_UNCONFIGURED_ADAPTER_IDS_IN_WIRINGS and (
            not v in SOURCE_ADAPTERS and not isinstance(v, str)
        ):
            raise ValueError(
                f"Adapter with id {str(v)} is not known / not registered as source adapter."
            )
        return v

    @validator("workflow_input_name")
    def name_valid_python_identifier(cls, workflow_input_name: str) -> str:
        return valid_python_identifier(cls, workflow_input_name)

    @validator("type")
    def metadata_type_includes_additional_fields(
        cls, v: ExternalType | None, values: dict
    ) -> ExternalType | None:
        if (
            v is not None
            and (GeneralType(v.general_type) == GeneralType.METADATA)
            and (values["ref_id_type"] is None or values["ref_key"] is None)
        ):
            raise ValueError(
                "metadata datatype in InputWiring requires additional fields "
                '"ref_id_type" and "ref_key". At least one of them is missing.'
            )
        return v

    @validator("ref_id")
    def ref_id_set_for_non_direct_provisioning(cls, v: str | None, values: dict) -> str | None:
        if values["adapter_id"] not in {"direct_provisioning", 1} and v is None:
            raise ValueError("ref_id must be provided for non direct_provisioning input wirings")
        return v

    @validator("filters")
    def no_reserved_filter_keys(
        cls, filters: dict[FilterKey, str | None]
    ) -> dict[FilterKey, str | None]:
        if any(reserved_key in filters for reserved_key in RESERVED_FILTER_KEYS):
            raise ValueError(f"The strings {RESERVED_FILTER_KEYS} are reserved filter keys!")

        return filters

    @validator("filters")
    def none_filter_value_to_empty_string(
        cls, filters: dict[FilterKey, str | None]
    ) -> dict[FilterKey, str | None]:
        for key, value in filters.items():
            if value is None:
                filters[key] = ""
        return filters


class GridstackPositioningType(StrEnum):
    INPUT = "INPUT"
    OUTPUT = "OUTPUT"


class GridstackItemPositioning(BaseModel):
    x: int | None = Field(None, ge=0)
    y: int | None = Field(None, ge=0)
    w: int | None = Field(None, ge=0)
    h: int | None = Field(None, ge=0)
    id: str = Field(  # noqa: A003
        ...,
        description=(
            "gs-id of the .grid-stack-item which is extracted as id by " "gridstacks save method"
        ),
    )
    type: GridstackPositioningType = GridstackPositioningType.OUTPUT
    allowed_input_values: list[str] = []


class WorkflowWiring(BaseModel):
    input_wirings: list[InputWiring] = []
    output_wirings: list[OutputWiring] = []
    dashboard_positionings: list[GridstackItemPositioning] = []

    @validator("input_wirings", each_item=False)
    def input_names_unique(cls, input_wirings: list[InputWiring]) -> list[InputWiring]:
        if len({iw.workflow_input_name for iw in input_wirings}) == len(input_wirings):
            return input_wirings

        raise ValueError(
            "Duplicates in workflow input names occuring in the input wirings not allowed."
        )

    @validator("output_wirings", each_item=False)
    def output_names_unique(cls, output_wirings: list[OutputWiring]) -> list[OutputWiring]:
        if len({ow.workflow_output_name for ow in output_wirings}) == len(output_wirings):
            return output_wirings

        raise ValueError(
            "Duplicates in workflow output names occuring in the output wirings not allowed."
        )

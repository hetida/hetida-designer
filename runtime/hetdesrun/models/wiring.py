import json
import re
from enum import StrEnum
from textwrap import dedent
from typing import Annotated, Any, Self
from urllib.parse import parse_qs

from pydantic import (
    AnyUrl,
    BaseModel,
    ConfigDict,
    Field,
    StrictInt,
    StrictStr,
    TypeAdapter,
    UrlConstraints,
    ValidationInfo,
    field_validator,
    model_validator,
)

from hetdesrun.adapters import SINK_ADAPTERS, SOURCE_ADAPTERS
from hetdesrun.adapters.generic_rest.external_types import ExternalType, GeneralType
from hetdesrun.models.adapter_data import RefIdType
from hetdesrun.models.util import valid_python_identifier

HdWiringUri = Annotated[AnyUrl, UrlConstraints(allowed_schemes=["hd"])]

ALLOW_UNCONFIGURED_ADAPTER_IDS_IN_WIRINGS = False
RESERVED_FILTER_KEYS = ["from", "to", "id"]

FilterKey = Annotated[
    str, Field(min_length=1, pattern=re.compile(r"^[a-zA-Z]\w*$", flags=re.ASCII))
]


filter_key_adapter = TypeAdapter(FilterKey)


class UriFragmentWiringInfo(BaseModel):
    ref_id_type: RefIdType | None = Field(
        None,
        description="Required if type is specified and is a metadata type. "
        "Then describes to what kind of object in the tree the metadatum is attached. "
        "Must then be one of "
        ", ".join(['"' + x.value + '"' for x in list(RefIdType)]),
    )
    ref_key: str | None = None
    use_default_value: bool = False
    attrs: dict[str, Any] | None = None

    # When parsed from uri fragment, misspelled fields should be detected:
    model_config = ConfigDict(extra="forbid")


class OutputWiring(BaseModel):
    workflow_output_name: str = Field(..., alias="workflow_output_name")

    uri: HdWiringUri | None = Field(  # pyright: ignore[reportInvalidTypeForm]
        None,
        description=dedent(
            """
            A wiring can be described completely (apart from the workflow input
            name and the type) by a uri. If such a uri is provided, its information
            will override other fields. The uri's filters (via query params) will update
            an supplement filters provided via the filters field, possibly overwriting
            them. I.e. filters set by uri have higher precedence.

            The format is

                hd://<adapter_key>/<ref_id>?filter_key_1=filter_value_1&other_filter=other_value#ref_key=<ref_key>&ref_id_type=<ref_id_type>

            Notes:
            * Schema must be "hd"
            * must be properly url encoded
            * multiple values for the same filter key will yield an json serialized array
              (i.e. a string) to this filter. This string will also override any
              value possibly provided with the filters field.
            * ref_key and ref_id_type can be provided in the "fragment" part of the uri
            """
        ).strip(),
    )

    adapter_id: StrictInt | StrictStr = Field("direct_provisioning", alias="adapter_id")
    ref_id: str | None = Field(
        None,
        description=(
            "Id referencing the sink in external systems. Not necessary for direct provisioning."
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

    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)

    @field_validator("adapter_id")
    @classmethod
    def adapter_id_known(cls, v: StrictInt | StrictStr) -> StrictInt | StrictStr:
        if not ALLOW_UNCONFIGURED_ADAPTER_IDS_IN_WIRINGS and (
            not v in SINK_ADAPTERS and not isinstance(v, str)
        ):
            raise ValueError(
                f"Adapter with id {str(v)} is not known / not registered as sink adapter."
            )
        return v

    @field_validator("workflow_output_name")
    @classmethod
    def name_valid_python_identifier(cls, workflow_output_name: str) -> str:
        return valid_python_identifier(cls, workflow_output_name)

    @field_validator("type")
    @classmethod
    def metadata_type_includes_additional_fields(
        cls, v: ExternalType | None, info: ValidationInfo
    ) -> ExternalType | None:
        if (
            v is not None
            and info.data["adapter_id"] not in {"direct_provisioning", 1, "component-adapter"}
            and (GeneralType(v.general_type) == GeneralType.METADATA)
            and (info.data["ref_id_type"] is None or info.data["ref_key"] is None)
        ):
            raise ValueError(
                "metadata datatype in OutputWiring requires additional fields "
                '"ref_id_type" and "ref_key". At least one of them is missing.'
            )
        return v

    @field_validator("ref_id")
    @classmethod
    def ref_id_set_for_non_direct_provisioning(
        cls, v: str | None, info: ValidationInfo
    ) -> str | None:
        if info.data["adapter_id"] not in {"direct_provisioning", 1, "drop", "plot"} and v is None:
            raise ValueError("ref_id must be provided for non direct_provisioning output wirings")
        return v

    @field_validator("filters")
    @classmethod
    def no_reserved_filter_keys(
        cls, filters: dict[FilterKey, str | None]
    ) -> dict[FilterKey, str | None]:
        if any(reserved_key in filters for reserved_key in RESERVED_FILTER_KEYS):
            raise ValueError(f"The strings {RESERVED_FILTER_KEYS} are reserved filter keys!")

        return filters

    @field_validator("filters")
    @classmethod
    def none_filter_value_to_empty_string(
        cls, filters: dict[FilterKey, str | None]
    ) -> dict[FilterKey, str | None]:
        for key, value in filters.items():
            if value is None:
                filters[key] = ""
        return filters

    @model_validator(mode="after")
    def extract_other_fields_from_uri(self, info: ValidationInfo) -> Self:
        """Extract infos from uri if present and update wiring fields

        The result is revalidated to ensure that the updated wiring conforms
        to all validation rules.

        Note: The uri is expected to be url encoded.
        """

        # Only extract once / avoid infinite recursion from revalidation:
        if (self.uri is None) or (info.context and info.context.get("uri_already_expanded", False)):
            # do not run this validator again!
            return self

        update_wiring_from_uri(self)

        # revalidate the new data
        revalidated = OutputWiring.model_validate(
            self.model_dump(), context={"uri_already_expanded": True}
        )

        # note: Pydantic wants us to return the original self really and not the
        # newly-validated object. This is okay, since both should be equal.
        # Fore safety, we actually check that:
        if not self == revalidated:
            raise ValueError(
                "Revalidating object after uri expansion did not yield an equal object!"
            )

        return self


class InputWiring(BaseModel):
    workflow_input_name: str = Field(..., alias="workflow_input_name")

    uri: HdWiringUri | None = Field(  # pyright: ignore[reportInvalidTypeForm]
        None,
        description=dedent(
            """
            A wiring can be described completely (apart from the workflow input
            name and the type) by a uri. If such a uri is provided, its information
            will override other fields. The uri's filters (via query params) will update
            an supplement filters provided via the filters field, possibly overwriting
            them. I.e. filters set by uri have higher precedence.

            The format is

                hd://<adapter_key>/<ref_id>?filter_key_1=filter_value_1&other_filter=other_value#ref_key=<ref_key>&ref_id_type=<ref_id_type>

            Notes:
            * Schema must be "hd"
            * must be properly url encoded
            * multiple values for the same filter key will yield an json serialized array
              (i.e. a string) to this filter. This string will also override any
              value possibly provided with the filters field.
            * ref_key and ref_id_type can be provided in the "fragment" part of the uri
            """
        ).strip(),
    )

    adapter_id: StrictInt | StrictStr = Field("direct_provisioning", alias="adapter_id")

    ref_id: str | None = Field(
        None,
        description=(
            "Id referencing the source in external systems. Not necessary for direct provisioning."
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

    # we must allow Any as filter value here, since InputWirings for Component Adapter
    # sinks need to get the actual value as Python object instead of a str in order
    # to avoid unnecessary serializing/deserializing between trafo output and
    # component adapter sink execution.
    filters: dict[FilterKey, str | Any | None] = {}

    attrs: dict[str, Any] | None = Field(
        None,
        description=(
            "Additional metadata that should update a attrs attribute of type dict the"
            " the loaded object after loading. This will be applied using a shallow dict"
            " update, so its entries may overwrite same-named entries in the attrs dict of"
            " the object provided by the adapter. This does only work for adapters"
            " that provide the correct object themself. E.g. It does not work for the"
            ' direct_provisioning adapter which provides the filter "value" as is (e.g. string)'
            " and relies on parsing at a later stage in the execution process."
            " The Virtual Structure adapter allows to set a meta_data attribute"
            " in virtual sources. Its value is provided as attrs to the actual"
            " adapter's wiring then."
        ),
    )

    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)

    @field_validator("adapter_id")
    @classmethod
    def adapter_id_known(cls, v: StrictInt | StrictStr) -> StrictInt | StrictStr:
        if not ALLOW_UNCONFIGURED_ADAPTER_IDS_IN_WIRINGS and (
            not v in SOURCE_ADAPTERS and not isinstance(v, str)
        ):
            raise ValueError(
                f"Adapter with id {str(v)} is not known / not registered as source adapter."
            )
        return v

    @field_validator("workflow_input_name")
    @classmethod
    def name_valid_python_identifier(cls, workflow_input_name: str) -> str:
        return valid_python_identifier(cls, workflow_input_name)

    @field_validator("type")
    @classmethod
    def metadata_type_includes_additional_fields(
        cls, v: ExternalType | None, info: ValidationInfo
    ) -> ExternalType | None:
        if (
            v is not None
            and info.data["adapter_id"] not in {"direct_provisioning", 1, "component-adapter"}
            and (GeneralType(v.general_type) == GeneralType.METADATA)
            and (info.data["ref_id_type"] is None or info.data["ref_key"] is None)
        ):
            raise ValueError(
                "metadata datatype in InputWiring requires additional fields "
                '"ref_id_type" and "ref_key". At least one of them is missing.'
            )
        return v

    @field_validator("ref_id")
    @classmethod
    def ref_id_set_for_non_direct_provisioning(
        cls, v: str | None, info: ValidationInfo
    ) -> str | None:
        if info.data["adapter_id"] not in {"direct_provisioning", 1, "drop", "plot"} and v is None:
            raise ValueError("ref_id must be provided for non direct_provisioning input wirings")
        return v

    @field_validator("filters")
    @classmethod
    def no_reserved_filter_keys(
        cls, filters: dict[FilterKey, str | None]
    ) -> dict[FilterKey, str | None]:
        if any(reserved_key in filters for reserved_key in RESERVED_FILTER_KEYS):
            raise ValueError(f"The strings {RESERVED_FILTER_KEYS} are reserved filter keys!")

        return filters

    @field_validator("filters")
    @classmethod
    def none_filter_value_to_empty_string(
        cls, filters: dict[FilterKey, str | None]
    ) -> dict[FilterKey, str | None]:
        for key, value in filters.items():
            if value is None:
                filters[key] = ""
        return filters

    @model_validator(mode="after")
    def extract_other_fields_from_uri(self, info: ValidationInfo) -> Self:
        """Extract infos from uri if present and update wiring fields

        The result is revalidated to ensure that the updated wiring conforms
        to all validation rules.

        Note: The uri is expected to be url encoded.
        """

        # Only extract once / avoid infinite recursion from revalidation:
        if (self.uri is None) or (info.context and info.context.get("uri_already_expanded", False)):
            # do not run this validator again!
            return self

        update_wiring_from_uri(self)

        # revalidate the new data
        revalidated = InputWiring.model_validate(
            self.model_dump(), context={"uri_already_expanded": True}
        )

        # note: Pydantic wants us to return the original self really and not the
        # newly-validated object. This is okay, since both should be equal.
        # Fore safety, we actually check that:
        if not self == revalidated:
            raise ValueError(
                "Revalidating object after uri expansion did not yield an equal object!"
            )

        return self


def update_wiring_from_uri(wiring: InputWiring | OutputWiring) -> None:
    """Modify wiring inplace with uri wiring if present

    This actually resolves uri wirings into actual wirings by overwriting
    fields with values from the uri, if present there.

    That is, infos provided as part of the uri have higher priority than
    directly provided, i.e. they overwrite them if both are present.

    Also resolves uri_wiring_shortcuts if configured.
    """
    extracted_key: str | None = None
    extracted_path: str | None = None
    from hetdesrun.webservice.config import get_config  # noqa: PLC0415

    if wiring.uri is None:
        return

    if wiring.uri.host:
        config = get_config()
        if wiring.uri.host in config.uri_wiring_shortcuts:
            extracted_key, extracted_path = config.uri_wiring_shortcuts[wiring.uri.host]
            extracted_path = extracted_path.lstrip("/")
        else:
            extracted_key = wiring.uri.host

        wiring.adapter_id = extracted_key

    if wiring.uri.path or extracted_path:
        # ref_id is path:
        if extracted_path is None and wiring.uri.path is not None:
            extracted_path = wiring.uri.path.lstrip("/")

        wiring.ref_id = extracted_path

    # query params can provide (updated) filter values
    if wiring.uri.query:
        parsed_params: dict[str, list[str]] = parse_qs(wiring.uri.query)

        # Convert to dict[str, str]
        uri_filters = {
            # repeated query param is stored as json array string value
            filter_key_adapter.validate_python(key): (
                values[0] if len(values) == 1 else json.dumps(values)
            )
            for key, values in parsed_params.items()
            if values  # Skip empty value lists
        }

        # Merge: URI params override existing filters
        wiring.filters = {**wiring.filters, **uri_filters}

    if wiring.uri.fragment:
        # update other, less used, wiring fields from fragment
        parsed_fragment: dict[str, list[str]] = parse_qs(wiring.uri.query)

        uri_fragment_info = UriFragmentWiringInfo(**parsed_fragment)

        if uri_fragment_info.ref_id_type is not None and "ref_id_type" in parsed_fragment:
            wiring.ref_id_type = uri_fragment_info.ref_id_type
        if uri_fragment_info.ref_key is not None and "ref_key" in parsed_fragment:
            wiring.ref_key = uri_fragment_info.ref_key
        if (
            uri_fragment_info.attrs is not None
            and "attrs" in parsed_fragment
            and isinstance(wiring, InputWiring)
        ):
            wiring.attrs = uri_fragment_info.attrs
        if (
            uri_fragment_info.use_default_value is not None
            and "use_default_value" in parsed_fragment
            and isinstance(wiring, InputWiring)
        ):
            wiring.use_default_value = uri_fragment_info.use_default_value


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
            "gs-id of the .grid-stack-item which is extracted as id by gridstacks save method"
        ),
    )
    type: GridstackPositioningType = GridstackPositioningType.OUTPUT
    allowed_input_values: list[str] = []


class WorkflowWiring(BaseModel):
    input_wirings: list[InputWiring] = []
    output_wirings: list[OutputWiring] = []
    dashboard_positionings: list[GridstackItemPositioning] = []

    @field_validator("input_wirings")
    @classmethod
    def input_names_unique(cls, input_wirings: list[InputWiring]) -> list[InputWiring]:
        if len({iw.workflow_input_name for iw in input_wirings}) == len(input_wirings):
            return input_wirings

        raise ValueError(
            "Duplicates in workflow input names occuring in the input wirings not allowed."
        )

    @field_validator("output_wirings")
    @classmethod
    def output_names_unique(cls, output_wirings: list[OutputWiring]) -> list[OutputWiring]:
        if len({ow.workflow_output_name for ow in output_wirings}) == len(output_wirings):
            return output_wirings

        raise ValueError(
            "Duplicates in workflow output names occuring in the output wirings not allowed."
        )

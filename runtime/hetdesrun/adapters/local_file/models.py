from typing import Literal

from pydantic import BaseModel, Field, field_validator

from hetdesrun.adapters.generic_rest.external_types import ExternalType
from hetdesrun.adapters.models import FilterType


class InfoResponse(BaseModel):
    id: str  # noqa: A003
    name: str
    version: str


class StructureThingNode(BaseModel):
    id: str  # noqa: A003
    parentId: str | None = None
    name: str
    description: str


class StructureFilter(BaseModel):
    name: str
    type: FilterType  # noqa: A003
    required: bool


class LocalFileStructureSource(BaseModel):
    id: str  # noqa: A003
    thingNodeId: str
    name: str
    type: ExternalType = ExternalType.DATAFRAME  # noqa: A003
    visible: Literal[True] = True
    path: str = Field(..., description="Display path used in Designer Frontend")
    metadataKey: str | None = None
    filters: dict[str, StructureFilter] | None = {}

    @field_validator("type")
    @classmethod
    def restrict_to_supported_types(cls, v: ExternalType) -> ExternalType:
        if v not in (ExternalType.DATAFRAME, ExternalType.METADATA_ANY):
            raise TypeError(
                "Only dataframe and metadata(any) are allowed external types"
                " for the local file adapter"
            )
        return v


class MultipleSourcesResponse(BaseModel):
    resultCount: int
    sources: list[LocalFileStructureSource]


class LocalFileStructureSink(BaseModel):
    id: str  # noqa: A003
    thingNodeId: str
    name: str
    type: ExternalType = ExternalType.DATAFRAME  # noqa: A003
    visible: Literal[True] = True
    path: str = Field(..., description="Display path used in Designer Frontend")
    metadataKey: str | None = None
    filters: dict[str, StructureFilter] | None = {}

    @field_validator("type")
    @classmethod
    def restrict_to_supported_types(cls, v: ExternalType) -> ExternalType:
        if v not in (ExternalType.DATAFRAME, ExternalType.METADATA_ANY):
            raise TypeError(
                "Only dataframe and metadata(any) are allowed external types"
                " for the local file adapter"
            )
        return v


class MultipleSinksResponse(BaseModel):
    resultCount: int
    sinks: list[LocalFileStructureSink]


class StructureResponse(BaseModel):
    id: str  # noqa: A003
    name: str
    thingNodes: list[StructureThingNode]
    sources: list[LocalFileStructureSource]
    sinks: list[LocalFileStructureSink]

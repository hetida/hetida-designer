from typing import Literal

from pydantic import BaseModel, Field

from hetdesrun.adapters.generic_rest.external_types import ExternalType


class InfoResponse(BaseModel):
    id: str  # noqa: A003
    name: str
    version: str


class StructureThingNode(BaseModel):
    id: str  # noqa: A003
    parentId: str | None = None
    name: str
    description: str


class SQLReaderStructureSource(BaseModel):
    id: str  # noqa: A003
    thingNodeId: str
    name: str
    type: ExternalType = ExternalType.DATAFRAME  # noqa: A003
    visible: Literal[True] = True
    path: str = Field(..., description="Display path used in Designer Frontend")
    metadataKey: str | None = None
    filters: dict[str, dict] | None = {}


class SQLReaderStructureSink(BaseModel):
    id: str  # noqa: A003
    thingNodeId: str
    name: str
    type: ExternalType = ExternalType.DATAFRAME  # noqa: A003
    visible: Literal[True] = True
    path: str = Field(..., description="Display path used in Designer Frontend")
    metadataKey: str | None = None
    filters: dict[str, dict] | None = {}


class MultipleSourcesResponse(BaseModel):
    resultCount: int
    sources: list[SQLReaderStructureSource]


class MultipleSinksResponse(BaseModel):
    resultCount: int
    sinks: list[SQLReaderStructureSink]


class StructureResponse(BaseModel):
    id: str  # noqa: A003
    name: str
    thingNodes: list[StructureThingNode]
    sources: list[SQLReaderStructureSource]
    sinks: list[object]

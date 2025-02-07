from typing import Literal

from pydantic import BaseModel, Field

from hetdesrun.adapters.generic_rest.external_types import ExternalType


class StructureThingNode(BaseModel):
    id: str  # noqa: A003
    parentId: str | None = None
    name: str
    description: str


class ComponentAdapterStructureSink(BaseModel):
    id: str  # noqa: A003
    thingNodeId: str
    name: str
    type: ExternalType
    visible: Literal[True] = True
    path: str = Field(..., description="Display path used in Designer Frontend")
    metadataKey: str | None = None
    filters: dict[str, dict] | None = {}


class ComponentAdapterStructureSource(BaseModel):
    id: str  # noqa: A003
    thingNodeId: str
    name: str
    type: ExternalType
    visible: Literal[True] = True
    path: str = Field(..., description="Display path used in Designer Frontend")
    metadataKey: str | None = None
    filters: dict[str, dict] | None = {}


class InfoResponse(BaseModel):
    id: str  # noqa: A003
    name: str
    version: str


class StructureResponse(BaseModel):
    id: str  # noqa: A003
    name: str
    thingNodes: list[StructureThingNode]
    sources: list[ComponentAdapterStructureSource]
    sinks: list[ComponentAdapterStructureSink]


class MultipleSourcesResponse(BaseModel):
    resultCount: int
    sources: list[ComponentAdapterStructureSource]


class MultipleSinksResponse(BaseModel):
    resultCount: int
    sources: list[ComponentAdapterStructureSink]

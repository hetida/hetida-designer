from typing import Literal

from pydantic import BaseModel, Field


class InfoResponse(BaseModel):
    id: str  # noqa: A003
    name: str
    version: str


class StructureThingNode(BaseModel):
    id: str  # noqa: A003
    parentId: str | None = None
    name: str
    description: str


class LocalFileStructureSource(BaseModel):
    id: str  # noqa: A003
    thingNodeId: str
    name: str
    type: Literal["dataframe"] = "dataframe"  # noqa: A003
    visible: Literal[True] = True
    path: str = Field(..., description="Display path used in Designer Frontend")
    metadataKey: Literal[None] = None
    filters: dict[str, dict] | None = {}


class MultipleSourcesResponse(BaseModel):
    resultCount: int
    sources: list[LocalFileStructureSource]


class LocalFileStructureSink(BaseModel):
    id: str  # noqa: A003
    thingNodeId: str
    name: str
    type: Literal["dataframe"] = "dataframe"  # noqa: A003
    visible: Literal[True] = True
    path: str = Field(..., description="Display path used in Designer Frontend")
    metadataKey: Literal[None] = None
    filters: dict[str, dict] | None = {}


class MultipleSinksResponse(BaseModel):
    resultCount: int
    sinks: list[LocalFileStructureSink]


class StructureResponse(BaseModel):
    id: str  # noqa: A003
    name: str
    thingNodes: list[StructureThingNode]
    sources: list[LocalFileStructureSource]
    sinks: list[LocalFileStructureSink]

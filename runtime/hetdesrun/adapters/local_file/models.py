from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field  # pylint: disable=no-name-in-module


class InfoResponse(BaseModel):
    id: str
    name: str
    version: str


class StructureThingNode(BaseModel):
    id: str
    parentId: Optional[str] = None
    name: str
    description: str


class LocalFileStructureSource(BaseModel):
    id: str
    thingNodeId: str
    name: str
    type: Literal["dataframe"] = "dataframe"
    visible: Literal[True] = True
    path: str = Field(..., description="Display path used in Designer Frontend")
    metadataKey: Literal[None] = None
    filters: Optional[Dict[str, Dict]] = {}


class MultipleSourcesResponse(BaseModel):
    resultCount: int
    sources: List[LocalFileStructureSource]


class LocalFileStructureSink(BaseModel):
    id: str
    thingNodeId: str
    name: str
    type: Literal["dataframe"] = "dataframe"
    visible: Literal[True] = True
    path: str = Field(..., description="Display path used in Designer Frontend")
    metadataKey: Literal[None] = None
    filters: Optional[Dict[str, Dict]] = {}


class MultipleSinksResponse(BaseModel):
    resultCount: int
    sinks: List[LocalFileStructureSink]


class StructureResponse(BaseModel):
    id: str
    name: str
    thingNodes: List[StructureThingNode]
    sources: List[LocalFileStructureSource]
    sinks: List[LocalFileStructureSink]

import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field  # pylint: disable=no-name-in-module

from demo_adapter_python.external_types import ExternalType, ValueDataType


class InfoResponse(BaseModel):
    id: str
    name: str
    version: str


class StructureThingNode(BaseModel):
    id: str
    parentId: Optional[str] = None
    name: str
    description: str


class StructureFilter(BaseModel):
    name: str
    required: bool


class StructureSource(BaseModel):
    id: str
    thingNodeId: str
    name: str
    type: ExternalType
    visible: Optional[bool] = True
    path: str
    metadataKey: Optional[str] = None
    filters: Optional[Dict[str, StructureFilter]] = {}


class StructureSink(BaseModel):
    id: str
    thingNodeId: str
    name: str
    type: ExternalType
    visible: Optional[bool] = True
    path: str
    metadataKey: Optional[str] = None
    filters: Optional[Dict[str, StructureFilter]] = {}


class StructureResponse(BaseModel):
    id: str
    name: str
    thingNodes: List[StructureThingNode]
    sources: List[StructureSource]
    sinks: List[StructureSink]


class MultipleSourcesResponse(BaseModel):
    resultCount: int
    sources: List[StructureSource]


class MultipleSinksResponse(BaseModel):
    resultCount: int
    sinks: List[StructureSink]


class PostMetadatum(BaseModel):
    key: str
    value: Any = Field(..., example=True)


class GetMetadatum(BaseModel):
    key: str
    value: Optional[Any] = None
    dataType: ValueDataType
    isSink: Optional[bool] = False


class TimeseriesRecord(BaseModel):
    timestamp: datetime.datetime
    value: Any = Field(..., example=0.25)

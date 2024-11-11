from typing import Literal, get_args

from pydantic import BaseModel, Field

from hetdesrun.adapters.generic_rest.external_types import ExternalType

LiteralRootNodeId = Literal["EXTERNAL_SOURCES_SINGLE_ROOT_NODE"]
single_root_node_id = get_args(LiteralRootNodeId)[0]


class InfoResponse(BaseModel):
    id: str  # noqa: A003
    name: str
    version: str


class StructureThingNode(BaseModel):
    id: LiteralRootNodeId = single_root_node_id
    parentId: None = None
    name: str = "External Sources"
    description: str = ""


class ExternalSourcesStructureSource(BaseModel):
    id: str  # noqa: A003
    thingNodeId: LiteralRootNodeId = single_root_node_id
    name: str
    type: ExternalType
    visible: Literal[True] = True
    path: str = Field(..., description="Display path used in Designer Frontend")
    metadataKey: str | None = None
    filters: dict[str, dict] | None = {}


class ExternalSourcesStructureSink(BaseModel):
    id: str  # noqa: A003
    thingNodeId: LiteralRootNodeId = single_root_node_id
    name: str
    type: ExternalType
    visible: Literal[True] = True
    path: str = Field(..., description="Display path used in Designer Frontend")
    metadataKey: str | None = None
    filters: dict[str, dict] | None = {}


class MultipleSourcesResponse(BaseModel):
    resultCount: int
    sources: list[ExternalSourcesStructureSource]


class MultipleSinksResponse(BaseModel):
    resultCount: int
    sinks: list[ExternalSourcesStructureSink]


class StructureResponse(BaseModel):
    id: str  # noqa: A003
    name: str
    thingNodes: list[StructureThingNode]
    sources: list[ExternalSourcesStructureSource]
    sinks: list[ExternalSourcesStructureSink]

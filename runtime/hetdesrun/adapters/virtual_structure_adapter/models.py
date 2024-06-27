from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from hetdesrun.adapters.generic_rest.external_types import ExternalType


class StructureThingNode(BaseModel):
    id: UUID  # noqa: A003
    parentId: UUID | None = None
    name: str
    description: str


class StructureVirtualSource(BaseModel):
    id: UUID  # noqa: A003
    thingNodeId: UUID
    name: str
    # TODO Change, create custom type?
    type: ExternalType = ExternalType.DATAFRAME  # noqa: A003
    visible: Literal[True] = True
    path: str = Field(..., description="Display path used in Designer Frontend")
    metadataKey: str | None = None
    filters: dict[str, dict] | None = {}


class StructureVirtualSink(BaseModel):
    id: UUID  # noqa: A003
    thingNodeId: UUID
    name: str
    # TODO Change, create custom type?
    type: ExternalType = ExternalType.DATAFRAME  # noqa: A003
    visible: Literal[True] = True
    path: str = Field(..., description="Display path used in Designer Frontend")
    metadataKey: str | None = None
    filters: dict[str, dict] | None = {}


class StructureResponse(BaseModel):
    id: str  # noqa: A003
    name: str
    thingNodes: list[StructureThingNode]
    sources: list[StructureVirtualSource]
    sinks: list[StructureVirtualSink]

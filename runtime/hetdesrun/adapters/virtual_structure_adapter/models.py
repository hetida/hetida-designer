from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from hetdesrun.adapters.generic_rest.external_types import ExternalType
from hetdesrun.structure.models import Sink, Source, ThingNode


class StructureThingNode(BaseModel):
    id: UUID  # noqa: A003
    parentId: UUID | None = None
    name: str
    description: str

    @classmethod
    def from_structure_service(cls, struct_tn: ThingNode) -> "StructureThingNode":
        return cls(
            id=struct_tn.id,
            parentId=struct_tn.parent_node_id,
            name=struct_tn.name,
            description=struct_tn.description,
        )


class StructureVirtualSource(BaseModel):
    id: UUID  # noqa: A003
    thingNodeId: UUID
    name: str
    type: ExternalType  # noqa: A003
    visible: Literal[True] = True
    path: str = Field(..., description="Display path used in Designer Frontend")
    metadataKey: str | None = None
    filters: dict[str, dict] | None = {}

    @classmethod
    def from_structure_service(cls, struct_source: Source) -> "StructureVirtualSource":
        return cls(
            id=struct_source.id,
            thingNodeId=struct_source.thingNodeId,
            name=struct_source.name,
            type=struct_source.type,
            path="",
        )


class StructureVirtualSink(BaseModel):
    id: UUID  # noqa: A003
    thingNodeId: UUID
    name: str
    type: ExternalType  # noqa: A003
    visible: Literal[True] = True
    path: str = Field(..., description="Display path used in Designer Frontend")
    metadataKey: str | None = None
    filters: dict[str, dict] | None = {}

    @classmethod
    def from_structure_service(cls, struct_sink: Sink) -> "StructureVirtualSink":
        return cls(
            id=struct_sink.id,
            thingNodeId=struct_sink.thingNodeId,
            name=struct_sink.name,
            type=struct_sink.type,
            path="",  # TODO Fill appropriately
        )


class StructureResponse(BaseModel):
    id: str  # noqa: A003
    name: str
    thingNodes: list[StructureThingNode]
    sources: list[StructureVirtualSource]
    sinks: list[StructureVirtualSink]

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
    name: str
    type: ExternalType  # noqa: A003
    visible: Literal[True] = True
    path: str = Field(..., description="Display path used in Designer Frontend")
    metadataKey: str | None = None
    filters: dict[str, dict] | None = {}

    @classmethod
    def from_structure_service(cls, source: Source) -> "StructureVirtualSource":
        def replace_whitespace(filter_name):
            filter_name = filter_name.strip()
            return filter_name.replace(" ", "_")

        return cls(
            id=source.id,
            name=source.name,
            type=source.type,
            path=source.path,
            filters={replace_whitespace(f.name): f for f in source.passthrough_filters}
            if source.passthrough_filters
            else {},
        )


class StructureVirtualSink(BaseModel):
    id: UUID  # noqa: A003
    name: str
    type: ExternalType  # noqa: A003
    visible: Literal[True] = True
    path: str = Field(..., description="Display path used in Designer Frontend")
    metadataKey: str | None = None
    filters: dict[str, dict] | None = {}

    @classmethod
    def from_structure_service(cls, sink: Sink) -> "StructureVirtualSink":
        def replace_whitespace(filter_name):
            filter_name = filter_name.strip()
            return filter_name.replace(" ", "_")

        return cls(
            id=sink.id,
            name=sink.name,
            type=sink.type,
            path=sink.path,
            filters={replace_whitespace(f.name): f for f in sink.passthrough_filters}
            if sink.passthrough_filters
            else {},
        )


class StructureResponse(BaseModel):
    id: str  # noqa: A003
    name: str
    thingNodes: list[StructureThingNode]
    sources: list[StructureVirtualSource]
    sinks: list[StructureVirtualSink]

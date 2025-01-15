from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from hetdesrun.adapters.generic_rest.external_types import ExternalType
from hetdesrun.structure.models import (
    StructureServiceSink,
    StructureServiceSource,
    StructureServiceThingNode,
)


class VirtualStructureAdapterThingNode(BaseModel):
    id: UUID  # noqa: A003
    parentId: UUID | None = None
    name: str
    description: str

    @classmethod
    def from_structure_service_thingnode(
        cls, struct_tn: StructureServiceThingNode
    ) -> "VirtualStructureAdapterThingNode":
        return cls(
            id=struct_tn.id,
            parentId=struct_tn.parent_node_id,
            name=struct_tn.name,
            description=struct_tn.description,
        )


class VirtualStructureAdapterSource(BaseModel):
    id: UUID  # noqa: A003
    # Needed for metadata(any) sources to fill ref_id in InputWiring for Frontend execution
    thingNodeId: UUID
    name: str
    type: ExternalType  # noqa: A003
    visible: Literal[True] = True
    path: str = Field(..., description="Display path used in Designer Frontend")
    metadataKey: str | None
    filters: dict[str, dict] | None = {}

    @classmethod
    def from_structure_service_source(
        cls, source: StructureServiceSource
    ) -> "VirtualStructureAdapterSource":
        return cls(
            id=source.id,
            thingNodeId=source.id,
            name=source.name,
            type=source.type,
            path=source.display_path,
            metadataKey=source.ref_key,
            filters={f.internal_name: f for f in source.passthrough_filters}
            if source.passthrough_filters
            else {},
        )


class VirtualStructureAdapterSink(BaseModel):
    id: UUID  # noqa: A003
    thingNodeId: (
        UUID  # Needed for metadata(any) sinks to fill ref_id in InputWiring for Frontend execution
    )
    name: str
    type: ExternalType  # noqa: A003
    visible: Literal[True] = True
    path: str = Field(..., description="Display path used in Designer Frontend")
    metadataKey: str | None
    filters: dict[str, dict] | None = {}

    @classmethod
    def from_structure_service_sink(
        cls, sink: StructureServiceSink
    ) -> "VirtualStructureAdapterSink":
        return cls(
            id=sink.id,
            thingNodeId=sink.id,
            name=sink.name,
            type=sink.type,
            path=sink.display_path,
            metadataKey=sink.ref_key,
            filters={f.internal_name: f for f in sink.passthrough_filters}
            if sink.passthrough_filters
            else {},
        )


class VirtualStructureAdapterInfoResponse(BaseModel):
    id: str  # noqa: A003
    name: str
    version: str


class VirtualStructureAdapterResponse(BaseModel):
    id: str  # noqa: A003
    name: str
    thingNodes: list[VirtualStructureAdapterThingNode]
    sources: list[VirtualStructureAdapterSource]
    sinks: list[VirtualStructureAdapterSink]


class MultipleVirtualStructureAdapterSourcesResponse(BaseModel):
    resultCount: int
    sources: list[VirtualStructureAdapterSource]


class MultipleVirtualStructureAdapterSinksResponse(BaseModel):
    resultCount: int
    sinks: list[VirtualStructureAdapterSink]

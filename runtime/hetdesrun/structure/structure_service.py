from uuid import UUID

from hetdesrun.persistence.structure_service_dbmodels import (
    SinkOrm,
    SourceOrm,
    ThingNodeOrm,
)
from hetdesrun.structure.db import get_session
from hetdesrun.structure.db.exceptions import DBNotFoundError
from hetdesrun.structure.models import Sink, Source, ThingNode


def get_children(
    parent_id: UUID | None,
) -> tuple[list[ThingNode], list[Source], list[Sink]]:
    with get_session()() as session:
        if parent_id is None:
            root_nodes = (
                session.query(ThingNodeOrm)
                .filter(ThingNodeOrm.parent_node_id.is_(None))
                .all()
            )
            return ([ThingNode.from_orm_model(node) for node in root_nodes], [], [])

        child_nodes = (
            session.query(ThingNodeOrm)
            .filter(ThingNodeOrm.parent_node_id == parent_id)
            .all()
        )

        sources = (
            session.query(SourceOrm).filter(SourceOrm.thing_node_id == parent_id).all()
        )
        sinks = session.query(SinkOrm).filter(SinkOrm.thing_node_id == parent_id).all()

        if not child_nodes and not sources and not sinks:
            raise DBNotFoundError(
                f"No children, sources, or sinks found for parent_id {parent_id}"
            )

        return (
            [ThingNode.from_orm_model(node) for node in child_nodes],
            [Source.from_orm_model(source) for source in sources],
            [Sink.from_orm_model(sink) for sink in sinks],
        )


def get_single_thingnode_from_db(tn_id: UUID) -> ThingNode:
    with get_session()() as session:
        thing_node = (
            session.query(ThingNodeOrm).filter(ThingNodeOrm.id == tn_id).one_or_none()
        )
        if thing_node:
            return ThingNode.from_orm_model(thing_node)

    raise DBNotFoundError(f"No ThingNode found for ID {tn_id}")


def get_single_source_from_db(src_id: UUID) -> Source:
    with get_session()() as session:
        source = session.query(SourceOrm).filter(SourceOrm.id == src_id).one_or_none()
        if source:
            return Source.from_orm_model(source)

    raise DBNotFoundError(f"No Source found for ID {src_id}")


def get_single_sink_from_db(sink_id: UUID) -> Sink:
    with get_session()() as session:
        sink = session.query(SinkOrm).filter(SinkOrm.id == sink_id).one_or_none()
        if sink:
            return Sink.from_orm_model(sink)

    raise DBNotFoundError(f"No Sink found for ID {sink_id}")

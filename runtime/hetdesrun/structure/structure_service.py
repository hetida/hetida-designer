from uuid import UUID

from hetdesrun.structure.db import get_session
from hetdesrun.persistence.dbmodels import SinkOrm, SourceOrm, ThingNodeOrm
from hetdesrun.structure.models import Sink, Source, ThingNode
from hetdesrun.structure.db.exceptions import DBNotFoundError


def get_children(parent_id: UUID | None) -> tuple[list[ThingNode], list[Source], list[Sink]]:
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
        sinks = (
            session.query(SinkOrm).filter(SinkOrm.thing_node_id == parent_id).all()
        )

        if not child_nodes and not sources and not sinks:
            raise DBNotFoundError(f"No children, sources, or sinks found for parent_id {parent_id}")

        return (
            [ThingNode.from_orm_model(node) for node in child_nodes],
            [Source.from_orm_model(source) for source in sources],
            [Sink.from_orm_model(sink) for sink in sinks]
        )

from uuid import UUID

from hetdesrun.persistence.db_engine_and_session import SQLAlchemySession, get_session
from hetdesrun.persistence.structure_service_dbmodels import (
    ElementTypeOrm,
    SinkOrm,
    SourceOrm,
    ThingNodeOrm,
)
from hetdesrun.structure.db.exceptions import DBNotFoundError
from hetdesrun.structure.models import Sink, Source, ThingNode


def get_children(
    parent_id: UUID | None,
) -> tuple[list[ThingNode], list[Source], list[Sink]]:
    with get_session()() as session:
        if parent_id == None:
            root_nodes = (
                session.query(ThingNodeOrm).filter(ThingNodeOrm.parent_node_id.is_(None)).all()
            )
            return ([ThingNode.from_orm_model(node) for node in root_nodes], [], [])

        child_nodes = (
            session.query(ThingNodeOrm).filter(ThingNodeOrm.parent_node_id == parent_id).all()
        )

        sources = session.query(SourceOrm).filter(SourceOrm.thing_node_id == parent_id).all()
        sinks = session.query(SinkOrm).filter(SinkOrm.thing_node_id == parent_id).all()

        if not child_nodes and not sources and not sinks:
            raise DBNotFoundError(f"No children, sources, or sinks found for parent_id {parent_id}")

        return (
            [ThingNode.from_orm_model(node) for node in child_nodes],
            [Source.from_orm_model(source) for source in sources],
            [Sink.from_orm_model(sink) for sink in sinks],
        )


def get_single_thingnode_from_db(tn_id: UUID) -> ThingNode:
    with get_session()() as session:
        thing_node = session.query(ThingNodeOrm).filter(ThingNodeOrm.id == tn_id).one_or_none()
        if thing_node:
            return ThingNode.from_orm_model(thing_node)

    raise DBNotFoundError(f"No ThingNode found for ID {tn_id}")


def get_collection_of_thingnodes_from_db(tn_ids: list[UUID]) -> dict[UUID, ThingNode]:
    return {tn_id: get_single_thingnode_from_db(tn_id) for tn_id in tn_ids}


def get_single_source_from_db(src_id: UUID) -> Source:
    with get_session()() as session:
        source = session.query(SourceOrm).filter(SourceOrm.id == src_id).one_or_none()
        if source:
            return Source.from_orm_model(source)

    raise DBNotFoundError(f"No Source found for ID {src_id}")


def get_collection_of_sources_from_db(src_ids: list[UUID]) -> dict[UUID, Source]:
    return {src_id: get_single_source_from_db(src_id) for src_id in src_ids}


def get_single_sink_from_db(sink_id: UUID) -> Sink:
    with get_session()() as session:
        sink = session.query(SinkOrm).filter(SinkOrm.id == sink_id).one_or_none()
        if sink:
            return Sink.from_orm_model(sink)

    raise DBNotFoundError(f"No Sink found for ID {sink_id}")


def get_collection_of_sinks_from_db(sink_ids: list[UUID]) -> dict[UUID, Sink]:
    return {sink_id: get_single_sink_from_db(sink_id) for sink_id in sink_ids}


# def delete_structure() -> None:
#     with get_session()() as session:
#         try:
#             root_node = (
#                 session.query(ThingNodeOrm)
#                 .filter(ThingNodeOrm.parent_node_id == None)
#                 .one_or_none()
#             )
#             if root_node:
#                 _delete_structure_recursive(session, root_node.id)

#             element_types = session.query(ElementTypeOrm).all()
#             for element_type in element_types:
#                 session.delete(element_type)

#             session.commit()
#         except Exception as e:
#             session.rollback()
#             raise e


# def _delete_structure_recursive(session: SQLAlchemySession, node_id: UUID) -> None:
#     child_nodes = session.query(ThingNodeOrm).filter(ThingNodeOrm.parent_node_id == node_id).all()

#     for child_node in child_nodes:
#         _delete_structure_recursive(session, child_node.id)

#     sources_to_delete = (
#         session.query(SourceOrm)
#         .join(ThingNodeSourceAssociation)
#         .filter(ThingNodeSourceAssociation.thing_node_id == node_id)
#         .all()
#     )
#     sinks_to_delete = (
#         session.query(SinkOrm)
#         .join(ThingNodeSinkAssociation)
#         .filter(ThingNodeSinkAssociation.thing_node_id == node_id)
#         .all()
#     )

#     for source in sources_to_delete:
#         session.query(ThingNodeSourceAssociation).filter_by(source_id=source.id).delete()
#         session.delete(source)
#     for sink in sinks_to_delete:
#         session.query(ThingNodeSinkAssociation).filter_by(sink_id=sink.id).delete()
#         session.delete(sink)

#     remaining_sources = session.query(SourceOrm).filter(SourceOrm.thing_node_id == node_id).all()
#     remaining_sinks = session.query(SinkOrm).filter(SinkOrm.thing_node_id == node_id).all()

#     for source in remaining_sources:
#         session.delete(source)
#     for sink in remaining_sinks:
#         session.delete(sink)

#     node_to_delete = session.query(ThingNodeOrm).filter(ThingNodeOrm.id == node_id).one_or_none()
#     if node_to_delete:
#         session.delete(node_to_delete)

#     orphaned_sources = session.query(SourceOrm).filter(SourceOrm.thing_node_id == None).all()
#     orphaned_sinks = session.query(SinkOrm).filter(SinkOrm.thing_node_id == None).all()

#     for source in orphaned_sources:
#         session.delete(source)
#     for sink in orphaned_sinks:
#         session.delete(sink)

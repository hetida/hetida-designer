from uuid import UUID

from sqlalchemy import delete

from hetdesrun.persistence.db_engine_and_session import SQLAlchemySession, get_session
from hetdesrun.persistence.structure_service_dbmodels import (
    ElementTypeOrm,
    SinkOrm,
    SourceOrm,
    ThingNodeOrm,
    thingnode_sink_association,
    thingnode_source_association,
)
from hetdesrun.structure.db.exceptions import DBNotFoundError
from hetdesrun.structure.db.orm_service import delete_structure as orm_delete_structure
from hetdesrun.structure.db.orm_service import (
    fetch_all_element_types,
    fetch_all_sinks,
    fetch_all_sources,
    fetch_all_thing_nodes,
)
from hetdesrun.structure.db.orm_service import is_database_empty as orm_is_database_empty
from hetdesrun.structure.db.orm_service import update_structure as orm_update_structure
from hetdesrun.structure.models import CompleteStructure, Sink, Source, ThingNode


def get_children(
    parent_id: UUID | None,
) -> tuple[list[ThingNode], list[Source], list[Sink]]:
    """Retrieves the child nodes, sources, and sinks associated with a given parent node from the database.

    If `parent_id` is None, it returns the root nodes (nodes without a parent). Otherwise, it fetches the direct
    child nodes, sources, and sinks associated with the specified parent node.
    """
    with get_session()() as session:
        if parent_id is None:
            root_nodes = (
                session.query(ThingNodeOrm).filter(ThingNodeOrm.parent_node_id.is_(None)).all()
            )
            return ([ThingNode.from_orm_model(node) for node in root_nodes], [], [])

        child_nodes = (
            session.query(ThingNodeOrm).filter(ThingNodeOrm.parent_node_id == parent_id).all()
        )

        sources = (
            session.query(SourceOrm)
            .join(
                thingnode_source_association,
                thingnode_source_association.c.source_id == SourceOrm.id,
            )
            .filter(thingnode_source_association.c.thing_node_id == parent_id)
            .all()
        )

        sinks = (
            session.query(SinkOrm)
            .join(thingnode_sink_association, thingnode_sink_association.c.sink_id == SinkOrm.id)
            .filter(thingnode_sink_association.c.thing_node_id == parent_id)
            .all()
        )

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


def get_all_sources_from_db() -> list[Source]:
    with get_session()() as session:
        sources = session.query(SourceOrm).all()
    return [Source.from_orm_model(source) for source in sources]


def get_collection_of_sources_from_db(src_ids: list[UUID]) -> dict[UUID, Source]:
    return {src_id: get_single_source_from_db(src_id) for src_id in src_ids}


def get_single_sink_from_db(sink_id: UUID) -> Sink:
    with get_session()() as session:
        sink = session.query(SinkOrm).filter(SinkOrm.id == sink_id).one_or_none()
        if sink:
            return Sink.from_orm_model(sink)

    raise DBNotFoundError(f"No Sink found for ID {sink_id}")


def get_all_sinks_from_db() -> list[Sink]:
    with get_session()() as session:
        sinks = session.query(SinkOrm).all()
    return [Sink.from_orm_model(sink) for sink in sinks]


def get_collection_of_sinks_from_db(sink_ids: list[UUID]) -> dict[UUID, Sink]:
    return {sink_id: get_single_sink_from_db(sink_id) for sink_id in sink_ids}


def is_database_empty() -> bool:
    """Wrapper function to check if the database is empty."""
    return orm_is_database_empty()


def delete_structure() -> None:
    """Wrapper function to delete the entire structure in the database."""
    with get_session()() as session:
        orm_delete_structure(session)


def update_structure(
    complete_structure: CompleteStructure,
) -> CompleteStructure:
    """Wrapper function to update or insert the given complete structure into the database."""
    updated_structure = orm_update_structure(complete_structure)

    return updated_structure

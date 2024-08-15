import logging
from uuid import UUID

from hetdesrun.persistence.db_engine_and_session import get_session
from hetdesrun.persistence.structure_service_dbmodels import (
    SinkOrm,
    SourceOrm,
    ThingNodeOrm,
    thingnode_sink_association,
    thingnode_source_association,
)
from hetdesrun.structure.db.exceptions import DBNotFoundError
from hetdesrun.structure.db.orm_service import delete_structure as orm_delete_structure
from hetdesrun.structure.db.orm_service import is_database_empty as orm_is_database_empty
from hetdesrun.structure.db.orm_service import update_structure as orm_update_structure
from hetdesrun.structure.models import CompleteStructure, Sink, Source, ThingNode

logger = logging.getLogger(__name__)


def get_children(
    parent_id: UUID | None,
) -> tuple[list[ThingNode], list[Source], list[Sink]]:
    """
    Retrieves the child nodes, sources, and sinks associated  with a given parent
    node from the database.

    If `parent_id` is None, it returns the root nodes (nodes without a parent).
    Otherwise, it fetches the direct child nodes, sources, and sinks associated
    with the specified parent node.
    """

    msg = f"Fetching children for parent_id: {parent_id}."
    logger.debug(msg)

    with get_session()() as session:
        if parent_id is None:
            msg = "No parent_id provided, fetching root nodes."
            logger.debug(msg)
            root_nodes = (
                session.query(ThingNodeOrm).filter(ThingNodeOrm.parent_node_id.is_(None)).all()
            )
            msg = f"Fetched {len(root_nodes)} root nodes."
            logger.debug(msg)
            return ([ThingNode.from_orm_model(node) for node in root_nodes], [], [])

        msg = f"Fetching child nodes for parent_id: {parent_id}."
        logger.debug(msg)
        child_nodes = (
            session.query(ThingNodeOrm).filter(ThingNodeOrm.parent_node_id == parent_id).all()
        )
        msg = f"Fetched {len(child_nodes)} child nodes."
        logger.debug(msg)

        msg = f"Fetching sources for parent_id: {parent_id}."
        logger.debug(msg)
        sources = (
            session.query(SourceOrm)
            .join(
                thingnode_source_association,
                thingnode_source_association.c.source_id == SourceOrm.id,
            )
            .filter(thingnode_source_association.c.thing_node_id == parent_id)
            .all()
        )
        msg = f"Fetched {len(sources)} sources."
        logger.debug(msg)

        msg = f"Fetching sinks for parent_id: {parent_id}."
        logger.debug(msg)
        sinks = (
            session.query(SinkOrm)
            .join(thingnode_sink_association, thingnode_sink_association.c.sink_id == SinkOrm.id)
            .filter(thingnode_sink_association.c.thing_node_id == parent_id)
            .all()
        )
        msg = f"Fetched {len(sinks)} sinks."
        logger.debug(msg)

        msg = (
            f"Returning {len(child_nodes)} child nodes, {len(sources)} sources, "
            f"and {len(sinks)} sinks for parent_id: {parent_id}."
        )
        logger.debug(msg)

        return (
            [ThingNode.from_orm_model(node) for node in child_nodes],
            [Source.from_orm_model(source) for source in sources],
            [Sink.from_orm_model(sink) for sink in sinks],
        )


def get_single_thingnode_from_db(tn_id: UUID) -> ThingNode:
    msg = f"Fetching single ThingNode from database with ID: {tn_id}."
    logger.debug(msg)
    with get_session()() as session:
        thing_node = session.query(ThingNodeOrm).filter(ThingNodeOrm.id == tn_id).one_or_none()
        if thing_node:
            msg = f"ThingNode with ID {tn_id} found."
            logger.debug(msg)
            return ThingNode.from_orm_model(thing_node)

    msg = f"No ThingNode found for ID {tn_id}. Raising DBNotFoundError."
    logger.error(msg)
    raise DBNotFoundError(f"No ThingNode found for ID {tn_id}")


def get_collection_of_thingnodes_from_db(tn_ids: list[UUID]) -> dict[UUID, ThingNode]:
    msg = f"Fetching collection of ThingNodes with IDs: {tn_ids}."
    logger.debug(msg)
    thingnodes = {tn_id: get_single_thingnode_from_db(tn_id) for tn_id in tn_ids}
    msg = f"Successfully fetched collection of ThingNodes."
    logger.debug(msg)
    return thingnodes


def get_single_source_from_db(src_id: UUID) -> Source:
    msg = f"Fetching single Source from database with ID: {src_id}."
    logger.debug(msg)
    with get_session()() as session:
        source = session.query(SourceOrm).filter(SourceOrm.id == src_id).one_or_none()
        if source:
            msg = f"Source with ID {src_id} found."
            logger.debug(msg)
            return Source.from_orm_model(source)

    msg = f"No Source found for ID {src_id}. Raising DBNotFoundError."
    logger.error(msg)
    raise DBNotFoundError(f"No Source found for ID {src_id}")


def get_all_sources_from_db() -> list[Source]:
    msg = "Fetching all Sources from the database."
    logger.debug(msg)
    with get_session()() as session:
        sources = session.query(SourceOrm).all()

    msg = f"Successfully fetched {len(sources)} sources from the database."
    logger.debug(msg)
    return [Source.from_orm_model(source) for source in sources]


def get_collection_of_sources_from_db(src_ids: list[UUID]) -> dict[UUID, Source]:
    msg = f"Fetching collection of Sources with IDs: {src_ids}."
    logger.debug(msg)
    sources = {src_id: get_single_source_from_db(src_id) for src_id in src_ids}

    msg = f"Successfully fetched collection of Sources."
    logger.debug(msg)
    return sources


def get_single_sink_from_db(sink_id: UUID) -> Sink:
    msg = f"Fetching single Sink from database with ID: {sink_id}."
    logger.debug(msg)
    with get_session()() as session:
        sink = session.query(SinkOrm).filter(SinkOrm.id == sink_id).one_or_none()
        if sink:
            msg = f"Sink with ID {sink_id} found."
            logger.debug(msg)
            return Sink.from_orm_model(sink)

    msg = f"No Sink found for ID {sink_id}. Raising DBNotFoundError."
    logger.error(msg)
    raise DBNotFoundError(f"No Sink found for ID {sink_id}")


def get_all_sinks_from_db() -> list[Sink]:
    msg = "Fetching all Sinks from the database."
    logger.debug(msg)
    with get_session()() as session:
        sinks = session.query(SinkOrm).all()

    msg = f"Successfully fetched {len(sinks)} sinks from the database."
    logger.debug(msg)
    return [Sink.from_orm_model(sink) for sink in sinks]


def get_collection_of_sinks_from_db(sink_ids: list[UUID]) -> dict[UUID, Sink]:
    msg = f"Fetching collection of Sinks with IDs: {sink_ids}."
    logger.debug(msg)

    sinks = {sink_id: get_single_sink_from_db(sink_id) for sink_id in sink_ids}
    msg = f"Successfully fetched collection of Sinks."
    logger.debug(msg)
    return sinks


def is_database_empty() -> bool:
    """Wrapper function to check if the database is empty."""

    msg = "Checking if the database is empty."
    logger.debug(msg)
    is_empty = orm_is_database_empty()
    msg = f"Database is {'empty' if is_empty else 'not empty'}."
    logger.debug(msg)
    return is_empty


def delete_structure() -> None:
    """Wrapper function to delete the entire structure in the database."""
    msg = "Deleting the entire structure from the database."
    logger.debug(msg)
    with get_session()() as session:
        orm_delete_structure(session)
    msg = "Successfully deleted the entire structure from the database."
    logger.debug(msg)


def update_structure(
    complete_structure: CompleteStructure,
) -> CompleteStructure:
    """Wrapper function to update or insert the given complete structure into the database."""
    msg = "Updating or inserting the complete structure into the database."
    logger.debug(msg)
    updated_structure = orm_update_structure(complete_structure)
    msg = "Successfully updated or inserted the complete structure into the database."
    logger.debug(msg)
    return updated_structure

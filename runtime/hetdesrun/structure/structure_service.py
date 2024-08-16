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
from hetdesrun.structure.db.orm_service import (
    orm_delete_structure,
    orm_is_database_empty,
    orm_update_structure,
)
from hetdesrun.structure.models import CompleteStructure, Sink, Source, ThingNode

logger = logging.getLogger(__name__)


def get_children(
    parent_id: UUID | None,
) -> tuple[list[ThingNode], list[Source], list[Sink]]:
    """
    Retrieves the child nodes, sources, and sinks associated with a given parent
    node from the database.

    If `parent_id` is None, it returns the root nodes (nodes without a parent),
    along with any sources and sinks associated with the root nodes. Otherwise,
    it fetches the direct child nodes, sources, and sinks associated with the
    specified parent node.
    """

    logger.debug("Fetching children for parent_id: %s", parent_id)

    with get_session()() as session:
        if parent_id is None:
            logger.debug("No parent_id provided, fetching root nodes.")
            root_nodes = (
                session.query(ThingNodeOrm).filter(ThingNodeOrm.parent_node_id.is_(None)).all()
            )
            logger.debug("Fetched %d root nodes.", len(root_nodes))

            root_node_ids = [node.id for node in root_nodes]

            logger.debug("Fetching sources associated with root nodes.")
            sources = (
                session.query(SourceOrm)
                .join(
                    thingnode_source_association,
                    thingnode_source_association.c.source_id == SourceOrm.id,
                )
                .filter(thingnode_source_association.c.thing_node_id.in_(root_node_ids))
                .all()
            )
            logger.debug("Fetched %d sources associated with root nodes.", len(sources))

            logger.debug("Fetching sinks associated with root nodes.")
            sinks = (
                session.query(SinkOrm)
                .join(
                    thingnode_sink_association,
                    thingnode_sink_association.c.sink_id == SinkOrm.id,
                )
                .filter(thingnode_sink_association.c.thing_node_id.in_(root_node_ids))
                .all()
            )
            logger.debug("Fetched %d sinks associated with root nodes.", len(sinks))

            return (
                [ThingNode.from_orm_model(node) for node in root_nodes],
                [Source.from_orm_model(source) for source in sources],
                [Sink.from_orm_model(sink) for sink in sinks],
            )

        logger.debug("Fetching child nodes for parent_id: %s", parent_id)
        child_nodes = (
            session.query(ThingNodeOrm).filter(ThingNodeOrm.parent_node_id == parent_id).all()
        )
        logger.debug("Fetched %d child nodes.", len(child_nodes))

        logger.debug("Fetching sources for parent_id: %s", parent_id)
        sources = (
            session.query(SourceOrm)
            .join(
                thingnode_source_association,
                thingnode_source_association.c.source_id == SourceOrm.id,
            )
            .filter(thingnode_source_association.c.thing_node_id == parent_id)
            .all()
        )
        logger.debug("Fetched %d sources.", len(sources))

        logger.debug("Fetching sinks for parent_id: %s", parent_id)
        sinks = (
            session.query(SinkOrm)
            .join(thingnode_sink_association, thingnode_sink_association.c.sink_id == SinkOrm.id)
            .filter(thingnode_sink_association.c.thing_node_id == parent_id)
            .all()
        )
        logger.debug("Fetched %d sinks.", len(sinks))

        logger.debug(
            "Returning %d child nodes, %d sources, and %d sinks for parent_id: %s",
            len(child_nodes),
            len(sources),
            len(sinks),
            parent_id,
        )

        return (
            [ThingNode.from_orm_model(node) for node in child_nodes],
            [Source.from_orm_model(source) for source in sources],
            [Sink.from_orm_model(sink) for sink in sinks],
        )


def get_single_thingnode_from_db(tn_id: UUID) -> ThingNode:
    logger.debug("Fetching single ThingNode from database with ID: %s", tn_id)
    with get_session()() as session:
        thing_node = session.query(ThingNodeOrm).filter(ThingNodeOrm.id == tn_id).one_or_none()
        if thing_node:
            logger.debug("ThingNode with ID %s found.", tn_id)
            return ThingNode.from_orm_model(thing_node)

    logger.error("No ThingNode found for ID %s. Raising DBNotFoundError.", tn_id)
    raise DBNotFoundError("No ThingNode found for ID %s" % tn_id)


def get_collection_of_thingnodes_from_db(tn_ids: list[UUID]) -> dict[UUID, ThingNode]:
    logger.debug("Fetching collection of ThingNodes with IDs: %s", tn_ids)
    thingnodes = {tn_id: get_single_thingnode_from_db(tn_id) for tn_id in tn_ids}
    logger.debug("Successfully fetched collection of ThingNodes.")
    return thingnodes


def get_single_source_from_db(src_id: UUID) -> Source:
    logger.debug("Fetching single Source from database with ID: %s", src_id)
    with get_session()() as session:
        source = session.query(SourceOrm).filter(SourceOrm.id == src_id).one_or_none()
        if source:
            logger.debug("Source with ID %s found.", src_id)
            return Source.from_orm_model(source)

    logger.error("No Source found for ID %s. Raising DBNotFoundError.", src_id)
    raise DBNotFoundError("No Source found for ID %s" % src_id)


def get_all_sources_from_db() -> list[Source]:
    logger.debug("Fetching all Sources from the database.")
    with get_session()() as session:
        sources = session.query(SourceOrm).all()

    logger.debug("Successfully fetched %d sources from the database.", len(sources))
    return [Source.from_orm_model(source) for source in sources]


def get_collection_of_sources_from_db(src_ids: list[UUID]) -> dict[UUID, Source]:
    logger.debug("Fetching collection of Sources with IDs: %s", src_ids)
    sources = {src_id: get_single_source_from_db(src_id) for src_id in src_ids}

    logger.debug("Successfully fetched collection of Sources.")
    return sources


def get_single_sink_from_db(sink_id: UUID) -> Sink:
    logger.debug("Fetching single Sink from database with ID: %s", sink_id)
    with get_session()() as session:
        sink = session.query(SinkOrm).filter(SinkOrm.id == sink_id).one_or_none()
        if sink:
            logger.debug("Sink with ID %s found.", sink_id)
            return Sink.from_orm_model(sink)

    logger.error("No Sink found for ID %s. Raising DBNotFoundError.", sink_id)
    raise DBNotFoundError("No Sink found for ID %s" % sink_id)


def get_all_sinks_from_db() -> list[Sink]:
    logger.debug("Fetching all Sinks from the database.")
    with get_session()() as session:
        sinks = session.query(SinkOrm).all()

    logger.debug("Successfully fetched %d sinks from the database.", len(sinks))
    return [Sink.from_orm_model(sink) for sink in sinks]


def get_collection_of_sinks_from_db(sink_ids: list[UUID]) -> dict[UUID, Sink]:
    logger.debug("Fetching collection of Sinks with IDs: %s", sink_ids)

    sinks = {sink_id: get_single_sink_from_db(sink_id) for sink_id in sink_ids}
    logger.debug("Successfully fetched collection of Sinks.")
    return sinks


def is_database_empty() -> bool:
    """Wrapper function to check if the database is empty."""

    logger.debug("Checking if the database is empty.")
    is_empty = orm_is_database_empty()
    logger.debug("Database is %s.", "empty" if is_empty else "not empty")
    return is_empty


def delete_structure() -> None:
    """Wrapper function to delete the entire structure in the database."""
    logger.debug("Deleting the entire structure from the database.")
    with get_session()() as session:
        orm_delete_structure(session)
    logger.debug("Successfully deleted the entire structure from the database.")


def update_structure(
    complete_structure: CompleteStructure,
) -> CompleteStructure:
    """Wrapper function to update or insert the given complete structure into the database."""
    logger.debug("Updating or inserting the complete structure into the database.")
    updated_structure = orm_update_structure(complete_structure)
    logger.debug("Successfully updated or inserted the complete structure into the database.")
    return updated_structure

import json
import logging
from collections import defaultdict, deque
from collections.abc import Sequence
from typing import Any
from uuid import UUID

from sqlalchemy import Table, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy_utils import UUIDType

from hetdesrun.persistence.db_engine_and_session import SQLAlchemySession, get_session
from hetdesrun.persistence.structure_service_dbmodels import (
    ElementTypeOrm,
    SinkOrm,
    SourceOrm,
    ThingNodeOrm,
    thingnode_sink_association,
    thingnode_source_association,
)
from hetdesrun.structure.db.exceptions import DBIntegrityError, DBNotFoundError
from hetdesrun.structure.models import (
    CompleteStructure,
    ElementType,
    Sink,
    Source,
    ThingNode,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Fetch Functions


def fetch_all_element_types(session: SQLAlchemySession) -> list[ElementTypeOrm]:
    element_types = session.query(ElementTypeOrm).all()
    msg = f"Fetched {len(element_types)} element types from the database."
    logger.debug(msg)
    return element_types


def fetch_all_thing_nodes(session: SQLAlchemySession) -> list[ThingNodeOrm]:
    thing_nodes = session.query(ThingNodeOrm).all()
    msg = f"Fetched {len(thing_nodes)} thing nodes from the database"
    logger.debug(msg)
    return thing_nodes


def fetch_all_sources(session: SQLAlchemySession) -> list[SourceOrm]:
    sources = session.query(SourceOrm).all()
    msg = f"Fetched {len(sources)} sources from the database."
    logger.debug(msg)
    return sources


def fetch_all_sinks(session: SQLAlchemySession) -> list[SinkOrm]:
    sinks = session.query(SinkOrm).all()
    msg = f"Fetched {len(sinks)} sinks from the database."
    logger.debug(msg)
    return sinks


def fetch_et_by_id(
    session: SQLAlchemySession,
    id: UUID,  # noqa: A002
) -> ElementTypeOrm:
    msg = f"Fetching element type by ID {id}."
    logger.debug(msg)
    result: ElementTypeOrm | None = (
        session.query(ElementTypeOrm).filter(ElementTypeOrm.id == id).one_or_none()
    )
    if result is None:
        msg = f"Found no element type in database with id {id}"
        logger.error(msg)
        raise DBNotFoundError(msg)

    return result


def fetch_et_by_external_id(
    session: SQLAlchemySession, external_id: str, stakeholder_key: str
) -> ElementTypeOrm:
    msg = (
        f"Fetching element type by external ID {external_id} and stakeholder key {stakeholder_key}."
    )
    logger.debug(msg)
    result: ElementTypeOrm | None = (
        session.query(ElementTypeOrm)
        .filter(
            ElementTypeOrm.external_id == external_id,
            ElementTypeOrm.stakeholder_key == stakeholder_key,
        )
        .one_or_none()
    )

    if result is None:
        msg = (
            f"Found no element type in database with external_id {external_id} "
            f"and stakeholder_key {stakeholder_key}"
        )
        logger.error(msg)
        raise DBNotFoundError(msg)

    return result


def fetch_tn_by_id(
    session: SQLAlchemySession,
    id: UUID,  # noqa: A002
) -> ThingNodeOrm:
    msg = f"Fetching thing nodes by ID {id}."
    logger.debug(msg)
    result: ThingNodeOrm | None = (
        session.query(ThingNodeOrm).filter(ThingNodeOrm.id == id).one_or_none()
    )

    if result is None:
        msg = f"Found no thing node in database with id {id}"
        logger.error(msg)
        raise DBNotFoundError(msg)

    return result


def fetch_tn_by_external_id(
    session: SQLAlchemySession, external_id: str, stakeholder_key: str
) -> ThingNodeOrm:
    msg = (
        f"Fetching thing nodes by external ID {external_id} and stakeholder key {stakeholder_key}."
    )
    logger.debug(msg)
    result: ThingNodeOrm | None = (
        session.query(ThingNodeOrm)
        .filter(
            ThingNodeOrm.external_id == external_id, ThingNodeOrm.stakeholder_key == stakeholder_key
        )
        .one_or_none()
    )

    if result is None:
        msg = (
            f"Found no thing node in database with external_id {external_id} "
            f"and stakeholder_key {stakeholder_key}"
        )
        logger.error(msg)
        raise DBNotFoundError(msg)

    return result


def fetch_tn_child_ids_by_parent_id(
    session: SQLAlchemySession, parent_id: UUID | None
) -> list[UUID]:
    msg = f"Fetching child IDs for parent node ID {parent_id}."
    logger.debug(msg)
    results = session.query(ThingNodeOrm.id).filter(ThingNodeOrm.parent_node_id == parent_id).all()

    if not results:
        msg = f"No children found for thingnode with parent_id {parent_id}"
        logger.error(msg)
        raise DBNotFoundError(msg)
    # Extracts the UUIDs from the list of tuples
    # returned by the query and returns them as a flat list.
    return [result[0] for result in results]


def fetch_source_by_id(
    session: SQLAlchemySession,
    id: UUID,  # noqa: A002
) -> SourceOrm:
    msg = f"Fetching source by ID {id}"
    logger.debug(msg)
    result: SourceOrm | None = session.query(SourceOrm).filter(SourceOrm.id == id).one_or_none()

    if result is None:
        msg = f"Found no source in database with id {id}"
        logger.error(msg)
        raise DBNotFoundError(msg)

    return result


def fetch_source_by_external_id(
    session: SQLAlchemySession, external_id: str, stakeholder_key: str
) -> SourceOrm:
    result: SourceOrm | None = (
        session.query(SourceOrm)
        .filter(SourceOrm.external_id == external_id, SourceOrm.stakeholder_key == stakeholder_key)
        .one_or_none()
    )
    msg = f"Fetching source by external ID {external_id} and stakeholder key {stakeholder_key}."
    logger.debug(msg)
    if result is None:
        msg = (
            f"Found no source in database with external_id {external_id} "
            f"and stakeholder_key {stakeholder_key}"
        )
        logger.error(msg)
        raise DBNotFoundError(msg)

    return result


def fetch_sink_by_id(
    session: SQLAlchemySession,
    id: UUID,  # noqa: A002
) -> SinkOrm:
    msg = f"Fetching sink by ID: {id}"
    logger.debug(msg)
    result: SinkOrm | None = session.query(SinkOrm).filter(SinkOrm.id == id).one_or_none()

    if result is None:
        msg = f"Found no sink in database with id {id}"
        logger.error(msg)
        raise DBNotFoundError

    return result


def fetch_sink_by_external_id(
    session: SQLAlchemySession, external_id: str, stakeholder_key: str
) -> SinkOrm:
    msg = f"Fetching sink by external ID {external_id} and stakeholder key {stakeholder_key}."
    logger.debug(msg)
    result: SinkOrm | None = (
        session.query(SinkOrm)
        .filter(SinkOrm.external_id == external_id, SinkOrm.stakeholder_key == stakeholder_key)
        .one_or_none()
    )

    if result is None:
        msg = (
            f"Found no sink in database with external_id {external_id} "
            f"and stakeholder_key {stakeholder_key}"
        )
        logger.error(msg)
        raise DBNotFoundError(msg)

    return result


# Element Type Services


def add_et(session: SQLAlchemySession, element_type_orm: ElementTypeOrm) -> None:
    # This function is intended to be used as a helper within session-managed operations
    # and should not be called directly without proper session handling.
    msg = f"Adding ElementType with ID {element_type_orm.id}."
    logger.debug(msg)
    try:
        session.add(element_type_orm)
        session.flush()
        msg = f"ElementType with id {element_type_orm.id} added successfully."
        logger.debug(msg)
    except IntegrityError as e:
        msg = (
            f"Integrity Error while trying to store ElementType "
            f"with id {element_type_orm.id}. Error was:\n{str(e)}"
        )
        logger.error(msg)
        raise DBIntegrityError(msg) from e


def store_single_element_type(
    element_type: ElementType,
) -> None:
    msg = f"Storing ElementType with id {element_type.id}."
    logger.debug(msg)
    with get_session()() as session, session.begin():
        orm_et = element_type.to_orm_model()
        add_et(session, orm_et)


def read_single_element_type(
    id: UUID,  # noqa: A002
) -> ElementType:
    msg = f"Fetching ElementType by id: {id}"
    logger.debug(msg)
    with get_session()() as session, session.begin():
        orm_et = fetch_et_by_id(session, id)
        return ElementType.from_orm_model(orm_et)


def read_single_element_type_by_external_id(external_id: str, stakeholder_key: str) -> ElementType:
    msg = (
        f"Fetching ElementType by external ID: {external_id} and stakeholder key: {stakeholder_key}"
    )
    logger.debug(msg)
    with get_session()() as session, session.begin():
        orm_et = fetch_et_by_external_id(session, external_id, stakeholder_key)
        return ElementType.from_orm_model(orm_et)


def delete_et(id: UUID) -> None:  # noqa: A002
    msg = f"Attempting to delete ElementType with id {id}."
    logger.debug(msg)
    with get_session()() as session, session.begin():
        try:
            msg = f"Fetching ElementType with id {id} from the database."
            logger.debug(msg)
            element_type = fetch_et_by_id(session, id)
            if element_type.thing_nodes:
                session.rollback()
                msg = f"Cannot delete ElementType with id {id} as it has associated ThingNodes."
                logger.error(msg)
                raise DBIntegrityError(msg)

            msg = f"Deleting ElementType with id {id}."
            logger.debug(msg)
            session.delete(element_type)
            session.commit()
            msg = f"Successfully deleted ElementType with id {id}."
            logger.debug(msg)

        except NoResultFound as e:
            session.rollback()
            msg = f"No ElementType found with id {id}."
            logger.error(msg)
            raise DBNotFoundError(msg) from e
        except IntegrityError as e:
            session.rollback()

            msg = f"Database integrity error while deleting Elementtype with id {id}: {str(e)}"
            logger.error(msg)
            raise DBIntegrityError(msg) from e


def delete_et_cascade(id: UUID) -> None:  # noqa: A002
    # The delete_et_cascade function differs from delete_et in that it also deletes all
    # associated ThingNode records before deleting the ElementType,
    # performing a cascading delete operation.
    with get_session()() as session, session.begin():
        msg = f"Attempting to perform cascading delete for ElementType with id {id}."
        logger.debug(msg)

        try:
            msg = f"Fetching ElementType with id {id} from the database."
            logger.debug(msg)
            element_type = fetch_et_by_id(session, id)

            msg = f"Deleting associated ThingNodes for ElementType with id {id}."
            logger.debug(msg)
            for thing_node in element_type.thing_nodes:
                session.delete(thing_node)

            msg = f"Deleting ElementType with id {id}."
            logger.debug(msg)
            session.delete(element_type)
            session.commit()
            msg = f"Successfully performed cascading delete for ElementType with id {id}."
            logger.debug(msg)

        except NoResultFound as e:
            session.rollback()
            msg = f"No ElementType found with id {id}."
            logger.error(msg)
            raise DBNotFoundError(msg) from e
        except IntegrityError as e:
            session.rollback()
            msg = f"Database integrity error while deleting ElementType with id {id}: {str(e)}"
            logger.error(msg)
            raise DBIntegrityError(msg) from e
        except Exception as e:
            session.rollback()
            msg = f"Unexpected error while deleting ElementType with id {id}: {str(e)}"
            logger.error(msg)
            raise


def update_et(
    id: UUID,  # noqa: A002
    et_update: ElementType,
) -> None:
    msg = f"Attempting to update ElementType with id {id}."
    logger.debug(msg)
    with get_session()() as session, session.begin():
        try:
            msg = f"Fetching ElementType with id {id} from the database."
            logger.debug(msg)
            element_type = fetch_et_by_id(session, id)
            if element_type:
                msg = f"Updating ElementType with id {id}."
                logger.debug(msg)
                for attr, value in et_update.dict(exclude_unset=True).items():
                    msg = f"Setting attribute {attr} to {value} for ElementType with id {id}."
                    logger.debug(msg)
                    setattr(element_type, attr, value)

                msg = f"Successfully updated ElementType with id {id}."
                logger.debug(msg)

        except NoResultFound as e:
            session.rollback()
            msg = f"No ElementType found with id {id}."
            logger.error(msg)
            raise DBNotFoundError(msg) from e


# Thing Node Services


def add_tn(session: SQLAlchemySession, thingnode_orm: ThingNodeOrm) -> None:
    # This function is intended to be used as a helper within session-managed operations
    # and should not be called directly without proper session handling.
    try:
        msg = f"Attempting to add ThingNode with id {thingnode_orm.id} to the session."
        logger.debug(msg)
        session.add(thingnode_orm)
        session.flush()
        msg = f"Successfully added ThingNode with id {thingnode_orm.id}."
        logger.debug(msg)
    except IntegrityError as e:
        msg = (
            f"Integrity Error while trying to store thingnode "
            f"with id {thingnode_orm.id}. Error was:\n{str(e)}"
        )
        logger.error(msg)
        raise DBIntegrityError(msg) from e


def store_single_thingnode(
    thingnode: ThingNode,
) -> None:
    msg = f"Storing single ThingNode with external_id {thingnode.external_id}."
    logger.debug(msg)
    with get_session()() as session, session.begin():
        orm_tn = thingnode.to_orm_model()
        add_tn(session, orm_tn)
        msg = f"Successfully stored ThingNode with id {orm_tn.id}."
        logger.debug(msg)


def read_single_thingnode(
    id: UUID,  # noqa: A002
) -> ThingNode:
    msg = f"Reading single ThingNode with id {id}."
    logger.debug(msg)
    with get_session()() as session, session.begin():
        orm_tn = fetch_tn_by_id(session, id)
        msg = f"Successfully read ThingNode with id {id}."
        logger.debug(msg)
        return ThingNode.from_orm_model(orm_tn)


def read_single_thingnode_by_external_id(external_id: str, stakeholder_key: str) -> ThingNode:
    msg = (
        f"Reading single ThingNode with external_id {external_id}"
        f" and stakeholder_key {stakeholder_key}."
    )
    logger.debug(msg)
    with get_session()() as session, session.begin():
        orm_tn = fetch_tn_by_external_id(session, external_id, stakeholder_key)
        msg = (
            f"Successfully read ThingNode with external_id {external_id}"
            f" and stakeholder_key {stakeholder_key}."
        )
        logger.debug(msg)
        return ThingNode.from_orm_model(orm_tn)


def delete_tn(id: UUID) -> None:  # noqa: A002
    msg = f"Attempting to delete ThingNode with id {id}."
    logger.debug(msg)
    with get_session()() as session, session.begin():
        try:
            # Fetch the ThingNode to be deleted
            thingnode = fetch_tn_by_id(session, id)
            msg = f"Fetched ThingNode with id {id} for deletion."
            logger.debug(msg)

            # Remove associations with sources
            sources = (
                session.query(SourceOrm).filter(SourceOrm.thing_nodes.any(id=thingnode.id)).all()
            )
            for source in sources:
                msg = (
                    f"Removing association with Source id {source.id}"
                    f" from ThingNode id {thingnode.id}."
                )
                logger.debug(msg)
                source.thing_nodes.remove(thingnode)

            # Remove associations with sinks
            sinks = session.query(SinkOrm).filter(SinkOrm.thing_nodes.any(id=thingnode.id)).all()
            for sink in sinks:
                msg = (
                    f"Removing association with Sink id {sink.id} from ThingNode id {thingnode.id}."
                )
                logger.debug(msg)
                sink.thing_nodes.remove(thingnode)

            # Recursively delete child ThingNodes
            children = (
                session.query(ThingNodeOrm)
                .filter(ThingNodeOrm.parent_node_id == thingnode.id)
                .all()
            )
            for child in children:
                msg = f"Recursively deleting child ThingNode with id {child.id}."
                logger.debug(msg)
                delete_tn(child.id)

            # Delete the ThingNode itself
            session.delete(thingnode)
            session.commit()
            msg = f"Successfully deleted ThingNode with id {id}."
            logger.debug(msg)

        except Exception as e:
            session.rollback()
            msg = f"Unexpected error while deleting ThingNode with id {id}: {str(e)}"
            logger.error(msg)
            raise


def update_tn(
    id: UUID,  # noqa: A002
    tn_update: ThingNode,
) -> ThingNode:
    msg = f"Attempting to update ThingNode with id {id}."
    logger.debug(msg)
    with get_session()() as session, session.begin():
        try:
            thingnode = fetch_tn_by_id(session, id)
            if thingnode:
                msg = f"ThingNode with id {id} found. Updating attributes."
                logger.debug(msg)
                for attr, value in tn_update.dict(exclude_unset=True).items():
                    msg = f"Setting attribute '{attr}' to '{value}'."
                    logger.debug(msg)
                    setattr(thingnode, attr, value)
            session.flush()
            msg = f"Successfully updated ThingNode with id {id}."
            logger.debug(msg)
            return ThingNode.from_orm_model(thingnode)
        except NoResultFound as e:
            session.rollback()
            msg = f"No ThingNode found with {id}."
            logger.error(msg)
            raise DBNotFoundError(msg) from e


def get_parent_tn_id(
    session: SQLAlchemySession,
    id: UUID,  # noqa: A002
) -> UUIDType | None:
    msg = f"Fetching parent ID for ThingNode with id {id}."
    logger.debug(msg)
    try:
        thingnode = fetch_tn_by_id(session, id)
        if thingnode:
            msg = f"Parent ID for ThingNode with id {id} is {thingnode.parent_node_id}."
            logger.debug(msg)
            return thingnode.parent_node_id
        msg = f"ThingNode with id {id} has no parent."
        logger.debug(msg)
        return None
    except DBNotFoundError:
        msg = f"Found no parent node in database for thingnode with id {id}"
        logger.error(msg)
        raise


def get_children_tn_ids(id: UUID) -> list[UUID]:  # noqa: A002
    msg = f"Fetching children IDs for ThingNode with id {id}."
    logger.debug(msg)
    with get_session()() as session, session.begin():
        try:
            thingnode = fetch_tn_by_id(session, id)
            results = fetch_tn_child_ids_by_parent_id(session, thingnode.id)
            msg = f"Found {len(results)} children for ThingNode with id {id}."
            logger.debug(msg)
            return results
        except DBNotFoundError:
            msg = f"No ThingNode found with id {id}. Returning empty list of children."
            logger.error(msg)
            return []


def get_ancestors_tn_ids(
    id: UUID,  # noqa: A002
    depth: int = -1,
) -> list[UUID]:
    """Retrieves the IDs of all ancestor ThingNodes up to a specified depth."""
    msg = f"Fetching ancestors for ThingNode with id {id} up to depth {depth}."
    logger.debug(msg)
    ancestors_ids = []
    current_depth = 0
    current_id = id
    with get_session()() as session, session.begin():
        try:
            # Traverse up the hierarchy, stopping if the root is
            # reached or the specified depth is exceeded
            while current_id and (depth == -1 or current_depth < depth):
                ancestors_ids.append(current_id)
                msg = f"Adding ThingNode with id {current_id} to ancestors list."
                logger.debug(msg)
                thingnode = fetch_tn_by_id(session, current_id)  # Fetch the current node
                if thingnode.parent_node_id is None:
                    msg = f"Reached root node with id {current_id}. Stopping traversal."
                    logger.debug(msg)
                    break
                current_id = thingnode.parent_node_id  # noqa: A001
                current_depth += 1
        except DBNotFoundError as e:
            msg = f"Error while evaluating hierarchy for id {id}: {str(e)}"
            logger.error(msg)
            raise
    msg = f"Found {len(ancestors_ids)} ancestors for ThingNode with id {id}."
    logger.debug(msg)
    return ancestors_ids


def get_descendants_tn_ids(
    id: UUID,  # noqa: A002
    depth: int = -1,
) -> list[UUID]:
    """Retrieves the IDs of all descendant ThingNodes up to a specified depth."""
    msg = f"Fetching descendants for ThingNode with id {id} up to depth {depth}."
    logger.debug(msg)
    descendant_ids = []
    nodes_to_visit = [(id, 0)]  # Stack to keep track of nodes to visit, starting with the root node

    with get_session()() as session, session.begin():
        try:
            while nodes_to_visit:
                current_id, current_depth = nodes_to_visit.pop()  # Get the next node to visit
                if current_id is None or (depth != -1 and current_depth >= depth):
                    msg = f"Skipping node with id {current_id} at depth {current_depth}."
                    logger.debug(msg)
                    continue
                try:
                    # Fetch the child nodes of the current node
                    child_ids = fetch_tn_child_ids_by_parent_id(session, current_id)
                except DBNotFoundError:
                    if current_depth == 0:
                        msg = f"No children found for thingnode with parent_id {current_id}"
                        logger.error(msg)
                    continue
                # Add each child node's ID to the list of descendants
                # and queue them for further exploration
                for child_id in child_ids:
                    msg = f"Adding ThingNode with id {child_id} to descendants list."
                    logger.debug(msg)
                    descendant_ids.append(child_id)
                    nodes_to_visit.append((child_id, current_depth + 1))
        except DBNotFoundError as e:
            msg = f"Error while fetching descendants for id {current_id}: {str(e)}"
            logger.error(msg)
            raise
    msg = f"Found {len(descendant_ids)} descendants for ThingNode with id {id}."
    logger.debug(msg)
    return descendant_ids


# Source Services


def add_source(session: SQLAlchemySession, source_orm: SourceOrm) -> None:
    # This function is intended to be used as a helper within session-managed operations
    # and should not be called directly without proper session handling.
    msg = f"Attempting to add Source with id {source_orm.id} to the session."
    logger.debug(msg)
    try:
        session.add(source_orm)
        session.flush()
        msg = f"Successfully added Source with id {source_orm.id}."
        logger.debug(msg)
    except IntegrityError as e:
        msg = (
            f"Integrity Error while trying to store source "
            f"with id {source_orm.id}. Error was:\n{str(e)}"
        )
        logger.error(msg)
        raise DBIntegrityError(msg) from e


def store_single_source(source: Source) -> None:
    msg = f"Storing single Source with external_id {source.external_id}."
    logger.debug(msg)
    with get_session()() as session, session.begin():
        orm_source = source.to_orm_model()
        add_source(session, orm_source)
        msg = f"Successfully stored Source with id {orm_source.id}."
        logger.debug(msg)


def read_single_source(
    id: UUID,  # noqa: A002
) -> Source:
    msg = f"Reading single Source with id {id}."
    logger.debug(msg)
    with get_session()() as session, session.begin():
        orm_source = fetch_source_by_id(session, id)
        msg = f"Successfully read Source with id {id}."
        logger.debug(msg)
        return Source.from_orm_model(orm_source)


def read_single_source_by_external_id(external_id: str, stakeholder_key: str) -> Source:
    msg = (
        f"Reading single Source with external_id {external_id} "
        f"and stakeholder_key {stakeholder_key}."
    )
    logger.debug(msg)
    with get_session()() as session, session.begin():
        orm_source = fetch_source_by_external_id(session, external_id, stakeholder_key)
        msg = (
            f"Successfully read Source with external_id {external_id} "
            f"and stakeholder_key {stakeholder_key}."
        )
        logger.debug(msg)
        return Source.from_orm_model(orm_source)


def update_source(
    id: UUID,  # noqa: A002
    source_update: Source,
) -> Source:
    msg = f"Updating Source with id {id}."
    logger.debug(msg)
    with get_session()() as session, session.begin():
        try:
            source = session.query(SourceOrm).filter(SourceOrm.id == id).one()
            for attr, value in source_update.dict(exclude_unset=True).items():
                setattr(source, attr, value)
            session.flush()
            msg = f"Successfully updated Source with id {id}."
            logger.debug(msg)
            return Source.from_orm_model(source)
        except NoResultFound as e:
            session.rollback()
            msg = f"No Source found with id {id}."
            logger.error(msg)
            raise DBNotFoundError(msg) from e


def delete_source(id: UUID) -> None:  # noqa: A002
    msg = f"Attempting to delete Source with id {id}."
    logger.debug(msg)
    with get_session()() as session, session.begin():
        try:
            source = fetch_source_by_id(session, id)
            msg = f"Fetched Source with id {id} for deletion."
            logger.debug(msg)
            session.delete(source)
            session.commit()
            msg = f"Successfully deleted Source with id {id}."
            logger.debug(msg)
        except Exception as e:
            session.rollback()
            msg = f"Unexpected error while deleteing Source with id {id}: {str(e)}"
            logger.error(msg)
            raise


# Sink Services


def add_sink(session: SQLAlchemySession, sink_orm: SinkOrm) -> None:
    # This function is intended to be used as a helper within session-managed operations
    # and should not be called directly without proper session handling.
    msg = f"Attempting to add Sink with id {sink_orm.id} to the session."
    logger.debug(msg)
    try:
        session.add(sink_orm)
        session.flush()
        msg = f"Successfully added Sink with id {sink_orm.id}."
        logger.debug(msg)
    except IntegrityError as e:
        msg = (
            f"Integrity Error while trying to store sink "
            f"with id {sink_orm.id}. Error was:\n{str(e)}"
        )
        logger.error(msg)
        raise DBIntegrityError(msg) from e


def store_single_sink(sink: Sink) -> None:
    msg = f"Storing single Sink with external_id {sink.external_id}."
    logger.debug(msg)
    with get_session()() as session, session.begin():
        orm_sink = sink.to_orm_model()
        add_sink(session, orm_sink)
        msg = f"Successfully stored Sink with id {orm_sink.id}."
        logger.debug(msg)


def read_single_sink(
    id: UUID,  # noqa: A002
) -> Sink:
    msg = f"Reading single Sink with id {id}."
    logger.debug(msg)
    with get_session()() as session, session.begin():
        orm_sink = fetch_sink_by_id(session, id)
        msg = f"Successfully read Sink with id {id}."
        logger.debug(msg)
        return Sink.from_orm_model(orm_sink)


def read_single_sink_by_external_id(external_id: str, stakeholder_key: str) -> Sink:
    msg = (
        f"Reading single Sink with external_id {external_id} "
        f"and stakeholder_key {stakeholder_key}."
    )
    logger.debug(msg)
    with get_session()() as session, session.begin():
        orm_sink = fetch_sink_by_external_id(session, external_id, stakeholder_key)
        msg = (
            f"Successfully read Sink with external_id {external_id} "
            f"and stakeholder_key {stakeholder_key}."
        )
        logger.debug(msg)
        return Sink.from_orm_model(orm_sink)


def update_sink(
    id: UUID,  # noqa: A002
    sink_update: Sink,
) -> Sink:
    msg = f"Updating Sink with id {id}."
    logger.debug(msg)
    with get_session()() as session, session.begin():
        try:
            sink = session.query(SinkOrm).filter(SinkOrm.id == id).one()
            for attr, value in sink_update.dict(exclude_unset=True).items():
                setattr(sink, attr, value)
            session.flush()
            msg = f"Successfully updated Sink with id {id}."
            logger.debug(msg)
            return Sink.from_orm_model(sink)
        except NoResultFound as e:
            session.rollback()
            msg = f"No Sink found with id {id}."
            logger.error(msg)
            raise DBNotFoundError(msg) from e


def delete_sink(id: UUID) -> None:  # noqa: A002
    msg = f"Attempting to delete Sink with id {id}."
    logger.debug(msg)
    with get_session()() as session, session.begin():
        try:
            sink = fetch_sink_by_id(session, id)
            msg = f"Fetched Sink with id {id} for deletion."
            logger.debug(msg)
            session.delete(sink)
            session.commit()
            msg = f"Successfully deleted Sink with id {id}."
            logger.debug(msg)
        except Exception as e:
            session.rollback()
            msg = f"Unexpected error while deleting Sink with id {id}: {str(e)}"
            logger.error(msg)
            raise


# Structure Services


def load_structure_from_json_file(
    file_path: str,
) -> CompleteStructure:
    msg = f"Loading structure from JSON file at {file_path}."
    logger.debug(msg)
    try:
        with open(file_path) as file:
            structure_json = json.load(file)
        msg = f"Successfully loaded JSON from {file_path}."
        logger.debug(msg)
        complete_structure = CompleteStructure(**structure_json)
        msg = "Successfully created CompleteStructure from JSON data."
        logger.debug(msg)
        return complete_structure
    except Exception as e:
        msg = f"Failed to load or parse structure from {file_path}: {str(e)}"
        logger.error(msg)
        raise


def sort_thing_nodes_from_db(
    thing_nodes: list[ThingNode], existing_thing_nodes: dict[str, ThingNodeOrm]
) -> dict[int, list[ThingNode]]:
    """
    This function sorts a list of ThingNodes into hierarchical levels using
    existing ThingNode data fetched from the database. It ensures that the
    existing database IDs are retained for each node. The function does not directly
    access the database but relies on the provided existing_thing_nodes.
    """
    msg = "Starting to sort ThingNodes into hierarchical levels."
    logger.debug(msg)
    msg = f"Number of ThingNodes to process: {len(thing_nodes)}"
    logger.debug(msg)
    msg = f"Number of existing ThingNodes: {len(existing_thing_nodes)}"
    logger.debug(msg)

    # Map existing ThingNodes from the database to a dictionary using a unique key
    existing_node_map = {
        (node.stakeholder_key or "") + (node.external_id or ""): node
        for node in existing_thing_nodes.values()
    }

    msg = f"Mapped existing ThingNodes to keys: {list(existing_node_map.keys())}"
    logger.debug(msg)

    # Assign existing IDs to new nodes if they match by stakeholder_key + external_id
    for node in thing_nodes:
        key = node.stakeholder_key + node.external_id
        existing_node = existing_node_map.get(key)
        if existing_node:
            node.id = existing_node.id  # Retain the existing ID for the node
            msg = f"Node {node.name} matched with existing node, ID retained: {node.id}"
            logger.debug(msg)

    # Initialize a dictionary to hold the children of each node, and an empty list for root nodes
    children_by_node_id: dict[UUID, list[ThingNode]] = {node.id: [] for node in thing_nodes}
    root_nodes = []

    # Iterate through each node to populate the children list or identify root nodes
    for node in thing_nodes:
        if node.parent_node_id:
            if node.parent_node_id not in children_by_node_id:
                children_by_node_id[node.parent_node_id] = []
            children_by_node_id[node.parent_node_id].append(node)
            msg = f"Node {node.name} added as child to parent ID: {node.parent_node_id}"
            logger.debug(msg)
        else:
            root_nodes.append(node)
            msg = f"Node {node.name} identified as root node."
            logger.debug(msg)

    # Dictionary to hold nodes sorted by their hierarchical levels
    sorted_nodes_by_level = defaultdict(list)
    # Queue for breadth-first traversal, starting with root nodes
    queue = deque([(root_nodes, 0)])

    # Perform breadth-first traversal to sort nodes by levels
    while queue:
        current_level_nodes, level = queue.popleft()
        next_level_nodes = []

        msg = f"Processing level {level} with {len(current_level_nodes)} nodes."
        logger.debug(msg)

        for node in current_level_nodes:
            # Add the current node to its respective level in the sorted dictionary
            sorted_nodes_by_level[level].append(node)
            if node.id in children_by_node_id:
                # Sort the children nodes by their external_id
                children_by_node_id[node.id].sort(key=lambda x: x.external_id)
                # Prepare the nodes for the next level of traversal
                next_level_nodes.extend(children_by_node_id[node.id])

                msg = (
                    f"Node {node.name} at level {level}"
                    f" has {len(children_by_node_id[node.id])} children."
                )
                logger.debug(msg)

        if next_level_nodes:
            msg = f"Queueing {len(next_level_nodes)} nodes for next level {level + 1}."
            logger.debug(msg)
            # Queue the next level nodes for processing
            queue.append((next_level_nodes, level + 1))

    msg = "Completed sorting ThingNodes into hierarchical levels."
    logger.debug(msg)
    return sorted_nodes_by_level


def fill_all_thingnode_element_type_ids_from_db(
    thing_nodes: list[ThingNode], existing_element_types: dict[str, ElementTypeOrm]
) -> None:
    """
    This function fills the element_type_id for each ThingNode using element types
    that have already been fetched from the database. The function itself does not
    query the database but relies on the provided existing_element_types.
    """
    msg = (
        "Filling element_type_id for each ThingNode using existing element types from the database."
    )
    logger.debug(msg)
    for node in thing_nodes:
        if node.element_type_external_id:
            key = node.stakeholder_key + node.element_type_external_id
            db_et = existing_element_types.get(key)
            if db_et:
                node.element_type_id = db_et.id
                msg = (
                    f"Set element_type_id {db_et.id} for ThingNode"
                    " with external_id {node.external_id}."
                )
                logger.debug(msg)


def fill_all_thingnode_parent_uuids_from_db(
    thing_nodes: list[ThingNode], existing_thing_nodes: dict[str, ThingNodeOrm]
) -> None:
    """
    This function assigns parent_node_id for each ThingNode using parent nodes
    that have already been fetched from the database. It does not perform any direct
    database operations but works with the provided existing_thing_nodes.
    """
    msg = (
        "Assigning parent_node_id for each ThingNode using existing parent nodes from the database."
    )
    logger.debug(msg)
    for node in thing_nodes:
        if node.parent_external_node_id:
            key = node.stakeholder_key + node.parent_external_node_id
            db_parent_tn = existing_thing_nodes.get(key)
            if db_parent_tn:
                node.parent_node_id = db_parent_tn.id
                msg = f"Set parent_node_id for ThingNode with external_id {node.external_id}."
                logger.debug(msg)
            else:
                # If the parent node is not found in the existing_thing_nodes,
                # use a generator expression to search through thing_nodes.
                # The generator searches for the first node that matches
                # both the parent_external_node_id and stakeholder_key.
                parent_node = next(
                    (
                        n
                        for n in thing_nodes
                        if n.external_id == node.parent_external_node_id
                        and n.stakeholder_key == node.stakeholder_key
                    ),
                    None,
                )
                if parent_node:
                    node.parent_node_id = parent_node.id
                    msg = (
                        f"Found parent node in thing_nodes and set parent_node_id {parent_node.id}"
                        "for ThingNode with external_id {node.external_id}."
                    )
                    logger.debug(msg)


def fill_source_sink_associations_db(
    complete_structure: CompleteStructure, session: SQLAlchemySession
) -> None:
    """
    Establishes associations between ThingNodes and their corresponding Sources and Sinks
    based on existing records in the database.

    This function ensures that all sources and sinks within the provided CompleteStructure
    are correctly associated with their respective ThingNodes in the database. It first
    retrieves existing ThingNodes, Sources, and Sinks from the database and maps them using
    their stakeholder keys and external IDs. Then, for each Source and Sink in the
    CompleteStructure, it checks whether an association with a ThingNode already exists in
    the database. If not, the function creates the necessary association.
    """

    msg = "Establishing associations between ThingNodes and their corresponding Sources and Sinks."
    logger.debug(msg)

    # Fetch existing ThingNodes from the database
    existing_thing_nodes = {
        tn.stakeholder_key + tn.external_id: tn for tn in session.query(ThingNodeOrm).all()
    }
    msg = f"Fetched {len(existing_thing_nodes)} existing ThingNodes from the database."
    logger.debug(msg)

    # Fetch existing Sources from the database
    existing_sources = {
        src.stakeholder_key + src.external_id: src for src in session.query(SourceOrm).all()
    }
    msg = f"Fetched {len(existing_sources)} existing Sources from the database."
    logger.debug(msg)

    # Fetch existing Sinks from the database
    existing_sinks = {
        snk.stakeholder_key + snk.external_id: snk for snk in session.query(SinkOrm).all()
    }
    msg = f"Fetched {len(existing_sinks)} existing Sinks from the database."
    logger.debug(msg)

    def process_db_associations(
        entities: list[Source | Sink],
        existing_entities: dict[str, Source | Sink],
        assoc_table: Table,
        entity_key: str,
    ) -> None:
        msg = f"Processing associations for {len(entities)} entities."
        logger.debug(msg)
        for entity in entities:
            if not entity.thing_node_external_ids:
                msg = (
                    f"Skipping entity with external_id {entity.external_id}"
                    " as it has no associated ThingNodes."
                )
                logger.debug(msg)
                continue
            for tn_external_id in entity.thing_node_external_ids:
                tn_key = entity.stakeholder_key + tn_external_id
                thing_node = existing_thing_nodes.get(tn_key)
                if not thing_node:
                    msg = f"ThingNode with key {tn_key} not found in existing ThingNodes, skipping."
                    logger.debug(msg)
                    continue
                thing_node_id = thing_node.id
                entity_key_full = entity.stakeholder_key + entity.external_id
                db_entity = existing_entities.get(entity_key_full)
                if not db_entity:
                    msg = (
                        f"Entity with key {entity_key_full} not"
                        " found in existing entities, skipping."
                    )
                    logger.debug(msg)
                    continue
                entity_id = db_entity.id
                association_exists = (
                    session.query(assoc_table)
                    .filter_by(thing_node_id=thing_node_id, **{entity_key: entity_id})
                    .first()
                )
                if association_exists:
                    msg = (
                        f"Association already exists between ThingNode id {thing_node_id}"
                        " and {entity_key} id {entity_id}."
                    )
                    logger.debug(msg)
                else:
                    association = {
                        "thing_node_id": thing_node_id,
                        entity_key: entity_id,
                    }
                    session.execute(assoc_table.insert().values(association))
                    msg = (
                        f"Created new association between ThingNode id {thing_node_id}"
                        " and {entity_key} id {entity_id}."
                    )
                    logger.debug(msg)

    msg = "Processing associations for Sources."
    logger.debug(msg)
    process_db_associations(
        complete_structure.sources,  # type: ignore
        existing_sources,
        thingnode_source_association,
        "source_id",
    )

    msg = "Processing associations for Sinks."
    logger.debug(msg)
    process_db_associations(
        complete_structure.sinks,  # type: ignore
        existing_sinks,
        thingnode_sink_association,
        "sink_id",
    )

    msg = (
        "Completed establishing associations between ThingNodes"
        " and their corresponding Sources and Sinks."
    )
    logger.debug(msg)


def update_structure_from_file(file_path: str) -> CompleteStructure:
    msg = f"Updating structure from JSON file at path: {file_path}."
    logger.debug(msg)
    complete_structure = load_structure_from_json_file(file_path)
    msg = "Successfully loaded structure from JSON file."
    logger.debug(msg)
    return update_structure(complete_structure)


def update_structure(complete_structure: CompleteStructure) -> CompleteStructure:
    """
    This function updates or inserts the given complete structure into the database.
    """
    msg = "Starting update or insert operation for the complete structure in the database."
    logger.debug(msg)

    with get_session()() as session, session.begin():
        msg = "Fetching existing records from the database."
        logger.debug(msg)

        existing_element_types = fetch_existing_records(session, ElementTypeOrm)
        existing_thing_nodes = fetch_existing_records(session, ThingNodeOrm)
        existing_sources = fetch_existing_records(session, SourceOrm)
        existing_sinks = fetch_existing_records(session, SinkOrm)

        with session.no_autoflush:
            msg = "Updating or creating element types."
            logger.debug(msg)
            update_or_create_element_types(
                complete_structure.element_types, existing_element_types, session
            )
            session.flush()

            update_existing_elements(session, ElementTypeOrm, existing_element_types)

            msg = "Filling in element type IDs for thing nodes."
            logger.debug(msg)
            fill_all_thingnode_element_type_ids_from_db(
                complete_structure.thing_nodes, existing_element_types
            )

            msg = "Filling in parent node IDs for thing nodes."
            logger.debug(msg)
            fill_all_thingnode_parent_uuids_from_db(
                complete_structure.thing_nodes, existing_thing_nodes
            )

            msg = "Sorting and flattening the thing nodes hierarchy."
            logger.debug(msg)
            sorted_thing_nodes = sort_and_flatten_thing_nodes(
                complete_structure.thing_nodes, existing_thing_nodes
            )

            msg = "Updating or creating thing nodes."
            logger.debug(msg)
            update_or_create_thing_nodes(sorted_thing_nodes, existing_thing_nodes, session)
            session.flush()

            update_existing_elements(session, ThingNodeOrm, existing_thing_nodes)
            session.flush()

            msg = "Updating or creating sources."
            logger.debug(msg)
            update_or_create_sources_or_sinks(complete_structure.sources, existing_sources, session)
            session.flush()

            msg = "Updating or creating sinks."
            logger.debug(msg)
            update_or_create_sources_or_sinks(complete_structure.sinks, existing_sinks, session)
            session.flush()

            msg = "Establishing associations between thing nodes, sources, and sinks."
            logger.debug(msg)
            fill_source_sink_associations_db(complete_structure, session)

    msg = "Completed update or insert operation for the complete structure."
    logger.debug(msg)
    return complete_structure


def fetch_existing_records(session: SQLAlchemySession, model_class: Any) -> dict[str, Any]:
    """
    Fetches all records of the specified model class from the database and returns them as a
    dictionary with keys composed of stakeholder_key and external_id.
    """
    msg = f"Fetching all records for model class {model_class.__name__} from the database."
    logger.debug(msg)
    try:
        # Fetch all records of the given model class from the database
        records = session.query(model_class).all()
        msg = f"Fetched {len(records)} records for model class {model_class.__name__}."
        logger.debug(msg)
        # Create a dictionary mapping stakeholder_key + external_id to the record
        return {rec.stakeholder_key + rec.external_id: rec for rec in records}
    except Exception as e:
        # Log the error and re-raise the exception if something goes wrong
        msg = f"Error fetching records for model class {model_class.__name__}: {str(e)}"
        logger.error(msg)
        raise


def update_or_create_element_types(
    elements: list[ElementType],
    existing_elements: dict[str, ElementTypeOrm],
    session: SQLAlchemySession,
) -> None:
    msg = f"Updating or creating {len(elements)} element types."
    logger.debug(msg)
    for element in elements:
        key = element.stakeholder_key + element.external_id
        db_element = existing_elements.get(key)
        if db_element:
            msg = f"Updating existing element with key {key}."
            logger.debug(msg)
            element.id = db_element.id  # Set the existing ID
            db_element.name = element.name
            db_element.description = element.description
            db_element.stakeholder_key = element.stakeholder_key
        else:
            msg = f"Creating new element with key {key}."
            logger.debug(msg)
            new_element = element.to_orm_model()
            session.add(new_element)


def update_existing_elements(
    session: SQLAlchemySession, model_class: Any, existing_elements: dict[str, Any]
) -> None:
    """
    Updates the existing_elements dictionary with records
    from the database for the specified model class.
    """
    msg = f"Updating existing elements dictionary for model class {model_class.__name__}."
    logger.debug(msg)
    try:
        # Query the database for all records of the specified model class
        new_elements = {
            el.stakeholder_key + el.external_id: el for el in session.query(model_class).all()
        }
        # Update the existing_elements dictionary with the new elements from the database
        existing_elements.update(new_elements)
        msg = (
            "Successfully updated existing elements dictionary"
            f" for model class {model_class.__name__}."
        )
        logger.debug(msg)
    except Exception as e:
        # Log the error and re-raise the exception if something goes wrong
        msg = f"Error updating existing elements for model class {model_class.__name__}: {str(e)}"
        logger.error(msg)
        raise


def sort_and_flatten_thing_nodes(
    thing_nodes: list[ThingNode], existing_thing_nodes: dict[str, ThingNodeOrm]
) -> list[ThingNode]:
    msg = "Sorting and flattening thing nodes."
    logger.debug(msg)
    sorted_nodes_by_level = sort_thing_nodes_from_db(thing_nodes, existing_thing_nodes)
    flattened_nodes = [node for nodes in sorted_nodes_by_level.values() for node in nodes]
    # Flattening the list of nodes is necessary to convert the hierarchical structure
    # into a single, ordered list.
    msg = f"Flattened thing nodes into a list of {len(flattened_nodes)} nodes."
    logger.debug(msg)
    return flattened_nodes


def update_or_create_thing_nodes(
    thing_nodes: list[ThingNode],
    existing_thing_nodes: dict[str, ThingNodeOrm],
    session: SQLAlchemySession,
) -> None:
    """
    Updates existing thing nodes, or creates new ones if they do not exist.
    """
    msg = f"Updating or creating {len(thing_nodes)} thing nodes."
    logger.debug(msg)
    for node in thing_nodes:
        key = node.stakeholder_key + node.external_id
        db_node = existing_thing_nodes.get(key)
        if db_node:
            msg = f"Updating existing thing node with key {key}."
            logger.debug(msg)
            node.id = db_node.id  # Set the existing ID
            db_node.name = node.name
            db_node.description = node.description
            db_node.element_type_id = node.element_type_id
            db_node.meta_data = node.meta_data
            db_node.parent_node_id = (
                node.parent_node_id if node.parent_node_id else db_node.parent_node_id
            )
        else:
            msg = f"Creating new thing node with key {key}."
            logger.debug(msg)
            new_node = node.to_orm_model()
            session.add(new_node)


def update_or_create_sources_or_sinks(
    sources_or_sinks: Sequence[Source | Sink],
    existing_items: dict[str, SourceOrm | SinkOrm],
    session: SQLAlchemySession,
) -> None:
    """
    Updates existing source or sink items, or creates new ones if they do not exist.
    """
    msg = f"Updating or creating {len(sources_or_sinks)} sources or sinks."
    logger.debug(msg)
    for item in sources_or_sinks:
        key = item.stakeholder_key + item.external_id
        db_item = existing_items.get(key)
        if db_item:
            msg = f"Updating existing item with key {key}."
            logger.debug(msg)
            item.id = db_item.id  # Set the existing ID
            db_item.name = item.name
            db_item.type = item.type
            db_item.visible = item.visible
            db_item.adapter_key = item.adapter_key
            if isinstance(db_item, SourceOrm) and isinstance(item, Source):
                db_item.source_id = item.source_id
            elif isinstance(db_item, SinkOrm) and isinstance(item, Sink):
                db_item.sink_id = item.sink_id
            db_item.meta_data = item.meta_data
            db_item.preset_filters = item.preset_filters
            db_item.passthrough_filters = item.passthrough_filters
            db_item.thing_node_external_ids = item.thing_node_external_ids
        else:
            msg = f"Creating new item with key {key}."
            logger.debug(msg)
            new_item = item.to_orm_model()
            session.add(new_item)


def delete_structure(session: SQLAlchemySession) -> None:
    msg = "Deleting all structure data from the database."
    logger.debug(msg)
    try:
        # List of all ORM classes to delete
        tables = [
            thingnode_source_association,
            thingnode_sink_association,
            ThingNodeOrm,
            SourceOrm,
            SinkOrm,
            ElementTypeOrm,
        ]

        # Delete all records in each table
        for table in tables:
            msg = f"Deleting records from table {table}."
            logger.debug(msg)
            session.execute(delete(table))

        session.commit()
    except Exception as e:
        session.rollback()
        msg = f"Error during structure deletion: {str(e)}"
        logger.error(msg)
        raise


def is_database_empty() -> bool:
    msg = "Checking if the database is empty."
    logger.debug(msg)
    with get_session()() as session:
        element_types = fetch_all_element_types(session)
        thing_nodes = fetch_all_thing_nodes(session)
        sources = fetch_all_sources(session)
        sinks = fetch_all_sinks(session)
        # TODO: Shorten function by only checking for ElementTypes?

    is_empty = not (element_types or thing_nodes or sources or sinks)
    msg = f"Database empty status: {is_empty}"
    logger.debug(msg)

    return is_empty

import json
import logging
from collections import defaultdict, deque
from typing import Any, Type
from uuid import UUID

from sqlalchemy import Table, delete, text
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


# Fetch Functions


def fetch_all_element_types(session: SQLAlchemySession) -> list[ElementTypeOrm]:
    return session.query(ElementTypeOrm).all()


def fetch_all_thing_nodes(session: SQLAlchemySession) -> list[ThingNodeOrm]:
    return session.query(ThingNodeOrm).all()


def fetch_all_sources(session: SQLAlchemySession) -> list[SourceOrm]:
    return session.query(SourceOrm).all()


def fetch_all_sinks(session: SQLAlchemySession) -> list[SinkOrm]:
    return session.query(SinkOrm).all()


def fetch_et_by_id(
    session: SQLAlchemySession,
    id: UUID,  # noqa: A002
    log_error: bool = True,
) -> ElementTypeOrm:
    result: ElementTypeOrm | None = (
        session.query(ElementTypeOrm).filter(ElementTypeOrm.id == id).one_or_none()
    )

    if result is None:
        msg = f"Found no element type in database with id {id}"
        if log_error:
            logger.error(msg)
        raise DBNotFoundError(msg)

    return result


def fetch_et_by_external_id(
    session: SQLAlchemySession,
    external_id: str,
    stakeholder_key: str,
    log_error: bool = True,
) -> ElementTypeOrm:
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

        if log_error:
            logger.error(msg)
        raise DBNotFoundError(msg)

    return result


def fetch_tn_by_id(
    session: SQLAlchemySession,
    id: UUID,  # noqa: A002
    log_error: bool = True,
) -> ThingNodeOrm:
    result: ThingNodeOrm | None = (
        session.query(ThingNodeOrm).filter(ThingNodeOrm.id == id).one_or_none()
    )

    if result is None:
        msg = f"Found no thing node in database with id {id}"
        if log_error:
            logger.error(msg)
        raise DBNotFoundError(msg)

    return result


def fetch_tn_by_external_id(
    session: SQLAlchemySession,
    external_id: str,
    stakeholder_key: str,
    log_error: bool = True,
) -> ThingNodeOrm:
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

        if log_error:
            logger.error(msg)
        raise DBNotFoundError(msg)

    return result


def fetch_tn_child_ids_by_parent_id(
    session: SQLAlchemySession, parent_id: UUID | None, log_error: bool = True
) -> list[UUID]:
    results = session.query(ThingNodeOrm.id).filter(ThingNodeOrm.parent_node_id == parent_id).all()

    if not results and log_error:
        msg = f"No children found for thingnode with parent_id {parent_id}"
        logger.error(msg)
        raise DBNotFoundError(msg)
    # Extracts the UUIDs from the list of tuples returned by the query and returns them as a flat list.
    return [result[0] for result in results]


def fetch_source_by_id(
    session: SQLAlchemySession,
    id: UUID,  # noqa: A002
    log_error: bool = True,
) -> SourceOrm:
    result: SourceOrm | None = session.query(SourceOrm).filter(SourceOrm.id == id).one_or_none()

    if result is None:
        msg = f"Found no source in database with id {id}"
        if log_error:
            logger.error(msg)
        raise DBNotFoundError(msg)

    return result


def fetch_source_by_external_id(
    session: SQLAlchemySession,
    external_id: str,
    stakeholder_key: str,
    log_error: bool = True,
) -> SourceOrm:
    result: SourceOrm | None = (
        session.query(SourceOrm)
        .filter(SourceOrm.external_id == external_id, SourceOrm.stakeholder_key == stakeholder_key)
        .one_or_none()
    )

    if result is None:
        msg = (
            f"Found no source in database with external_id {external_id} "
            f"and stakeholder_key {stakeholder_key}"
        )

        if log_error:
            logger.error(msg)
        raise DBNotFoundError(msg)

    return result


def fetch_sink_by_id(
    session: SQLAlchemySession,
    id: UUID,  # noqa: A002
    log_error: bool = True,
) -> SinkOrm:
    result: SinkOrm | None = session.query(SinkOrm).filter(SinkOrm.id == id).one_or_none()

    if result is None:
        msg = f"Found no sink in database with id {id}"
        if log_error:
            logger.error(msg)
        raise DBNotFoundError

    return result


def fetch_sink_by_external_id(
    session: SQLAlchemySession,
    external_id: str,
    stakeholder_key: str,
    log_error: bool = True,
) -> SinkOrm:
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

        if log_error:
            logger.error(msg)
        raise DBNotFoundError(msg)

    return result


# Element Type Services


def add_et(session: SQLAlchemySession, element_type_orm: ElementTypeOrm) -> None:
    # This function is intended to be used as a helper within session-managed operations
    # and should not be called directly without proper session handling.
    try:
        session.add(element_type_orm)
        session.flush()
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
    with get_session()() as session, session.begin():
        orm_et = element_type.to_orm_model()
        add_et(session, orm_et)


def read_single_element_type(
    id: UUID,  # noqa: A002
    log_error: bool = True,
) -> ElementType:
    with get_session()() as session, session.begin():
        orm_et = fetch_et_by_id(session, id, log_error)
        return ElementType.from_orm_model(orm_et)


def read_single_element_type_by_external_id(
    external_id: str,
    stakeholder_key: str,
    log_error: bool = True,
) -> ElementType:
    with get_session()() as session, session.begin():
        orm_et = fetch_et_by_external_id(session, external_id, stakeholder_key, log_error)
        return ElementType.from_orm_model(orm_et)


def delete_et(id: UUID, log_error: bool = True) -> None:  # noqa: A002
    with get_session()() as session, session.begin():
        try:
            element_type = fetch_et_by_id(session, id, log_error)
            if element_type.thing_nodes:
                session.rollback()
                if log_error:
                    msg = f"Cannot delete ElementType with id {id} as it has associated ThingNodes."
                    logger.error(msg)
                raise DBIntegrityError(msg)

            session.delete(element_type)
            session.commit()
        except NoResultFound as e:
            session.rollback()
            if log_error:
                msg = f"No ElementType found with id {id}."
                logger.error(msg)
            raise DBNotFoundError(msg) from e
        except IntegrityError as e:
            session.rollback()
            if log_error:
                msg = f"Database integrity error while deleting Elementtype with id {id}: {str(e)}"
                logger.error(msg)
            raise DBIntegrityError(msg) from e


def delete_et_cascade(id: UUID, log_error: bool = True) -> None:  # noqa: A002
    # The delete_et_cascade function differs from delete_et in that it also deletes all
    # associated ThingNode records before deleting the ElementType,
    # performing a cascading delete operation.
    with get_session()() as session, session.begin():
        try:
            element_type = fetch_et_by_id(session, id, log_error)
            for thing_node in element_type.thing_nodes:
                session.delete(thing_node)
            session.delete(element_type)
            session.commit()
        except NoResultFound as e:
            session.rollback()
            if log_error:
                msg = f"No ElementType found with id {id}."
                logger.error(msg)
            raise DBNotFoundError(msg) from e
        except IntegrityError as e:
            session.rollback()
            if log_error:
                msg = f"Database integrity error while deleting ElementType with id {id}: {str(e)}"
                logger.error(msg)
            raise DBIntegrityError(msg) from e
        except Exception as e:
            session.rollback()
            if log_error:
                msg = f"Unexpected error while deleting ElementType with id {id}: {str(e)}"
                logger.error(msg)
            raise


def update_et(
    id: UUID,  # noqa: A002
    et_update: ElementType,
    log_error: bool = True,
) -> None:
    with get_session()() as session, session.begin():
        try:
            element_type = fetch_et_by_id(session, id, log_error)
            if element_type:
                for attr, value in et_update.dict(exclude_unset=True).items():
                    setattr(element_type, attr, value)
        except NoResultFound as e:
            session.rollback()
            msg = f"No ElementType found with id {id}."
            if log_error:
                logger.error(msg)
            raise DBNotFoundError(msg) from e


# Thing Node Services


def add_tn(session: SQLAlchemySession, thingnode_orm: ThingNodeOrm) -> None:
    # This function is intended to be used as a helper within session-managed operations
    # and should not be called directly without proper session handling.
    try:
        session.add(thingnode_orm)
        session.flush()
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
    with get_session()() as session, session.begin():
        orm_tn = thingnode.to_orm_model()
        add_tn(session, orm_tn)


def read_single_thingnode(
    id: UUID,  # noqa: A002
    log_error: bool = True,
) -> ThingNode:
    with get_session()() as session, session.begin():
        orm_tn = fetch_tn_by_id(session, id, log_error)
        return ThingNode.from_orm_model(orm_tn)


def read_single_thingnode_by_external_id(
    external_id: str,
    stakeholder_key: str,
    log_error: bool = True,
) -> ThingNode:
    with get_session()() as session, session.begin():
        orm_tn = fetch_tn_by_external_id(session, external_id, stakeholder_key, log_error)
        return ThingNode.from_orm_model(orm_tn)


def delete_tn(id: UUID, log_error: bool = True) -> None:  # noqa: A002
    with get_session()() as session, session.begin():
        try:
            # Fetch the ThingNode to be deleted
            thingnode = fetch_tn_by_id(session, id, log_error)

            # Remove associations with sources
            sources = (
                session.query(SourceOrm).filter(SourceOrm.thing_nodes.any(id=thingnode.id)).all()
            )
            for source in sources:
                source.thing_nodes.remove(thingnode)

            # Remove associations with sinks
            sinks = session.query(SinkOrm).filter(SinkOrm.thing_nodes.any(id=thingnode.id)).all()
            for sink in sinks:
                sink.thing_nodes.remove(thingnode)

            # Recursively delete child ThingNodes
            children = (
                session.query(ThingNodeOrm)
                .filter(ThingNodeOrm.parent_node_id == thingnode.id)
                .all()
            )
            for child in children:
                delete_tn(child.id, log_error)

            # Delete the ThingNode itself
            session.delete(thingnode)
            session.commit()

        except Exception as e:
            session.rollback()
            if log_error:
                msg = f"Unexpected error while deleting ThingNode with id {id}: {str(e)}"
                logger.error(msg)
            raise


def update_tn(
    id: UUID,  # noqa: A002
    tn_update: ThingNode,
    log_error: bool = True,
) -> ThingNode:
    with get_session()() as session, session.begin():
        try:
            thingnode = fetch_tn_by_id(session, id, log_error)
            if thingnode:
                for attr, value in tn_update.dict(exclude_unset=True).items():
                    setattr(thingnode, attr, value)
            session.flush()
            return ThingNode.from_orm_model(thingnode)
        except NoResultFound as e:
            session.rollback()
            msg = f"No ThingNode found with {id}."
            if log_error:
                logger.error(msg)
            raise DBNotFoundError(msg) from e


def get_parent_tn_id(
    session: SQLAlchemySession,
    id: UUID,  # noqa: A002
    log_error: bool = True,
) -> UUIDType | None:
    try:
        thingnode = fetch_tn_by_id(session, id, log_error)
        if thingnode:
            return thingnode.parent_node_id
        return None
    except DBNotFoundError:
        if log_error:
            msg = f"Found no parent node in database for thingnode with id {id}"
            logger.error(msg)
        raise


def get_children_tn_ids(id: UUID, log_error: bool = True) -> list[UUID]:  # noqa: A002
    with get_session()() as session, session.begin():
        try:
            thingnode = fetch_tn_by_id(session, id, log_error)
            results = fetch_tn_child_ids_by_parent_id(session, thingnode.id)

            return results
        except DBNotFoundError:
            return []


def get_ancestors_tn_ids(
    id: UUID,  # noqa: A002
    depth: int = -1,
    log_error: bool = True,
) -> list[UUID]:
    """
    Retrieves the IDs of all ancestor ThingNodes up to a specified depth.

    Args:
        id (UUID): The ID of the starting ThingNode.
        depth (int): The maximum depth to search. If -1, search until the root node is reached.
        log_error (bool): Whether to log errors if a ThingNode is not found.

    Returns:
        list[UUID]: A list of UUIDs representing the ancestor ThingNodes.
    """
    ancestors_ids = []
    current_depth = 0
    current_id = id
    with get_session()() as session, session.begin():
        try:
            # Traverse up the hierarchy, stopping if the root is reached or the specified depth is exceeded
            while current_id and (depth == -1 or current_depth < depth):
                ancestors_ids.append(current_id)
                thingnode = fetch_tn_by_id(session, current_id, log_error)  # Fetch the current node
                if thingnode.parent_node_id is None:
                    break
                current_id = thingnode.parent_node_id  # noqa: A001
                current_depth += 1
        except DBNotFoundError as e:
            if log_error:
                msg = f"Error while evaluating hierarchy for id {id}: {str(e)}"
                logger.error(msg)
            raise

    return ancestors_ids


def get_descendants_tn_ids(
    id: UUID,  # noqa: A002
    depth: int = -1,
    log_error: bool = True,
) -> list[UUID]:
    """
    Retrieves the IDs of all descendant ThingNodes up to a specified depth.

    Args:
        id (UUID): The ID of the starting ThingNode.
        depth (int): The maximum depth to search. If -1, search through all descendants.
        log_error (bool): Whether to log errors if no descendants are found.

    Returns:
        list[UUID]: A list of UUIDs representing the descendant ThingNodes.
    """
    descendant_ids = []
    nodes_to_visit = [(id, 0)]  # Stack to keep track of nodes to visit, starting with the root node

    with get_session()() as session, session.begin():
        try:
            while nodes_to_visit:
                current_id, current_depth = nodes_to_visit.pop()  # Get the next node to visit
                if current_id is None or (depth != -1 and current_depth >= depth):
                    continue
                try:
                    # Fetch the child nodes of the current node
                    child_ids = fetch_tn_child_ids_by_parent_id(session, current_id, log_error)
                except DBNotFoundError:
                    if current_depth == 0 and log_error:
                        msg = f"No children found for thingnode with parent_id {current_id}"
                        logger.error(msg)
                    continue
                # Add each child node's ID to the list of descendants and queue them for further exploration
                for child_id in child_ids:
                    descendant_ids.append(child_id)
                    nodes_to_visit.append((child_id, current_depth + 1))
        except DBNotFoundError as e:
            if log_error:
                msg = f"Error while fetching descendants for id {current_id}: {str(e)}"
                logger.error(msg)
            raise

    return descendant_ids


# Source Services


def add_source(session: SQLAlchemySession, source_orm: SourceOrm) -> None:
    # This function is intended to be used as a helper within session-managed operations
    # and should not be called directly without proper session handling.
    try:
        session.add(source_orm)
        session.flush()
    except IntegrityError as e:
        msg = (
            f"Integrity Error while trying to store source "
            f"with id {source_orm.id}. Error was:\n{str(e)}"
        )
        logger.error(msg)
        raise DBIntegrityError(msg) from e


def store_single_source(source: Source) -> None:
    with get_session()() as session, session.begin():
        orm_source = source.to_orm_model()
        add_source(session, orm_source)


def read_single_source(
    id: UUID,  # noqa: A002
    log_error: bool = True,
) -> Source:
    with get_session()() as session, session.begin():
        orm_source = fetch_source_by_id(session, id, log_error)
        return Source.from_orm_model(orm_source)


def read_single_source_by_external_id(
    external_id: str,
    stakeholder_key: str,
    log_error: bool = True,
) -> Source:
    with get_session()() as session, session.begin():
        orm_source = fetch_source_by_external_id(session, external_id, stakeholder_key, log_error)
        return Source.from_orm_model(orm_source)


def update_source(
    id: UUID,  # noqa: A002
    source_update: Source,
    log_error: bool = True,
) -> Source:
    with get_session()() as session, session.begin():
        try:
            source = session.query(SourceOrm).filter(SourceOrm.id == id).one()
            for attr, value in source_update.dict(exclude_unset=True).items():
                setattr(source, attr, value)
            session.flush()
            return Source.from_orm_model(source)
        except NoResultFound as e:
            session.rollback()
            msg = f"No Source found with id {id}."
            if log_error:
                logger.error(msg)
            raise DBNotFoundError(msg) from e


def delete_source(id: UUID, log_error: bool = True) -> None:  # noqa: A002
    with get_session()() as session, session.begin():
        try:
            source = fetch_source_by_id(session, id, log_error)
            session.delete(source)
            session.commit()
        except Exception as e:
            session.rollback()
            if log_error:
                msg = f"Unexpected error while deleteing Source with id {id}: {str(e)}"
                logger.error(msg)
            raise


# Sink Services


def add_sink(session: SQLAlchemySession, sink_orm: SinkOrm) -> None:
    # This function is intended to be used as a helper within session-managed operations
    # and should not be called directly without proper session handling.
    try:
        session.add(sink_orm)
        session.flush()
    except IntegrityError as e:
        msg = (
            f"Integrity Error while trying to store sink "
            f"with id {sink_orm.id}. Error was:\n{str(e)}"
        )
        logger.error(msg)
        raise DBIntegrityError(msg) from e


def store_single_sink(sink: Sink) -> None:
    with get_session()() as session, session.begin():
        orm_sink = sink.to_orm_model()
        add_sink(session, orm_sink)


def read_single_sink(
    id: UUID,  # noqa: A002
    log_error: bool = True,
) -> Sink:
    with get_session()() as session, session.begin():
        orm_sink = fetch_sink_by_id(session, id, log_error)
        return Sink.from_orm_model(orm_sink)


def read_single_sink_by_external_id(
    external_id: str,
    stakeholder_key: str,
    log_error: bool = True,
) -> Sink:
    with get_session()() as session, session.begin():
        orm_sink = fetch_sink_by_external_id(session, external_id, stakeholder_key, log_error)
        return Sink.from_orm_model(orm_sink)


def update_sink(
    id: UUID,  # noqa: A002
    sink_update: Sink,
    log_error: bool = True,
) -> Sink:
    with get_session()() as session, session.begin():
        try:
            sink = session.query(SinkOrm).filter(SinkOrm.id == id).one()
            for attr, value in sink_update.dict(exclude_unset=True).items():
                setattr(sink, attr, value)
            session.flush()
            return Sink.from_orm_model(sink)
        except NoResultFound as e:
            session.rollback()
            msg = f"No Sink found with id {id}."
            if log_error:
                logger.error(msg)
            raise DBNotFoundError(msg) from e


def delete_sink(id: UUID, log_error: bool = True) -> None:  # noqa: A002
    with get_session()() as session, session.begin():
        try:
            sink = fetch_sink_by_id(session, id, log_error)
            session.delete(sink)
            session.commit()
        except Exception as e:
            session.rollback()
            if log_error:
                msg = f"Unexpected error while deleting Sink with id {id}: {str(e)}"
                logger.error(msg)
            raise


# Structure Services


def load_structure_from_json_file(
    file_path: str,
) -> CompleteStructure:
    with open(file_path) as file:
        structure_json = json.load(file)
    complete_structure = CompleteStructure(**structure_json)
    return complete_structure


# Structure Services: Insert function


def sort_thing_nodes(nodes: list[ThingNode]) -> dict[int, list[ThingNode]]:
    """
    Sorts a list of ThingNodes into hierarchical levels.

    Args:
        nodes (list[ThingNode]): The list of ThingNodes to be sorted.

    Returns:
        dict[int, list[ThingNode]]: A dictionary mapping each hierarchical level (int) to a list of
        ThingNodes at that level.
    """

    # Initialize a dictionary to hold the children of each node, and an empty list for root nodes
    children_by_node_id: dict[UUID, list[ThingNode]] = {node.id: [] for node in nodes}
    root_nodes = []  # List to hold root nodes (nodes with no parent)

    # Iterate through each node to populate the children list or identify root nodes
    for node in nodes:
        if node.parent_node_id:
            # If the node has a parent, add it to the parent's children list
            if node.parent_node_id not in children_by_node_id:
                children_by_node_id[node.parent_node_id] = []
            children_by_node_id[node.parent_node_id].append(node)
        else:
            # If no parent, it's a root node
            root_nodes.append(node)

    # Dictionary to hold nodes sorted by their hierarchical levels
    sorted_nodes_by_level = defaultdict(list)
    # Queue for breadth-first traversal, starting with root nodes
    queue = deque([(root_nodes, 0)])

    # Perform breadth-first traversal to sort nodes by levels
    while queue:
        current_level_nodes, level = queue.popleft()
        next_level_nodes = []

        for node in current_level_nodes:
            # Add the current node to its respective level in the sorted dictionary
            sorted_nodes_by_level[level].append(node)
            if node.id in children_by_node_id:
                # Sort the children nodes by their external_id
                children_by_node_id[node.id].sort(key=lambda x: x.external_id)
                # Prepare the nodes for the next level of traversal
                next_level_nodes.extend(children_by_node_id[node.id])

        if next_level_nodes:
            # Queue the next level nodes for processing
            queue.append((next_level_nodes, level + 1))

    return sorted_nodes_by_level


def create_mapping_between_external_and_internal_ids(
    tn_list: list[ThingNode], src_list: list[Source], snk_list: list[Sink]
) -> tuple[dict[str, UUID], dict[str, UUID], dict[str, UUID]]:
    """
    Creates mappings between external identifiers (combined with stakeholder keys) and their corresponding internal UUIDs.

    This mapping is necessary to look up internal UUIDs during processing,
    ensuring that external references can be resolved to their associated internal IDs,
    which are used within the system's database operations.
    """
    tn_mapping = {tn.stakeholder_key + tn.external_id: tn.id for tn in tn_list}
    src_mapping = {src.stakeholder_key + src.external_id: src.id for src in src_list}
    snk_mapping = {snk.stakeholder_key + snk.external_id: snk.id for snk in snk_list}
    return tn_mapping, src_mapping, snk_mapping


def fill_parent_uuids_of_thing_nodes(
    tn_mapping: dict[str, UUID], node_list: list[ThingNode]
) -> None:
    for node in node_list:
        if node.parent_external_node_id:
            parent_uuid = tn_mapping[node.stakeholder_key + node.parent_external_node_id]
            node.parent_node_id = parent_uuid


def fill_element_type_ids_of_thing_nodes(
    element_type_mapping: dict[str, UUID], node_list: list[ThingNode]
) -> None:
    for node in node_list:
        if node.element_type_external_id:
            element_type_uuid = element_type_mapping[
                node.stakeholder_key + node.element_type_external_id
            ]
            node.element_type_id = element_type_uuid


def fill_all_thingnode_parent_uuids(complete_structure: CompleteStructure) -> None:
    tn_mapping, _, _ = create_mapping_between_external_and_internal_ids(
        complete_structure.thing_nodes, [], []
    )
    fill_parent_uuids_of_thing_nodes(tn_mapping, complete_structure.thing_nodes)


def fill_all_thingnode_element_type_ids(complete_structure: CompleteStructure) -> None:
    element_type_mapping = {
        et.stakeholder_key + et.external_id: et.id for et in complete_structure.element_types
    }
    fill_element_type_ids_of_thing_nodes(element_type_mapping, complete_structure.thing_nodes)


def fill_source_sink_associations(
    complete_structure: CompleteStructure, session: SQLAlchemySession
) -> None:
    """
    Establishes associations between ThingNodes and their corresponding Sources and Sinks.

    This function creates mappings between the external IDs and internal UUIDs for ThingNodes,
    Sources, and Sinks within the given CompleteStructure. It then uses these mappings to
    associate each Source and Sink with the appropriate ThingNodes in the database, ensuring
    that the relationships are correctly represented.

    For each Source and Sink in the CompleteStructure, the function checks if an association
    with a ThingNode already exists in the database. If not, it inserts the association into
    the database to maintain the integrity of the structure.
    """
    tn_mapping, src_mapping, snk_mapping = create_mapping_between_external_and_internal_ids(
        complete_structure.thing_nodes, complete_structure.sources, complete_structure.sinks
    )

    def process_associations(
        entities: list[Source | Sink], mapping: dict[str, UUID], assoc_table: Table, entity_key: str
    ) -> None:
        for entity in entities:
            if entity.thing_node_external_ids:
                for tn_external_id in entity.thing_node_external_ids:
                    thing_node_id = tn_mapping[entity.stakeholder_key + tn_external_id]
                    entity_id = mapping[entity.stakeholder_key + entity.external_id]
                    association_exists = (
                        session.query(assoc_table)
                        .filter_by(thing_node_id=thing_node_id, **{entity_key: entity_id})
                        .first()
                    )
                    if not association_exists:
                        association = {
                            "thing_node_id": thing_node_id,
                            entity_key: entity_id,
                        }
                        session.execute(assoc_table.insert().values(association))

    process_associations(
        complete_structure.sources,  # type: ignore
        src_mapping,
        thingnode_source_association,
        "source_id",
    )
    process_associations(
        complete_structure.sinks,  # type: ignore
        snk_mapping,
        thingnode_sink_association,
        "sink_id",
    )


def flush_items(session: SQLAlchemySession, items: list) -> None:
    """
    Flushes a list of items to the database in a single transaction.

    This function iterates over a list of items, converts each to its ORM model, and adds it
    to the session. Once all items are added, the transaction is committed, ensuring all changes
    are persisted to the database simultaneously.

    If an IntegrityError occurs (e.g., due to constraint violations), the transaction is rolled
    back to maintain database integrity, and a custom DBIntegrityError is raised. Any other
    exceptions that occur are also caught, leading to a rollback and the raising of a
    DBIntegrityError to signal an unexpected issue.
    """
    try:
        for item in items:
            orm_item = item.to_orm_model()
            session.add(orm_item)

        session.commit()  # Commit all changes at once after all items are added

    except IntegrityError as e:
        session.rollback()  # Rollback the transaction if an integrity error occurs
        msg = f"Integrity Error while trying to store items. Error was:\n{str(e)}"
        logger.error(msg)
        raise DBIntegrityError(msg) from e
    except Exception as e:
        session.rollback()  # Catch-all rollback for any other unexpected exceptions
        msg = f"Unexpected error while processing items. Error was:\n{str(e)}"
        logger.error(msg)
        raise DBIntegrityError(msg) from e


def insert_structure_from_file(file_path: str) -> CompleteStructure:
    complete_structure = load_structure_from_json_file(file_path)
    return insert_structure(complete_structure)


def insert_structure(complete_structure: CompleteStructure) -> CompleteStructure:
    with get_session()() as session:
        fill_all_thingnode_element_type_ids(complete_structure)
        fill_all_thingnode_parent_uuids(complete_structure)

        sorted_nodes_by_level = sort_thing_nodes(complete_structure.thing_nodes)
        sorted_thing_nodes = [node for nodes in sorted_nodes_by_level.values() for node in nodes]

        flush_items(session, complete_structure.element_types)
        flush_items(session, sorted_thing_nodes)
        flush_items(session, complete_structure.sources)
        flush_items(session, complete_structure.sinks)

        fill_source_sink_associations(complete_structure, session)
        session.commit()

        return complete_structure


# Structure Services: Update function


def sort_thing_nodes_from_db(
    thing_nodes: list[ThingNode], existing_thing_nodes: dict[str, ThingNodeOrm]
) -> dict[int, list[ThingNode]]:
    """
    This function sorts a list of ThingNodes into hierarchical levels using existing ThingNode data
    fetched from the database. It ensures that the existing database IDs are retained for each node.
    The function does not directly access the database but relies on the provided existing_thing_nodes.

    """

    # Map existing ThingNodes from the database to a dictionary using a unique key
    existing_node_map = {
        (node.stakeholder_key or "") + (node.external_id or ""): node
        for node in existing_thing_nodes.values()
    }

    # Assign existing IDs to new nodes if they match by stakeholder_key + external_id
    for node in thing_nodes:
        key = node.stakeholder_key + node.external_id
        existing_node = existing_node_map.get(key)
        if existing_node:
            node.id = existing_node.id  # Retain the existing ID for the node

    # Initialize a dictionary to hold the children of each node, and an empty list for root nodes
    children_by_node_id: dict[UUID, list[ThingNode]] = {node.id: [] for node in thing_nodes}
    root_nodes = []

    # Iterate through each node to populate the children list or identify root nodes
    for node in thing_nodes:
        if node.parent_node_id:
            if node.parent_node_id not in children_by_node_id:
                children_by_node_id[node.parent_node_id] = []
            children_by_node_id[node.parent_node_id].append(node)
        else:
            root_nodes.append(node)

    # Dictionary to hold nodes sorted by their hierarchical levels
    sorted_nodes_by_level = defaultdict(list)
    # Queue for breadth-first traversal, starting with root nodes
    queue = deque([(root_nodes, 0)])

    # Perform breadth-first traversal to sort nodes by levels
    while queue:
        current_level_nodes, level = queue.popleft()
        next_level_nodes = []

        for node in current_level_nodes:
            # Add the current node to its respective level in the sorted dictionary
            sorted_nodes_by_level[level].append(node)
            if node.id in children_by_node_id:
                # Sort the children nodes by their external_id
                children_by_node_id[node.id].sort(key=lambda x: x.external_id)
                # Prepare the nodes for the next level of traversal
                next_level_nodes.extend(children_by_node_id[node.id])

        if next_level_nodes:
            # Queue the next level nodes for processing
            queue.append((next_level_nodes, level + 1))

    return sorted_nodes_by_level


def fill_all_thingnode_element_type_ids_from_db(
    thing_nodes: list[ThingNode], existing_element_types: dict[str, ElementTypeOrm]
) -> None:
    """
    This function fills the element_type_id for each ThingNode using element types
    that have already been fetched from the database. The function itself does not
    query the database but relies on the provided existing_element_types.
    """
    for node in thing_nodes:
        if node.element_type_external_id:
            key = node.stakeholder_key + node.element_type_external_id
            db_et = existing_element_types.get(key)
            if db_et:
                node.element_type_id = db_et.id


def fill_all_thingnode_parent_uuids_from_db(
    thing_nodes: list[ThingNode], existing_thing_nodes: dict[str, ThingNodeOrm]
) -> None:
    """
    This function assigns parent_node_id for each ThingNode using parent nodes
    that have already been fetched from the database. It does not perform any direct
    database operations but works with the provided existing_thing_nodes.
    """
    for node in thing_nodes:
        if node.parent_external_node_id:
            key = node.stakeholder_key + node.parent_external_node_id
            db_parent_tn = existing_thing_nodes.get(key)
            if db_parent_tn:
                node.parent_node_id = db_parent_tn.id
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

    existing_thing_nodes = {
        tn.stakeholder_key + tn.external_id: tn for tn in session.query(ThingNodeOrm).all()
    }
    existing_sources = {
        src.stakeholder_key + src.external_id: src for src in session.query(SourceOrm).all()
    }
    existing_sinks = {
        snk.stakeholder_key + snk.external_id: snk for snk in session.query(SinkOrm).all()
    }

    def process_db_associations(
        entities: list[Source | Sink],
        existing_entities: dict[str, Source | Sink],
        assoc_table: Table,
        entity_key: str,
    ) -> None:
        for entity in entities:
            if not entity.thing_node_external_ids:
                continue
            for tn_external_id in entity.thing_node_external_ids:
                tn_key = entity.stakeholder_key + tn_external_id
                thing_node = existing_thing_nodes.get(tn_key)
                if not thing_node:
                    continue
                thing_node_id = thing_node.id
                entity_key_full = entity.stakeholder_key + entity.external_id
                db_entity = existing_entities.get(entity_key_full)
                if not db_entity:
                    continue
                entity_id = db_entity.id
                association_exists = (
                    session.query(assoc_table)
                    .filter_by(thing_node_id=thing_node_id, **{entity_key: entity_id})
                    .first()
                )
                if not association_exists:
                    association = {
                        "thing_node_id": thing_node_id,
                        entity_key: entity_id,
                    }
                    session.execute(assoc_table.insert().values(association))

    process_db_associations(
        complete_structure.sources,  # type: ignore
        existing_sources,
        thingnode_source_association,
        "source_id",
    )
    process_db_associations(
        complete_structure.sinks,  # type: ignore
        existing_sinks,
        thingnode_sink_association,
        "sink_id",
    )


def update_structure_from_file(file_path: str) -> CompleteStructure:
    complete_structure = load_structure_from_json_file(file_path)
    return update_structure(complete_structure)


def update_structure(complete_structure: CompleteStructure) -> CompleteStructure:
    """
    This function updates or inserts the given complete structure into the database.
    """

    with get_session()() as session, session.begin():
        existing_element_types = fetch_existing_records(session, ElementTypeOrm)
        existing_thing_nodes = fetch_existing_records(session, ThingNodeOrm)
        existing_sources = fetch_existing_records(session, SourceOrm)
        existing_sinks = fetch_existing_records(session, SinkOrm)

        # Update or create element types
        with session.no_autoflush:
            update_or_create_elements(
                complete_structure.element_types, existing_element_types, session
            )
            session.flush()
            update_existing_elements(session, ElementTypeOrm, existing_element_types)

            # Fill in element type IDs for thing nodes
            fill_all_thingnode_element_type_ids_from_db(
                complete_structure.thing_nodes, existing_element_types
            )

            # Fill in parent node IDs for thing nodes
            fill_all_thingnode_parent_uuids_from_db(
                complete_structure.thing_nodes, existing_thing_nodes
            )

            # Sort and flatten the thing nodes hierarchy for easier processing
            sorted_thing_nodes = sort_and_flatten_thing_nodes(
                complete_structure.thing_nodes, existing_thing_nodes
            )

            update_or_create_thing_nodes(sorted_thing_nodes, existing_thing_nodes, session)
            session.flush()

            update_existing_elements(session, ThingNodeOrm, existing_thing_nodes)
            session.flush()

            update_or_create_sources_or_sinks(
                complete_structure.sources, existing_sources, session, SourceOrm
            )
            session.flush()

            update_or_create_sources_or_sinks(
                complete_structure.sinks, existing_sinks, session, SinkOrm
            )
            session.flush()

            # Establish associations between thing nodes, sources, and sinks
            fill_source_sink_associations_db(complete_structure, session)

    return complete_structure


def fetch_existing_records(session: SQLAlchemySession, model_class: Any) -> dict[str, Any]:
    """
    Fetches all records of the specified model class from the database and returns them as a
    dictionary with keys composed of stakeholder_key and external_id.
    """
    try:
        # Fetch all records of the given model class from the database
        records = session.query(model_class).all()
        # Create a dictionary mapping stakeholder_key + external_id to the record
        return {rec.stakeholder_key + rec.external_id: rec for rec in records}
    except Exception as e:
        # Log the error and re-raise the exception if something goes wrong
        msg = f"Error fetching records for model class {model_class.__name__}: {str(e)}"
        logger.error(msg)
        raise


def update_or_create_elements(
    elements: list[ElementType],
    existing_elements: dict[str, ElementTypeOrm],
    session: SQLAlchemySession,
) -> None:
    for element in elements:
        key = element.stakeholder_key + element.external_id
        db_element = existing_elements.get(key)
        if db_element:
            element.id = db_element.id  # Set the existing ID
            db_element.name = element.name
            db_element.description = element.description
            db_element.stakeholder_key = element.stakeholder_key
        else:
            new_element = element.to_orm_model()
            session.add(new_element)


def update_existing_elements(
    session: SQLAlchemySession, model_class: Any, existing_elements: dict[str, Any]
) -> None:
    """
    Updates the existing_elements dictionary with records from the database for the specified model class.
    """
    try:
        # Query the database for all records of the specified model class
        new_elements = {
            el.stakeholder_key + el.external_id: el for el in session.query(model_class).all()
        }
        # Update the existing_elements dictionary with the new elements from the database
        existing_elements.update(new_elements)
    except Exception as e:
        # Log the error and re-raise the exception if something goes wrong
        msg = f"Error updating existing elements for model class {model_class.__name__}: {str(e)}"
        logger.error(msg)
        raise


def sort_and_flatten_thing_nodes(
    thing_nodes: list[ThingNode], existing_thing_nodes: dict[str, ThingNodeOrm]
) -> list[ThingNode]:
    sorted_nodes_by_level = sort_thing_nodes_from_db(thing_nodes, existing_thing_nodes)
    # Flattening the list of nodes is necessary to convert the hierarchical structure
    # into a single, ordered list.
    return [node for nodes in sorted_nodes_by_level.values() for node in nodes]


def update_or_create_thing_nodes(
    thing_nodes: list[ThingNode],
    existing_thing_nodes: dict[str, ThingNodeOrm],
    session: SQLAlchemySession,
) -> None:
    for node in thing_nodes:
        key = node.stakeholder_key + node.external_id
        db_node = existing_thing_nodes.get(key)
        if db_node:
            node.id = db_node.id  # Set the existing ID
            db_node.name = node.name
            db_node.description = node.description
            db_node.element_type_id = node.element_type_id
            db_node.meta_data = node.meta_data
            db_node.parent_node_id = (
                node.parent_node_id if node.parent_node_id else db_node.parent_node_id
            )
        else:
            new_node = node.to_orm_model()
            session.add(new_node)


def update_or_create_sources_or_sinks(
    sources_or_sinks: list[Source | Sink],
    existing_items: dict[str, SourceOrm | SinkOrm],
    session: SQLAlchemySession,
    model_class: Type[SourceOrm | SinkOrm],
) -> None:
    """
    Updates existing source or sink items, or creates new ones if they do not exist.
    """
    for item in sources_or_sinks:
        key = item.stakeholder_key + item.external_id
        db_item = existing_items.get(key)
        if db_item:
            item.id = db_item.id  # Set the existing ID
            db_item.name = item.name
            db_item.type = item.type
            db_item.visible = item.visible
            db_item.adapter_key = item.adapter_key
            if model_class == SourceOrm:
                db_item.source_id = item.source_id
            elif model_class == SinkOrm:
                db_item.sink_id = item.sink_id
            db_item.meta_data = item.meta_data
            db_item.preset_filters = item.preset_filters
            db_item.passthrough_filters = item.passthrough_filters
            db_item.thing_node_external_ids = item.thing_node_external_ids
        else:
            new_item = item.to_orm_model()
            session.add(new_item)


def delete_structure(session: SQLAlchemySession) -> None:
    try:
        # Deactivate foreign key checks
        session.connection().execute(text("PRAGMA foreign_keys = OFF"))

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
            session.execute(delete(table))

        # Reactivate foreign key checks
        session.connection().execute(text("PRAGMA foreign_keys = ON"))

        session.commit()
    except Exception as e:
        session.rollback()
        raise e

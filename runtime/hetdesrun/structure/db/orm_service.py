import json
import logging
import uuid
from collections import defaultdict, deque
from typing import Any
from uuid import UUID

from sqlalchemy import delete, text
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
    log_error: bool = True,
) -> ElementTypeOrm:
    result: ElementTypeOrm | None = (
        session.query(ElementTypeOrm)
        .filter(ElementTypeOrm.external_id == external_id)
        .one_or_none()
    )

    if result is None:
        msg = f"Found no element type in database with external_id {external_id}"
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
    log_error: bool = True,
) -> ThingNodeOrm:
    result: ThingNodeOrm | None = (
        session.query(ThingNodeOrm).filter(ThingNodeOrm.external_id == external_id).one_or_none()
    )

    if result is None:
        msg = f"Found no thing node in database with external_id {external_id}"
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
    log_error: bool = True,
) -> SourceOrm:
    result: SourceOrm | None = (
        session.query(SourceOrm).filter(SourceOrm.external_id == external_id).one_or_none()
    )

    if result is None:
        msg = f"Found no source in database with external_id {external_id}"
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
    log_error: bool = True,
) -> SinkOrm:
    result: SinkOrm | None = (
        session.query(SinkOrm).filter(SinkOrm.external_id == external_id).one_or_none()
    )

    if result is None:
        msg = f"Found no source in database with external_id {external_id}"
        if log_error:
            logger.error(msg)
        raise DBNotFoundError(msg)

    return result


# Element Type Services


def add_et(session: SQLAlchemySession, element_type_orm: ElementTypeOrm) -> None:
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
    session: SQLAlchemySession,
    element_type: ElementType,
) -> None:
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
    external_id: str,  # noqa: A002
    log_error: bool = True,
) -> ElementType:
    with get_session()() as session, session.begin():
        orm_et = fetch_et_by_external_id(session, external_id, log_error)
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
    session: SQLAlchemySession,
    id: UUID,  # noqa: A002
    et_update: ElementType,
    log_error: bool = True,
) -> None:
    try:
        element_type = session.query(ElementTypeOrm).filter(ElementTypeOrm.id == id).one()
        for attr, value in et_update.dict(exclude_unset=True).items():
            setattr(element_type, attr, value)
        session.flush()
    except NoResultFound as e:
        session.rollback()
        msg = f"No ElementType found with id {id}."
        if log_error:
            logger.error(msg)
        raise DBNotFoundError(msg) from e


# Thing Node Services


def add_tn(session: SQLAlchemySession, thingnode_orm: ThingNodeOrm) -> None:
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
    session: SQLAlchemySession,
    thingnode: ThingNode,
) -> None:
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
    external_id: str,  # noqa: A002
    log_error: bool = True,
) -> ThingNode:
    with get_session()() as session, session.begin():
        orm_tn = fetch_tn_by_external_id(session, external_id, log_error)
        return ThingNode.from_orm_model(orm_tn)


def delete_tn(id: UUID, log_error: bool = True) -> None:  # noqa: A002
    with get_session()() as session, session.begin():
        try:
            thingnode = fetch_tn_by_id(session, id, log_error)

            sources = (
                session.query(SourceOrm).filter(SourceOrm.thing_nodes.any(id=thingnode.id)).all()
            )
            for source in sources:
                source.thing_nodes.remove(thingnode)

            sinks = session.query(SinkOrm).filter(SinkOrm.thing_nodes.any(id=thingnode.id)).all()
            for sink in sinks:
                sink.thing_nodes.remove(thingnode)

            children = (
                session.query(ThingNodeOrm)
                .filter(ThingNodeOrm.parent_node_id == thingnode.id)
                .all()
            )
            for child in children:
                delete_tn(child.id, log_error)

            session.delete(thingnode)
            session.commit()

        except Exception as e:
            session.rollback()
            if log_error:
                msg = f"Unexpected error while deleting ThingNode with id {id}: {str(e)}"
                logger.error(msg)
            raise


def update_tn(
    session: SQLAlchemySession,
    id: UUID,  # noqa: A002
    tn_update: ThingNode,
    log_error: bool = True,
) -> ThingNode:
    try:
        thingnode = session.query(ThingNodeOrm).filter(ThingNodeOrm.id == id).one()
        if tn_update.element_type_id:
            session.query(ElementTypeOrm).filter(
                ElementTypeOrm.id == tn_update.element_type_id
            ).one()
        for attr, value in tn_update.dict(exclude_unset=True).items():
            setattr(thingnode, attr, value)
        session.flush()
        return ThingNode.from_orm_model(thingnode)
    except NoResultFound as e:
        session.rollback()
        msg = f"No ThingNode found with id {id}."
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
    ancestors_ids = []
    current_depth = 0
    current_id = id
    with get_session()() as session, session.begin():
        try:
            while current_id and (depth == -1 or current_depth < depth):
                ancestors_ids.append(current_id)
                thingnode = fetch_tn_by_id(session, current_id, log_error)
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
    descendant_ids = []
    nodes_to_visit = [(id, 0)]

    with get_session()() as session, session.begin():
        try:
            while nodes_to_visit:
                current_id, current_depth = nodes_to_visit.pop()
                if current_id is None or (depth != -1 and current_depth >= depth):
                    continue
                try:
                    child_ids = fetch_tn_child_ids_by_parent_id(session, current_id, log_error)
                except DBNotFoundError:
                    if current_depth == 0 and log_error:
                        msg = f"No children found for thingnode with parent_id {current_id}"
                        logger.error(msg)
                    continue
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
    log_error: bool = True,
) -> Source:
    with get_session()() as session, session.begin():
        orm_source = fetch_source_by_external_id(session, external_id, log_error)
        return Source.from_orm_model(orm_source)


def update_source(
    session: SQLAlchemySession,
    id: UUID,  # noqa: A002
    source_update: Source,
    log_error: bool = True,
) -> Source:
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
    log_error: bool = True,
) -> Sink:
    with get_session()() as session, session.begin():
        orm_sink = fetch_sink_by_external_id(session, external_id, log_error)
        return Sink.from_orm_model(orm_sink)


def update_sink(
    session: SQLAlchemySession,
    id: UUID,  # noqa: A002
    sink_update: Sink,
    log_error: bool = True,
) -> Sink:
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


def sort_thing_nodes(nodes: list[ThingNode]) -> dict[int, list[ThingNode]]:
    children_by_node_id: dict[UUID, list[ThingNode]] = {node.id: [] for node in nodes}
    root_nodes = []

    for node in nodes:
        if node.parent_node_id:
            if node.parent_node_id not in children_by_node_id:
                children_by_node_id[node.parent_node_id] = []
            children_by_node_id[node.parent_node_id].append(node)
        else:
            root_nodes.append(node)

    sorted_nodes_by_level = defaultdict(list)
    queue = deque([(root_nodes, 0)])

    while queue:
        current_level_nodes, level = queue.popleft()
        next_level_nodes = []

        for node in current_level_nodes:
            sorted_nodes_by_level[level].append(node)
            children_by_node_id[node.id].sort(key=lambda x: x.external_id)
            next_level_nodes.extend(children_by_node_id[node.id])

        if next_level_nodes:
            queue.append((next_level_nodes, level + 1))

    return sorted_nodes_by_level


def create_mapping_between_external_and_internal_ids(
    tn_list: list[ThingNode], src_list: list[Source], snk_list: list[Sink]
) -> tuple[dict[str, UUID], dict[str, UUID], dict[str, UUID]]:
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


def fill_all_parent_uuids(complete_structure: CompleteStructure) -> None:
    tn_mapping, _, _ = create_mapping_between_external_and_internal_ids(
        complete_structure.thing_nodes, [], []
    )
    fill_parent_uuids_of_thing_nodes(tn_mapping, complete_structure.thing_nodes)


def fill_all_element_type_ids(complete_structure: CompleteStructure) -> None:
    element_type_mapping = {
        et.stakeholder_key + et.external_id: et.id for et in complete_structure.element_types
    }
    fill_element_type_ids_of_thing_nodes(element_type_mapping, complete_structure.thing_nodes)


def fill_source_sink_associations(
    complete_structure: CompleteStructure, session: SQLAlchemySession
) -> None:
    tn_mapping, src_mapping, snk_mapping = create_mapping_between_external_and_internal_ids(
        complete_structure.thing_nodes, complete_structure.sources, complete_structure.sinks
    )

    for source in complete_structure.sources:
        if source.thing_node_external_ids:
            for tn_external_id in source.thing_node_external_ids:
                thing_node_id = tn_mapping[source.stakeholder_key + tn_external_id]
                source_id = src_mapping[source.stakeholder_key + source.external_id]
                association_exists = (
                    session.query(thingnode_source_association)
                    .filter_by(thing_node_id=thing_node_id, source_id=source_id)
                    .first()
                )
                if not association_exists:
                    association = {
                        "thing_node_id": thing_node_id,
                        "source_id": source_id,
                    }
                    session.execute(thingnode_source_association.insert().values(association))

    for sink in complete_structure.sinks:
        if sink.thing_node_external_ids:
            for tn_external_id in sink.thing_node_external_ids:
                thing_node_id = tn_mapping[sink.stakeholder_key + tn_external_id]
                sink_id = snk_mapping[sink.stakeholder_key + sink.external_id]
                association_exists = (
                    session.query(thingnode_sink_association)
                    .filter_by(thing_node_id=thing_node_id, sink_id=sink_id)
                    .first()
                )
                if not association_exists:
                    association = {
                        "thing_node_id": thing_node_id,
                        "sink_id": sink_id,
                    }
                    session.execute(thingnode_sink_association.insert().values(association))


def fill_source_sink_associations_db(
    complete_structure: CompleteStructure, session: SQLAlchemySession
) -> None:
    existing_element_types = {
        et.stakeholder_key + et.external_id: et for et in session.query(ElementTypeOrm).all()
    }
    existing_thing_nodes = {
        tn.stakeholder_key + tn.external_id: tn for tn in session.query(ThingNodeOrm).all()
    }
    existing_sources = {
        src.stakeholder_key + src.external_id: src for src in session.query(SourceOrm).all()
    }
    existing_sinks = {
        snk.stakeholder_key + snk.external_id: snk for snk in session.query(SinkOrm).all()
    }

    for source in complete_structure.sources:
        if source.thing_node_external_ids:
            for tn_external_id in source.thing_node_external_ids:
                tn_key = source.stakeholder_key + tn_external_id
                thing_node = existing_thing_nodes.get(tn_key)
                if thing_node:
                    thing_node_id = thing_node.id
                    src_key = source.stakeholder_key + source.external_id
                    db_source = existing_sources.get(src_key)
                    if db_source:
                        source_id = db_source.id
                        association_exists = (
                            session.query(thingnode_source_association)
                            .filter_by(thing_node_id=thing_node_id, source_id=source_id)
                            .first()
                        )
                        if not association_exists:
                            association = {
                                "thing_node_id": thing_node_id,
                                "source_id": source_id,
                            }
                            session.execute(thingnode_source_association.insert().values(association))

    for sink in complete_structure.sinks:
        if sink.thing_node_external_ids:
            for tn_external_id in sink.thing_node_external_ids:
                tn_key = sink.stakeholder_key + tn_external_id
                thing_node = existing_thing_nodes.get(tn_key)
                if thing_node:
                    thing_node_id = thing_node.id
                    snk_key = sink.stakeholder_key + sink.external_id
                    db_sink = existing_sinks.get(snk_key)
                    if db_sink:
                        sink_id = db_sink.id
                        association_exists = (
                            session.query(thingnode_sink_association)
                            .filter_by(thing_node_id=thing_node_id, sink_id=sink_id)
                            .first()
                        )
                        if not association_exists:
                            association = {
                                "thing_node_id": thing_node_id,
                                "sink_id": sink_id,
                            }
                            session.execute(thingnode_sink_association.insert().values(association))



def load_structure_from_json_file(
    file_path: str,
) -> CompleteStructure:
    with open(file_path) as file:
        structure_json = json.load(file)
    complete_structure = CompleteStructure(**structure_json)
    return complete_structure


def flush_items(session: SQLAlchemySession, items: list) -> None:
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


def insert_structure_from_file(file_path: str, session: SQLAlchemySession) -> CompleteStructure:
    complete_structure = load_structure_from_json_file(file_path)
    return insert_structure(complete_structure, session)


def insert_structure(
    complete_structure: CompleteStructure, session: SQLAlchemySession
) -> CompleteStructure:
    fill_all_element_type_ids(complete_structure)
    fill_all_parent_uuids(complete_structure)
    sorted_thing_nodes = sort_thing_nodes(complete_structure.thing_nodes)

    sorted_nodes_by_level = sort_thing_nodes(complete_structure.thing_nodes)
    sorted_thing_nodes = [node for nodes in sorted_nodes_by_level.values() for node in nodes]

    flush_items(session, complete_structure.element_types)
    flush_items(session, sorted_thing_nodes)
    flush_items(session, complete_structure.sources)
    flush_items(session, complete_structure.sinks)

    fill_source_sink_associations(complete_structure, session)
    session.commit()

    return complete_structure


def fill_all_element_type_ids_from_db(
    thing_nodes: list[ThingNode], existing_element_types: dict[str, ElementTypeOrm]
) -> None:
    for node in thing_nodes:
        if node.element_type_external_id:
            key = node.stakeholder_key + node.element_type_external_id
            db_et = existing_element_types.get(key)
            if db_et:
                node.element_type_id = db_et.id


def fill_all_parent_uuids_from_db(
    thing_nodes: list[ThingNode], existing_thing_nodes: dict[str, ThingNodeOrm]
) -> None:
    for node in thing_nodes:
        if node.parent_external_node_id:
            key = node.stakeholder_key + node.parent_external_node_id
            db_parent_tn = existing_thing_nodes.get(key)
            if db_parent_tn:
                node.parent_node_id = db_parent_tn.id


def update_structure_from_file(file_path: str, session: SQLAlchemySession) -> CompleteStructure:
    complete_structure = load_structure_from_json_file(file_path)
    return update_structure(complete_structure, session)


def update_structure(
    complete_structure: CompleteStructure, session: SQLAlchemySession
) -> CompleteStructure:
    existing_element_types = {
        et.stakeholder_key + et.external_id: et for et in session.query(ElementTypeOrm).all()
    }
    existing_thing_nodes = {
        tn.stakeholder_key + tn.external_id: tn for tn in session.query(ThingNodeOrm).all()
    }
    existing_sources = {
        src.stakeholder_key + src.external_id: src for src in session.query(SourceOrm).all()
    }
    existing_sinks = {
        snk.stakeholder_key + snk.external_id: snk for snk in session.query(SinkOrm).all()
    }

    print("Existing ElementTypes:", {key: et.id for key, et in existing_element_types.items()})
    print("Existing ThingNodes:", {key: tn.id for key, tn in existing_thing_nodes.items()})
    print("Existing Sources:", {key: src.id for key, src in existing_sources.items()})
    print("Existing Sinks:", {key: snk.id for key, snk in existing_sinks.items()})

    # Fill IDs from existing elements in the database
    fill_all_element_type_ids_from_db(complete_structure.thing_nodes, existing_element_types)
    fill_all_parent_uuids_from_db(complete_structure.thing_nodes, existing_thing_nodes)

    sorted_nodes_by_level = sort_thing_nodes(complete_structure.thing_nodes)
    sorted_thing_nodes = [node for nodes in sorted_nodes_by_level.values() for node in nodes]

    with session.no_autoflush:
        for et in complete_structure.element_types:
            key = et.stakeholder_key + et.external_id
            db_et = existing_element_types.get(key)
            if db_et:
                print(f"Updating ElementType: {et.external_id} (old ID: {db_et.id})")
                et.id = db_et.id  # Set the existing ID
                print(f"New ElementType ID set to: {et.id}")
                db_et.name = et.name
                db_et.description = et.description
                db_et.stakeholder_key = et.stakeholder_key
            else:
                new_et = et.to_orm_model()
                print(f"Adding new ElementType: {et.external_id}")
                session.add(new_et)

        # Ensure all ElementTypes are flushed before processing ThingNodes
        session.flush()
        print("ElementTypes flushed.")

        for tn in sorted_thing_nodes:
            key = tn.stakeholder_key + tn.external_id
            db_tn = existing_thing_nodes.get(key)
            if db_tn:
                print(f"Updating ThingNode: {tn.external_id} (old ID: {db_tn.id})")
                tn.id = db_tn.id  # Set the existing ID
                print(f"New ThingNode ID set to: {tn.id}")
                tn.element_type_id = db_tn.element_type_id  # Keep existing element type ID
                print(
                    f"Setting parent_node_id: {tn.parent_node_id} for ThingNode: {tn.external_id}"
                )
                db_tn.parent_node_id = (
                    tn.parent_node_id if tn.parent_node_id else db_tn.parent_node_id
                )
                print(f"New parent_node_id: {db_tn.parent_node_id} for ThingNode: {db_tn.id}")
                db_tn.meta_data = tn.meta_data
            else:
                new_tn = tn.to_orm_model()
                print(f"Adding new ThingNode: {tn.external_id}")
                session.add(new_tn)

        # Ensure all ThingNodes are flushed before processing Sources and Sinks
        session.flush()
        print("ThingNodes flushed.")

        for src in complete_structure.sources:
            key = src.stakeholder_key + src.external_id
            db_src = existing_sources.get(key)
            if db_src:
                print(f"Updating Source: {src.external_id} (old ID: {db_src.id})")
                src.id = db_src.id  # Set the existing ID
                print(f"New Source ID set to: {src.id}")
                db_src.name = src.name
                db_src.type = src.type
                db_src.visible = src.visible
                db_src.adapter_key = src.adapter_key
                db_src.source_id = src.source_id
                db_src.meta_data = src.meta_data
                db_src.preset_filters = src.preset_filters
                db_src.passthrough_filters = src.passthrough_filters
                db_src.thing_node_external_ids = src.thing_node_external_ids
            else:
                new_src = src.to_orm_model()
                print(f"Adding new Source: {src.external_id}")
                session.add(new_src)

        for snk in complete_structure.sinks:
            key = snk.stakeholder_key + snk.external_id
            db_snk = existing_sinks.get(key)
            if db_snk:
                print(f"Updating Sink: {snk.external_id} (old ID: {db_snk.id})")
                snk.id = db_snk.id  # Set the existing ID
                print(f"New Sink ID set to: {snk.id}")
                db_snk.name = snk.name
                db_snk.type = snk.type
                db_snk.visible = snk.visible
                db_snk.adapter_key = snk.adapter_key
                db_snk.sink_id = snk.sink_id
                db_snk.meta_data = snk.meta_data
                db_snk.preset_filters = snk.preset_filters
                db_snk.passthrough_filters = snk.passthrough_filters
                db_snk.thing_node_external_ids = snk.thing_node_external_ids
            else:
                new_snk = snk.to_orm_model()
                print(f"Adding new Sink: {snk.external_id}")
                session.add(new_snk)

        # Flush all changes before filling associations
        session.flush()
        print("Sources and Sinks flushed.")

        fill_source_sink_associations_db(complete_structure, session)
        session.commit()
        print("Associations filled and committed.")

    return complete_structure


def fill_all_element_type_ids_from_json(thing_nodes: list, element_types: list) -> None:
    element_type_mapping = {et.stakeholder_key + et.external_id: et.id for et in element_types}
    for node in thing_nodes:
        if node.element_type_external_id:
            key = node.stakeholder_key + node.element_type_external_id
            node.element_type_id = element_type_mapping.get(key)


def fill_all_parent_uuids_from_json(
    thing_nodes: list, element_types: list, sources: list, sinks: list
) -> None:
    tn_mapping = {tn.stakeholder_key + tn.external_id: tn.id for tn in thing_nodes}

    for node in thing_nodes:
        if node.parent_external_node_id:
            parent_key = node.stakeholder_key + node.parent_external_node_id
            node.parent_node_id = tn_mapping.get(parent_key)


def fill_source_sink_associations_from_json(
    json_data: dict[str, Any], session: SQLAlchemySession
) -> None:
    sources_data = json_data.get("sources", [])
    sinks_data = json_data.get("sinks", [])

    # Mapping from external ID to ORM instance
    existing_thing_nodes = {
        tn.stakeholder_key + tn.external_id: tn for tn in session.query(ThingNodeOrm).all()
    }

    # Update the associations for sources
    for src_data in sources_data:
        db_src = (
            session.query(SourceOrm)
            .filter_by(
                stakeholder_key=src_data["stakeholder_key"], external_id=src_data["external_id"]
            )
            .one_or_none()
        )

        if db_src:
            db_src.thing_nodes.clear()
            for tn_external_id in src_data.get("thing_node_external_ids", []):
                tn_key = src_data["stakeholder_key"] + tn_external_id
                db_tn = existing_thing_nodes.get(tn_key)
                if db_tn:
                    db_src.thing_nodes.append(db_tn)
            session.add(db_src)

    # Update the associations for sinks
    for snk_data in sinks_data:
        db_snk = (
            session.query(SinkOrm)
            .filter_by(
                stakeholder_key=snk_data["stakeholder_key"], external_id=snk_data["external_id"]
            )
            .one_or_none()
        )

        if db_snk:
            db_snk.thing_nodes.clear()
            for tn_external_id in snk_data.get("thing_node_external_ids", []):
                tn_key = snk_data["stakeholder_key"] + tn_external_id
                db_tn = existing_thing_nodes.get(tn_key)
                if db_tn:
                    db_snk.thing_nodes.append(db_tn)
            session.add(db_snk)

    session.flush()
    print("Source and Sink associations updated.")


def update_structure_from_json(json_data: dict[str, Any], session: SQLAlchemySession) -> None:
    # Extract the relevant structures from the JSON data
    element_types_data = json_data.get("element_types", [])
    thing_nodes_data = json_data.get("thing_nodes", [])
    sources_data = json_data.get("sources", [])
    sinks_data = json_data.get("sinks", [])

    existing_element_types = {
        et.stakeholder_key + et.external_id: et for et in session.query(ElementTypeOrm).all()
    }
    existing_thing_nodes = {
        tn.stakeholder_key + tn.external_id: tn for tn in session.query(ThingNodeOrm).all()
    }
    existing_sources = {
        src.stakeholder_key + src.external_id: src for src in session.query(SourceOrm).all()
    }
    existing_sinks = {
        snk.stakeholder_key + snk.external_id: snk for snk in session.query(SinkOrm).all()
    }

    print("Existing ElementTypes:", {key: et.id for key, et in existing_element_types.items()})
    print("Existing ThingNodes:", {key: tn.id for key, tn in existing_thing_nodes.items()})
    print("Existing Sources:", {key: src.id for key, src in existing_sources.items()})
    print("Existing Sinks:", {key: snk.id for key, snk in existing_sinks.items()})

    # Ensure 'id' is present in element_types_data
    for et_data in element_types_data:
        if "id" not in et_data:
            et_data["id"] = str(uuid.uuid4())  # Generating a new UUID if id is missing

    # Ensure 'id' is present in thing_nodes_data
    for tn_data in thing_nodes_data:
        if "id" not in tn_data:
            tn_data["id"] = str(uuid.uuid4())  # Generating a new UUID if id is missing

    # Ensure 'id' is present in sources_data
    for src_data in sources_data:
        if "id" not in src_data:
            src_data["id"] = str(uuid.uuid4())  # Generating a new UUID if id is missing

    # Ensure 'id' is present in sinks_data
    for snk_data in sinks_data:
        if "id" not in snk_data:
            snk_data["id"] = str(uuid.uuid4())  # Generating a new UUID if id is missing

    # Map data from JSON to ORM models
    element_types = [ElementType(**et_data) for et_data in element_types_data]
    thing_nodes = [ThingNode(**tn_data) for tn_data in thing_nodes_data]
    sources = [Source(**src_data) for src_data in sources_data]
    sinks = [Sink(**snk_data) for snk_data in sinks_data]

    fill_all_element_type_ids_from_json(thing_nodes, element_types)
    fill_all_parent_uuids_from_json(thing_nodes, element_types, sources, sinks)

    sorted_nodes_by_level = sort_thing_nodes(thing_nodes)
    sorted_thing_nodes = [node for nodes in sorted_nodes_by_level.values() for node in nodes]

    with session.no_autoflush:
        for et_data in element_types_data:
            key = et_data["stakeholder_key"] + et_data["external_id"]
            db_et = existing_element_types.get(key)
            if db_et:
                print(f"Updating ElementType: {et_data['external_id']} (old ID: {db_et.id})")
                db_et.name = et_data["name"]
                db_et.description = et_data["description"]
                db_et.stakeholder_key = et_data["stakeholder_key"]
                session.add(db_et)  # update the existing record
            else:
                new_et = ElementTypeOrm(**et_data)  # Use the dictionary data directly
                print(f"Adding new ElementType: {et_data['external_id']}")
                session.add(new_et)

        # Ensure all ElementTypes are flushed before processing ThingNodes
        session.flush()
        print("ElementTypes flushed.")

        for tn_data in sorted_thing_nodes:
            key = tn_data.stakeholder_key + tn_data.external_id
            db_tn = existing_thing_nodes.get(key)
            if db_tn:
                print(f"Updating ThingNode: {tn_data.external_id} (old ID: {db_tn.id})")
                db_tn.name = tn_data.name
                db_tn.description = tn_data.description
                db_tn.parent_node_id = tn_data.parent_node_id
                db_tn.meta_data = tn_data.meta_data
                session.add(db_tn)  # update the existing record
            else:
                new_tn = ThingNodeOrm(**tn_data.__dict__)  # Convert the ThingNode to a dictionary
                print(f"Adding new ThingNode: {tn_data.external_id}")
                session.add(new_tn)

        # Ensure all ThingNodes are flushed before processing Sources and Sinks
        session.flush()
        print("ThingNodes flushed.")

        for src_data in sources_data:
            key = src_data["stakeholder_key"] + src_data["external_id"]
            db_src = existing_sources.get(key)
            if db_src:
                print(f"Updating Source: {src_data['external_id']} (old ID: {db_src.id})")
                db_src.name = src_data["name"]
                db_src.type = src_data["type"]
                db_src.visible = src_data["visible"]
                db_src.adapter_key = src_data["adapter_key"]
                db_src.source_id = src_data["source_id"]
                db_src.meta_data = src_data["meta_data"]
                db_src.preset_filters = src_data["preset_filters"]
                db_src.passthrough_filters = src_data["passthrough_filters"]
                db_src.thing_node_external_ids = src_data["thing_node_external_ids"]
                session.add(db_src)  # update the existing record
            else:
                new_src = SourceOrm(**src_data)
                print(f"Adding new Source: {src_data['external_id']}")
                session.add(new_src)

        for snk_data in sinks_data:
            key = snk_data["stakeholder_key"] + snk_data["external_id"]
            db_snk = existing_sinks.get(key)
            if db_snk:
                print(f"Updating Sink: {snk_data['external_id']} (old ID: {db_snk.id})")
                db_snk.name = snk_data["name"]
                db_snk.type = snk_data["type"]
                db_snk.visible = snk_data["visible"]
                db_snk.adapter_key = snk_data["adapter_key"]
                db_snk.sink_id = snk_data["sink_id"]
                db_snk.meta_data = snk_data["meta_data"]
                db_snk.preset_filters = snk_data["preset_filters"]
                db_snk.passthrough_filters = snk_data["passthrough_filters"]
                db_snk.thing_node_external_ids = snk_data["thing_node_external_ids"]
                session.add(db_snk)  # update the existing record
            else:
                new_snk = SinkOrm(**snk_data)
                print(f"Adding new Sink: {snk_data['external_id']}")
                session.add(new_snk)

        # Flush all changes before filling associations
        session.flush()
        print("Sources and Sinks flushed.")

        fill_source_sink_associations_from_json(json_data, session)
        session.commit()
        print("Associations filled and committed.")


def is_database_empty(session: SQLAlchemySession) -> bool:
    with get_session()() as session:
        element_types = fetch_all_element_types(session)
        thing_nodes = fetch_all_thing_nodes(session)
        sources = fetch_all_sources(session)
        sinks = fetch_all_sinks(session)

    return not (element_types or thing_nodes or sources or sinks)


def purge_structure(session: SQLAlchemySession) -> None:
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

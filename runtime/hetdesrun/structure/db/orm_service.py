import json
import logging
from collections import defaultdict, deque
from uuid import UUID

from sqlalchemy import select
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
                association = {
                    "thing_node_id": tn_mapping[source.stakeholder_key + tn_external_id],
                    "source_id": src_mapping[source.stakeholder_key + source.external_id],
                }
                session.execute(thingnode_source_association.insert().values(association))

    for sink in complete_structure.sinks:
        if sink.thing_node_external_ids:
            for tn_external_id in sink.thing_node_external_ids:
                association = {
                    "thing_node_id": tn_mapping[sink.stakeholder_key + tn_external_id],
                    "sink_id": snk_mapping[sink.stakeholder_key + sink.external_id],
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
    for item in items:
        try:
            orm_item = item.to_orm_model()
            session.add(orm_item)
            session.flush()
        except IntegrityError as e:
            msg = (
                f"Integrity Error while trying to store Item "
                f"with id {orm_item.id}. Error was:\n{str(e)}"
            )
            logger.error(msg)
            raise DBIntegrityError(msg) from e


def update_structure_from_file(file_path: str) -> None:
    complete_structure = load_structure_from_json_file(file_path)
    update_structure(complete_structure)


def update_structure(complete_structure: CompleteStructure) -> None:
    with get_session()() as session, session.begin():
        fill_all_element_type_ids(complete_structure)
        fill_all_parent_uuids(complete_structure)

        sorted_nodes_by_level = sort_thing_nodes(complete_structure.thing_nodes)
        sorted_thing_nodes = [node for nodes in sorted_nodes_by_level.values() for node in nodes]

        flush_items(session, complete_structure.element_types)
        flush_items(session, sorted_thing_nodes)
        flush_items(session, complete_structure.sources)
        flush_items(session, complete_structure.sinks)

        fill_source_sink_associations(complete_structure, session)

        session.flush()


def is_database_empty(session: SQLAlchemySession) -> bool:
    element_types = fetch_all_element_types(session)
    thing_nodes = fetch_all_thing_nodes(session)
    sources = fetch_all_sources(session)
    sinks = fetch_all_sinks(session)

    return not (element_types or thing_nodes or sources or sinks)

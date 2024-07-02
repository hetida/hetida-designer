import json
import logging
from collections import defaultdict, deque
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy_utils import UUIDType

from hetdesrun.persistence.dbmodels import (
    ElementTypeOrm,
    ElementTypeToPropertySetOrm,
    PropertyMetadataOrm,
    PropertySetOrm,
    SinkOrm,
    SourceOrm,
    ThingNodeOrm,
)
from hetdesrun.structure.db import SQLAlchemySession, get_session
from hetdesrun.structure.db.exceptions import DBIntegrityError, DBNotFoundError
from hetdesrun.structure.models import (
    ElementType,
    ElementTypeToPropertySet,
    PropertyMetadata,
    PropertySet,
    Sink,
    Source,
    ThingNode,
)

logger = logging.getLogger(__name__)


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


def fetch_source_by_id(
    session: SQLAlchemySession, id: int, log_error: bool = True  # noqa: A002
) -> SourceOrm:
    result: SourceOrm | None = session.execute(
        select(SourceOrm).where(SourceOrm.id == id)
    ).scalar_one_or_none()

    if result is None:
        msg = f"Found no source in database with id {id}"
        if log_error:
            logger.error(msg)
        raise DBNotFoundError(msg)

    return result


def update_source(
    id: int, source_update: Source, log_error: bool = True  # noqa: A002
) -> Source | None:
    with get_session()() as session, session.begin():
        try:
            source = session.query(SourceOrm).filter(SourceOrm.id == id).one()
            if source:
                source.name = source_update.name
                source.type = source_update.type
                source.visible = source_update.visible
                source.preset_filters = source_update.preset_filters
                source.passthrough_filters = source_update.passthrough_filters
                source.adapter_key = source_update.adapter_key
                source.source_id = source_update.source_id
                return Source.from_orm_model(source)
            return None
        except NoResultFound as e:
            session.rollback()
            if log_error:
                msg = f"No Source found with {id}."
                logger.error(msg)
            raise DBNotFoundError(f"No Source with id {id}") from e
        except IntegrityError as e:
            session.rollback()
            if log_error:
                msg = f"Database integrity error while updating Source with id {id}: {str(e)}"
                logger.error(msg)
            raise DBIntegrityError(msg) from e
        except Exception as e:
            session.rollback()
            if log_error:
                msg = f"Unexpected error while updating Source with id {id}: {str(e)}"
                logger.error(msg)
            raise


def delete_source(id: int, log_error: bool = True) -> None:  # noqa: A002
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


# Sink Service


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


def fetch_sink_by_id(
    session: SQLAlchemySession, id: int, log_error: bool = True  # noqa: A002
) -> SinkOrm:
    result: SinkOrm | None = session.execute(
        select(SinkOrm).where(SinkOrm.id == id)
    ).scalar_one_or_none()

    if result is None:
        msg = f"Found no sink in database with id {id}"
        if log_error:
            logger.error(msg)
        raise DBNotFoundError

    return result


def update_sink(
    id: int, sink_update: Sink, log_error: bool = True  # noqa: A002
) -> Sink | None:
    with get_session()() as session, session.begin():
        try:
            sink = session.query(SinkOrm).filter(SinkOrm.id == id).one()
            if sink:
                sink.name = sink_update.name
                sink.type = sink_update.type
                sink.visible = sink_update.visible
                sink.preset_filters = sink_update.preset_filters
                sink.passthrough_filters = sink_update.passthrough_filters
                sink.adapter_key = sink_update.adapter_key
                sink.sink_id = sink_update.sink_id
                return Sink.from_orm_model(sink)
            return None
        except NoResultFound as e:
            session.rollback()
            if log_error:
                msg = f"No Sink found with {id}."
                logger.error(msg)
            raise DBNotFoundError(f"No Sink with id {id}") from e
        except IntegrityError as e:
            session.rollback()
            if log_error:
                msg = f"Database integrity error while updating Sink with id {id}: {str(e)}"
                logger.error(msg)
            raise DBIntegrityError(msg) from e
        except Exception as e:
            session.rollback()
            if log_error:
                msg = f"Unexpected error while updating Sink with id {id}: {str(e)}"
                logger.error(msg)
            raise


def delete_sink(id: int, log_error: bool = True) -> None:  # noqa: A002
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


def fetch_tn_by_id(
    session: SQLAlchemySession,
    id: int,  # noqa: A002
    log_error: bool = True,
) -> ThingNodeOrm:
    result: ThingNodeOrm | None = session.execute(
        select(ThingNodeOrm).where(ThingNodeOrm.id == id)
    ).scalar_one_or_none()

    if result is None:
        msg = f"Found no thing node in database with id {id}"
        if log_error:
            logger.error(msg)
        raise DBNotFoundError(msg)

    return result


def fetch_tn_child_ids_by_parent_id(
    session: SQLAlchemySession, parent_id: int | None, log_error: bool = True
) -> list[int]:
    results = (
        session.execute(
            select(ThingNodeOrm.id).where(ThingNodeOrm.parent_node_id == parent_id)
        )
        .scalars()
        .all()
    )

    if not results and log_error:
        msg = f"No children found for thingnode with parent_id {parent_id}"
        logger.error(msg)
        raise DBNotFoundError(msg)

    return list(results)


def read_single_thingnode(
    id: int,  # noqa: A002
    log_error: bool = True,
) -> ThingNode:
    with get_session()() as session, session.begin():
        orm_tn = fetch_tn_by_id(session, id, log_error)
        return ThingNode.from_orm_model(orm_tn)


def delete_tn(id: int, log_error: bool = True) -> None:  # noqa: A002
    with get_session()() as session, session.begin():
        try:
            thingnode = fetch_tn_by_id(session, id, log_error)

            sources = (
                session.query(SourceOrm)
                .filter(SourceOrm.thing_node_id == thingnode.id)
                .all()
            )
            for source in sources:
                session.delete(source)

            sinks = (
                session.query(SinkOrm)
                .filter(SinkOrm.thing_node_id == thingnode.id)
                .all()
            )
            for sink in sinks:
                session.delete(sink)

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
                msg = (
                    f"Unexpected error while deleting ThingNode with id {id}: {str(e)}"
                )
                logger.error(msg)
            raise


def update_tn(
    id: UUID,  # noqa: A002
    tn_update: ThingNode,
    log_error: bool = True,
) -> ThingNode | None:
    with get_session()() as session, session.begin():
        try:
            thingnode = fetch_tn_by_id(session, id, log_error)
            if thingnode:
                thingnode.name = tn_update.name
                thingnode.description = tn_update.description
                thingnode.parent_node_id = tn_update.parent_node_id
                thingnode.element_type_id = tn_update.element_type_id
                thingnode.entity_uuid = tn_update.entity_uuid
                return ThingNode.from_orm_model(thingnode)
            return None
        except DBNotFoundError as e:
            session.rollback()
            if log_error:
                msg = f"No ThingNode found with {id}."
                logger.error(msg)
            raise DBNotFoundError(f"No ThingNode with id {id}") from e
        except IntegrityError as e:
            session.rollback()
            if log_error:
                msg = f"Database integrity error while updating ThingNode with id {id}: {str(e)}"
                logger.error(msg)
            raise DBIntegrityError(msg) from e
        except Exception as e:
            session.rollback()
            if log_error:
                msg = (
                    f"Unexpected error while updating ThingNode with id {id}: {str(e)}"
                )
                logger.error(msg)
            raise


def get_parent_tn_id(
    session: SQLAlchemySession, id: int, log_error: bool = True  # noqa: A002
) -> int | None:
    try:
        thingnode = fetch_tn_by_id(session, id, log_error)
        if thingnode:
            if thingnode.parent_node_id is not None:
                return int(thingnode.parent_node_id)
            return None
        return None
    except DBNotFoundError:
        if log_error:
            msg = f"Found no parent node in database for thingnode with id {id}"
            logger.error(msg)
        raise


def get_children_tn_ids(id: int, log_error: bool = True) -> list[int]:  # noqa: A002
    with get_session()() as session, session.begin():
        try:
            thingnode = fetch_tn_by_id(session, id, log_error)
            results = fetch_tn_child_ids_by_parent_id(session, thingnode.id)

            return results
        except DBNotFoundError:
            return []


def get_ancestors_tn_ids(
    id: int, depth: int = -1, log_error: bool = True  # noqa: A002
) -> list[int]:  # noqa: A002
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
    id: int, depth: int = -1, log_error: bool = True  # noqa: A002
) -> list[int]:
    descendant_ids = []
    nodes_to_visit = [(id, 0)]

    with get_session()() as session, session.begin():
        try:
            while nodes_to_visit:
                current_id, current_depth = nodes_to_visit.pop()
                if current_id is None or (depth != -1 and current_depth >= depth):
                    continue
                try:
                    child_ids = fetch_tn_child_ids_by_parent_id(
                        session, current_id, log_error
                    )
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


def fetch_et_by_id(
    session: SQLAlchemySession,
    id: int,  # noqa: A002
    log_error: bool = True,
) -> ElementTypeOrm:
    result: ElementTypeOrm | None = session.execute(
        select(ElementTypeOrm).where(ElementTypeOrm.id == id)
    ).scalar_one_or_none()

    if result is None:
        msg = f"Found no element type in database with id {id}"
        if log_error:
            logger.error(msg)
        raise DBNotFoundError(msg)

    return result


def read_single_element_type(
    id: int,  # noqa: A002
    log_error: bool = True,
) -> ElementType:
    with get_session()() as session, session.begin():
        orm_et = fetch_et_by_id(session, id, log_error)
        return ElementType.from_orm_model(orm_et)


def delete_et(id: int, log_error: bool = True) -> None:  # noqa: A002
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


def delete_et_cascade(id: int, log_error: bool = True) -> None:  # noqa: A002
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


from typing import Union
from uuid import UUID


def update_et(
    id: UUID,  # noqa: A002
    et_update: ElementType,
    log_error: bool = True,
) -> ElementType | None:
    with get_session()() as session, session.begin():
        try:
            element_type = fetch_et_by_id(session, id, log_error)
            if element_type:
                    element_type.name = et_update.name
                    element_type.icon = et_update.icon
                    element_type.description = et_update.description
                    element_type.property_sets = et_update.property_sets
                    element_type.thing_nodes = et_update.thing_nodes
            return ElementType.from_orm_model(element_type)
        except DBNotFoundError as e:
            session.rollback()
            if log_error:
                msg = f"No ElementType found with id {id}."
                logger.error(msg)
            raise DBIntegrityError(msg) from e
        except Exception as e:
            session.rollback()
            if log_error:
                msg = f"Unexpected error while updating ElementType with id {id}: {str(e)}"
                logger.error(msg)
            raise


# Property Set Services


def add_ps(session: SQLAlchemySession, property_set_orm: PropertySetOrm) -> None:
    try:
        session.add(property_set_orm)
    except IntegrityError as e:
        msg = (
            f"Integrity Error while trying to store PropertySet "
            f"with id {property_set_orm.id}. Error was:\n{str(e)}"
        )
        logger.error(msg)
        raise DBIntegrityError(msg) from e


def store_single_property_set(
    property_set: PropertySet,
) -> None:
    with get_session()() as session, session.begin():
        orm_ps = property_set.to_orm_model()
        add_ps(session, orm_ps)


def fetch_ps_by_id(
    session: SQLAlchemySession,
    id: int,  # noqa: A002
    log_error: bool = True,
) -> PropertySetOrm:
    result: PropertySetOrm | None = session.execute(
        select(PropertySetOrm).where(PropertySetOrm.id == id)
    ).scalar_one_or_none()

    if result is None:
        msg = f"Found no property set in database with id {id}"
        if log_error:
            logger.error(msg)
        raise DBNotFoundError(msg)

    return result


def read_single_property_set(
    id: int,  # noqa: A002
    log_error: bool = True,
) -> PropertySet:
    with get_session()() as session, session.begin():
        orm_ps = fetch_ps_by_id(session, id, log_error)
        return PropertySet.from_orm_model(orm_ps)


def delete_ps(id: int, log_error: bool = True) -> None:  # noqa: A002
    with get_session()() as session, session.begin():
        try:
            property_set = fetch_ps_by_id(session, id, log_error)
            if property_set.element_types:
                session.rollback()
                if log_error:
                    msg = (
                        f"Cannot delete PropertySet with id {id} "
                        "as it has associated ElementTypes."
                    )
                    logger.error(msg)
                raise DBIntegrityError(msg)
            if property_set.properties_metadata:
                session.rollback()
                if log_error:
                    msg = (
                        f"Cannot delete PropertySet with id {id} as "
                        "it has associated PropertyMetadata."
                    )
                    logger.error(msg)
                raise DBIntegrityError(msg)

            session.delete(property_set)
            session.commit()
        except NoResultFound as e:
            session.rollback()
            if log_error:
                msg = f"No PropertySet found with id {id}."
                logger.error(msg)
            raise DBNotFoundError(msg) from e
        except IntegrityError as e:
            session.rollback()
            if log_error:
                msg = f"Database integrity error while deleting PropertySet with id {id}: {str(e)}"
                logger.error(msg)
            raise DBIntegrityError(msg) from e


def update_ps(
    id: int,  # noqa: A002
    updated_data: dict,
    log_error: bool = True,
) -> PropertySet:
    with get_session()() as session, session.begin():
        try:
            property_set = fetch_ps_by_id(session, id, log_error)
            for key, value in updated_data.items():
                setattr(property_set, key, value)
            return PropertySet.from_orm_model(property_set)
        except DBNotFoundError as e:
            session.rollback()
            if log_error:
                msg = f"No PropertySet found with id {id}."
                logger.error(msg)
            raise DBIntegrityError(msg) from e
        except Exception as e:
            session.rollback()
            if log_error:
                msg = f"Unexpected error while updating PropertySet with id {id}: {str(e)}"
                logger.error(msg)
            raise


# Property Metadata Services


def add_pm(
    session: SQLAlchemySession, property_metadata_orm: PropertyMetadataOrm
) -> None:
    try:
        session.add(property_metadata_orm)
    except IntegrityError as e:
        msg = (
            f"Integrity Error while trying to store PropertyMetadataOrm "
            f"with id {property_metadata_orm.id}. Error was:\n{str(e)}"
        )
        logger.error(msg)
        raise DBIntegrityError(msg) from e


def store_single_property_metadata(
    property_metadata: PropertyMetadata,
) -> None:
    with get_session()() as session, session.begin():
        orm_pm = property_metadata.to_orm_model()
        add_pm(session, orm_pm)


def fetch_pm_by_id(
    session: SQLAlchemySession,
    id: int,  # noqa: A002
    log_error: bool = True,
) -> PropertyMetadataOrm:
    result: PropertyMetadataOrm | None = session.execute(
        select(PropertyMetadataOrm).where(PropertyMetadataOrm.id == id)
    ).scalar_one_or_none()

    if result is None:
        msg = f"Found no property metadata in database with id {id}"
        if log_error:
            logger.error(msg)
        raise DBNotFoundError(msg)

    return result


def read_single_property_metadata(
    id: int,  # noqa: A002
    log_error: bool = True,
) -> PropertyMetadata:
    with get_session()() as session, session.begin():
        orm_pm = fetch_pm_by_id(session, id, log_error)
        return PropertyMetadata.from_orm_model(orm_pm)


def delete_pm(id: int, log_error: bool = True) -> None:  # noqa: A002
    with get_session()() as session, session.begin():
        try:
            property_metadata = fetch_pm_by_id(session, id, log_error)
            if property_metadata.property_set:
                session.rollback()
                if log_error:
                    msg = (
                        f"Cannot delete PropertyMetadata with id {id} as "
                        "it has an associated PropertySet."
                    )
                    logger.error(msg)
                raise DBIntegrityError(msg)

            session.delete(property_metadata)
            session.commit()
        except NoResultFound as e:
            session.rollback()
            if log_error:
                msg = f"No PropertyMetadata found with id {id}."
                logger.error(msg)
            raise DBNotFoundError(msg) from e
        except IntegrityError as e:
            session.rollback()
            if log_error:
                msg = (
                    "Database integrity error while deleting "
                    f"PropertyMetadata with id {id}: {str(e)}"
                )
                logger.error(msg)
            raise DBIntegrityError(msg) from e


def update_pm(
    id: int,  # noqa: A002
    updated_data: dict,
    log_error: bool = True,
) -> PropertyMetadata:
    with get_session()() as session, session.begin():
        try:
            property_metadata = fetch_pm_by_id(session, id, log_error)
            for key, value in updated_data.items():
                setattr(property_metadata, key, value)
            return PropertyMetadata.from_orm_model(property_metadata)
        except DBNotFoundError as e:
            session.rollback()
            if log_error:
                msg = f"No PropertyMetadata found with id {id}."
                logger.error(msg)
            raise DBIntegrityError(msg) from e
        except Exception as e:
            session.rollback()
            if log_error:
                msg = f"Unexpected error while updating PropertyMetadata with id {id}: {str(e)}"
                logger.error(msg)
            raise


# Element Type To Property Set Services


def add_et2ps(
    session: SQLAlchemySession,
    element_type_to_property_set_orm: ElementTypeToPropertySetOrm,
) -> None:
    try:
        session.add(element_type_to_property_set_orm)
    except IntegrityError as e:
        msg = (
            f"Integrity Error while trying to store ElementTypeToPropertySetOrm "
            f"with element_type_id {element_type_to_property_set_orm.element_type_id} "
            f"and property_set_id {element_type_to_property_set_orm.property_set_id}. "
            f"Error was:\n{str(e)}"
        )
        logger.error(msg)
        raise DBIntegrityError(msg) from e


def store_single_et2ps(
    element_type_to_property_set: ElementTypeToPropertySet,
) -> None:
    with get_session()() as session, session.begin():
        orm_et2ps = element_type_to_property_set.to_orm_model()
        add_et2ps(session, orm_et2ps)


def fetch_et2ps_by_id(
    session: SQLAlchemySession,
    element_type_id: int,
    property_set_id: int,
    log_error: bool = True,
) -> ElementTypeToPropertySetOrm:
    result: ElementTypeToPropertySetOrm | None = session.execute(
        select(ElementTypeToPropertySetOrm).where(
            ElementTypeToPropertySetOrm.element_type_id
            == element_type_id & ElementTypeToPropertySetOrm.property_set_id
            == property_set_id
        )
    ).scalar_one_or_none()

    if result is None:
        msg = (
            f"Found no element type to property set table in database "
            f"with element_type_id {element_type_id} and property_set_id {property_set_id}"
        )
        if log_error:
            logger.error(msg)
        raise DBNotFoundError(msg)

    return result


def read_single_et2ps(
    id: int,  # noqa: A002
    log_error: bool = True,
) -> ElementTypeToPropertySet:
    with get_session()() as session, session.begin():
        orm_et2ps = fetch_et2ps_by_id(session, id, log_error)
        return ElementTypeToPropertySet.from_orm_model(orm_et2ps)


def delete_et2ps(id: int, log_error: bool = True) -> None:  # noqa: A002
    with get_session()() as session, session.begin():
        try:
            element_type_to_property_set = fetch_et2ps_by_id(session, id, log_error)
            if element_type_to_property_set.element_type_id:
                session.rollback()
                if log_error:
                    msg = (
                        f"Cannot delete ElementTypeToPropertySet with id {id} as "
                        "it has an associated ElementType."
                    )
                    logger.error(msg)
                raise DBIntegrityError(msg)
            if element_type_to_property_set.property_set_id:
                session.rollback()
                if log_error:
                    msg = (
                        f"Cannot delete ElementTypeToPropertySet with id {id} as "
                        "it has an associated PropertySet."
                    )
                    logger.error(msg)
                raise DBIntegrityError(msg)

            session.delete(element_type_to_property_set)
            session.commit()
        except NoResultFound as e:
            session.rollback()
            if log_error:
                msg = f"No ElementTypeToPropertySet found with id {id}."
                logger.error(msg)
            raise DBNotFoundError(msg) from e
        except IntegrityError as e:
            session.rollback()
            if log_error:
                msg = (
                    "Database integrity error while deleting ElementTypeToPropertySet "
                    f"with id {id}: {str(e)}"
                )
                logger.error(msg)
            raise DBIntegrityError(msg) from e


def update_et2ps(
    id: int,  # noqa: A002
    updated_data: dict,
    log_error: bool = True,
) -> ElementTypeToPropertySet:
    with get_session()() as session, session.begin():
        try:
            element_type_to_property_set = fetch_et2ps_by_id(session, id, log_error)
            for key, value in updated_data.items():
                setattr(element_type_to_property_set, key, value)
            return ElementTypeToPropertySet.from_orm_model(element_type_to_property_set)
        except DBNotFoundError as e:
            session.rollback()
            if log_error:
                msg = f"No ElementTypeToPropertySet found with id {id}."
                logger.error(msg)
            raise DBIntegrityError(msg) from e
        except Exception as e:
            session.rollback()
            if log_error:
                msg = (
                    "Unexpected error while updating ElementTypeToPropertySet "
                    f"with id {id}: {str(e)}"
                )
                logger.error(msg)
            raise


# Structure Services


def process_element_types(data: dict) -> list[ElementType]:
    element_types = []
    for element_type_data in data.get("element_types", []):
        try:
            element_type = ElementType(**element_type_data)
            element_types.append(element_type)
        except ValidationError as e:
            msg = f"Error validating ElementType: {e}"
            logger.error(msg)
    return element_types


def process_sources(data: dict) -> tuple[list[Source], dict[UUID, list[Source]]]:
    sources = []
    sources_by_node_id = defaultdict(list)
    for source_data in data.get("sources", []):
        try:
            source = Source(**source_data)
            sources.append(source)
            sources_by_node_id[source.thingNodeId].append(source)
        except ValidationError as e:
            msg = f"Error validating Source: {e}"
            logger.error(msg)
    return sources, sources_by_node_id


def process_sinks(data: dict) -> tuple[list[Sink], dict[UUID, list[Sink]]]:
    sinks = []
    sinks_by_node_id = defaultdict(list)
    for sink_data in data.get("sinks", []):
        try:
            sink = Sink(**sink_data)
            sinks.append(sink)
            sinks_by_node_id[sink.thingNodeId].append(sink)
        except ValidationError as e:
            msg = f"Error validating Sink: {e}"
            logger.error(msg)
    return sinks, sinks_by_node_id


def process_thing_nodes(data: dict) -> dict[UUID, ThingNode]:
    nodes_by_id = {}
    for node_data in data.get("thing_nodes", []):
        try:
            node = ThingNode(**node_data)
            nodes_by_id[node.id] = node
        except ValidationError as e:
            msg = f"Error validating ThingNode: {e}"
            logger.error(msg)
    return nodes_by_id


def topological_sort_thing_nodes(nodes_by_id: dict[UUID, ThingNode]) -> list[ThingNode]:
    in_degree = {node_id: 0 for node_id in nodes_by_id}

    for node in nodes_by_id.values():
        if node.parent_node_id:
            in_degree[node.id] += 1

    queue = deque(
        [node for node_id, node in nodes_by_id.items() if in_degree[node_id] == 0]
    )

    sorted_nodes = []

    while queue:
        node = queue.popleft()
        sorted_nodes.append(node)
        for child_node in nodes_by_id.values():
            if child_node.parent_node_id == node.id:
                in_degree[child_node.id] -= 1
                if in_degree[child_node.id] == 0:
                    queue.append(child_node)

    if len(sorted_nodes) != len(nodes_by_id):
        raise ValueError("cycle detected in ThingNodes")

    return sorted_nodes


def process_json_data(
    data: dict,
) -> tuple[list[ElementType], list[ThingNode], list[Source], list[Sink]]:
    element_types = process_element_types(data)
    sources, sources_by_node_id = process_sources(data)
    sinks, sinks_by_node_id = process_sinks(data)
    nodes_by_id = process_thing_nodes(data)
    sorted_nodes = topological_sort_thing_nodes(nodes_by_id)
    return element_types, sorted_nodes, sources, sinks


def load_structure_from_json_file(
    file_path: str,
) -> tuple[list[ElementType], list[ThingNode], list[Source], list[Sink]]:
    with open(file_path) as file:
        data = json.load(file)
    element_types, thing_nodes, sources, sinks = process_json_data(data)
    return element_types, thing_nodes, sources, sinks


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


def update_structure(file_path: str) -> None:
    element_types, thing_nodes, sources, sinks = load_structure_from_json_file(
        file_path
    )

    with get_session()() as session, session.begin():
        flush_items(session, element_types)
        flush_items(session, thing_nodes)
        flush_items(session, sources)
        flush_items(session, sinks)

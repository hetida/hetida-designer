import logging
from itertools import batched
from uuid import UUID

from sqlalchemy import Connection, Engine, delete, insert
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.postgresql.dml import Insert as pg_insert_typing
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.dialects.sqlite.dml import Insert as sqlite_insert_typing
from sqlalchemy.exc import IntegrityError

from hetdesrun.persistence.db_engine_and_session import SQLAlchemySession, get_session
from hetdesrun.persistence.structure_service_dbmodels import (
    StructureServiceSinkDBModel,
    StructureServiceSourceDBModel,
    StructureServiceThingNodeDBModel,
    thingnode_sink_association,
    thingnode_source_association,
)
from hetdesrun.structure.db.exceptions import (
    DBError,
    DBIntegrityError,
    DBNotFoundError,
    DBUpdateError,
)
from hetdesrun.structure.models import (
    StructureServiceSink,
    StructureServiceSource,
)
from hetdesrun.structure.utils import is_postgresql, is_sqlite

logger = logging.getLogger(__name__)


def fetch_all_sources_from_db() -> list[StructureServiceSource]:
    logger.debug("Fetching all StructureServiceSources from the database.")
    with get_session()() as session:
        sources = session.query(StructureServiceSourceDBModel).all()

    logger.debug("Successfully fetched %d sources from the database.", len(sources))
    return [StructureServiceSource.from_orm_model(source) for source in sources]


def fetch_all_sinks_from_db() -> list[StructureServiceSink]:
    logger.debug("Fetching all StructureServiceSinks from the database.")
    with get_session()() as session:
        sinks = session.query(StructureServiceSinkDBModel).all()

    logger.debug("Successfully fetched %d sinks from the database.", len(sinks))
    return [StructureServiceSink.from_orm_model(sink) for sink in sinks]


def fetch_single_sink_from_db_by_id(sink_id: UUID) -> StructureServiceSink:
    logger.debug("Fetching single StructureServiceSink from database with ID: %s", sink_id)
    with get_session()() as session:
        sink = (
            session.query(StructureServiceSinkDBModel)
            .filter(StructureServiceSinkDBModel.id == sink_id)
            .one_or_none()
        )
        if sink:
            logger.debug("StructureServiceSink with ID %s found.", sink_id)
            return StructureServiceSink.from_orm_model(sink)

    logger.warning("No StructureServiceSink found for ID %s.", sink_id)
    raise DBNotFoundError(f"No StructureServiceSink found for ID {sink_id}")


def fetch_single_source_from_db_by_id(src_id: UUID) -> StructureServiceSource:
    logger.debug("Fetching single StructureServiceSource from database with ID: %s", src_id)
    with get_session()() as session:
        source = (
            session.query(StructureServiceSourceDBModel)
            .filter(StructureServiceSourceDBModel.id == src_id)
            .one_or_none()
        )
        if source:
            logger.debug("StructureServiceSource with ID %s found.", src_id)
            return StructureServiceSource.from_orm_model(source)

    logger.warning("No StructureServiceSource found for ID %s.", src_id)
    raise DBNotFoundError(f"No StructureServiceSource found for ID {src_id}")


def fetch_collection_of_sources_from_db_by_id(
    src_ids: list[UUID], batch_size: int = 500
) -> dict[UUID, StructureServiceSource]:
    """Fetch multiple sources by their unique IDs.

    Retrieves a collection of StructureServiceSource records from the database,
    returning a dictionary that maps each source ID to its corresponding record.
    """
    sources: dict[UUID, StructureServiceSource] = {}
    if not src_ids:
        return sources

    logger.debug("Fetching collection of StructureServiceSources for %d IDs.", len(src_ids))
    with get_session()() as session:
        for id_batch in batched(src_ids, batch_size, strict=False):
            batch_query = session.query(StructureServiceSourceDBModel).filter(
                StructureServiceSourceDBModel.id.in_(id_batch)
            )
            batch_results = batch_query.all()
            for src in batch_results:
                sources[src.id] = StructureServiceSource.from_orm_model(src)

    if not sources:
        raise DBNotFoundError(f"No StructureServiceSources found for IDs {src_ids}")

    logger.debug(
        "Successfully fetched collection of %d StructureServiceSources for %d IDs.",
        len(sources),
        len(src_ids),
    )
    return sources


def fetch_collection_of_sinks_from_db_by_id(
    sink_ids: list[UUID], batch_size: int = 500
) -> dict[UUID, StructureServiceSink]:
    """Fetch multiple sinks by their unique IDs.

    Retrieves a collection of StructureServiceSink records from the database,
    returning a dictionary that maps each sink ID to its corresponding record.
    """
    sinks: dict[UUID, StructureServiceSink] = {}
    if not sink_ids:
        return sinks

    logger.debug("Fetching collection of StructureServiceSinks for %d IDs.", len(sink_ids))
    with get_session()() as session:
        for id_batch in batched(sink_ids, batch_size, strict=False):
            batch_query = session.query(StructureServiceSinkDBModel).filter(
                StructureServiceSinkDBModel.id.in_(id_batch)
            )
            batch_results = batch_query.all()
            for sink in batch_results:
                sinks[sink.id] = StructureServiceSink.from_orm_model(sink)

    if not sinks:
        raise DBNotFoundError(f"No StructureServiceSinks found for IDs {sink_ids}")

    logger.debug(
        "Successfully fetched collection of %d StructureServiceSinks for %d IDs.",
        len(sinks),
        len(sink_ids),
    )
    return sinks


def fetch_sources_by_substring_match(filter_string: str) -> list[StructureServiceSource]:
    """Search for sources with names matching a substring.

    Performs a case-insensitive search for StructureServiceSource records
    whose names contain the given substring. Returns a list of matching
    source instances.
    """
    with get_session()() as session:
        try:
            matching_sources = (
                session.query(StructureServiceSourceDBModel)
                .filter(
                    StructureServiceSourceDBModel.name.icontains(filter_string, autoescape=True)
                )
                .all()
            )
            logger.debug(
                "Found %d StructureServiceSourceDBModel items matching filter string '%s'.",
                len(matching_sources),
                filter_string,
            )
            return [StructureServiceSource.from_orm_model(src) for src in matching_sources]
        except IntegrityError as e:
            logger.error(
                "Integrity Error while filtering StructureServiceSourceDBModel "
                "by substring match: %s",
                e,
            )
            raise DBIntegrityError(
                "Integrity Error while filtering StructureServiceSourceDBModel by substring match"
            ) from e
        except Exception as e:
            logger.exception(
                "Unexpected error while filtering StructureServiceSourceDBModel by substring match"
            )
            raise DBError(
                "Unexpected error while filtering StructureServiceSourceDBModel by substring match"
            ) from e


def fetch_sinks_by_substring_match(filter_string: str) -> list[StructureServiceSink]:
    """Search for sinks with names matching a substring.

    Performs a case-insensitive search for StructureServiceSink records
    whose names contain the given substring. Returns a list of matching
    sink instances.
    """
    with get_session()() as session:
        try:
            matching_sinks = (
                session.query(StructureServiceSinkDBModel)
                .filter(StructureServiceSinkDBModel.name.icontains(filter_string, autoescape=True))
                .all()
            )
            logger.debug(
                "Found %d StructureServiceSinkDBModel items matching filter string '%s'.",
                len(matching_sinks),
                filter_string,
            )
            return [StructureServiceSink.from_orm_model(sink) for sink in matching_sinks]
        except IntegrityError as e:
            logger.error(
                "Integrity Error while filtering StructureServiceSinkDBModel "
                "by substring match: %s",
                e,
            )
            raise DBIntegrityError(
                "Integrity Error while filtering StructureServiceSourceDBModel by substring match"
            ) from e
        except Exception as e:
            logger.exception(
                "Unexpected error while filtering StructureServiceSinkDBModel by substring match"
            )
            raise DBError(
                "Unexpected error while filtering StructureServiceSinkDBModel by substring match"
            ) from e


def _collect_thing_node_associations(
    entity_dbmodels: object,
    existing_thing_nodes: dict[tuple[str, str], StructureServiceThingNodeDBModel],
    entity_id_column: str,
) -> tuple[list[UUID], list[dict]]:
    """Collect the thing-node association rows for a set of upserted sources/sinks.

    Returns the entity ids and the association rows ({"thingnode_id": ..., <entity_id_column>: ...})
    for a bulk replace. Duplicate associations are removed. Only scalar columns of the
    returned orm models are accessed, so this does not trigger relationship lazy-loads.
    """
    entity_ids: list[UUID] = []
    association_rows: list[dict] = []
    seen: set[tuple[UUID, UUID]] = set()
    for entity in entity_dbmodels:  # type: ignore[attr-defined]
        entity_ids.append(entity.id)
        for tn_external_id in entity.thing_node_external_ids or []:
            thing_node = existing_thing_nodes.get((entity.stakeholder_key, tn_external_id))
            if thing_node is None:
                continue
            association = (thing_node.id, entity.id)
            if association in seen:
                continue
            seen.add(association)
            association_rows.append({"thingnode_id": thing_node.id, entity_id_column: entity.id})
    return entity_ids, association_rows


def upsert_sources(
    session: SQLAlchemySession,
    sources: list[StructureServiceSource],
    existing_thing_nodes: dict[tuple[str, str], StructureServiceThingNodeDBModel],
) -> None:
    """Insert or update source records in the database.

    For each StructureServiceSource, updates existing records if they are found;
    otherwise, creates new records.
    """
    if not sources:
        return
    source_dicts = [src.model_dump() for src in sources]

    try:
        engine: Engine | Connection = session.get_bind()
        if isinstance(engine, Connection):
            raise ValueError("The session in use has to be bound to an Engine not a Connection.")

        upsert_stmt: sqlite_insert_typing | pg_insert_typing

        if is_postgresql(engine):
            upsert_stmt = pg_insert(StructureServiceSourceDBModel)
        elif is_sqlite(engine):
            upsert_stmt = sqlite_insert(StructureServiceSourceDBModel)
        else:
            raise ValueError(
                f"Unsupported database engine: {engine}. Please use either Postgres or SQLITE."
            )

        upsert_stmt = upsert_stmt.on_conflict_do_update(
            index_elements=[
                "external_id",
                "stakeholder_key",
            ],  # Columns where insert looks for a conflict
            set_={
                col: upsert_stmt.excluded[col] for col in source_dicts[0] if col != "id"
            },  # Exclude primary key from update
        ).returning(StructureServiceSourceDBModel)  # type: ignore

        # ORM models returned by the upsert query
        sources_dbmodels = session.scalars(
            upsert_stmt,
            source_dicts,
            execution_options={"populate_existing": True},
        )

        # Replace the many-to-many thing-node associations in bulk. Assigning
        # source.thing_nodes per row would lazy-load each source's current association
        # collection to diff it (one SELECT per source, i.e. N+1); instead apply the
        # desired associations with a single bulk delete + bulk insert.
        source_ids, source_association_rows = _collect_thing_node_associations(
            sources_dbmodels, existing_thing_nodes, "source_id"
        )
        session.execute(
            delete(thingnode_source_association).where(
                thingnode_source_association.c.source_id.in_(source_ids)
            )
        )
        if source_association_rows:
            session.execute(insert(thingnode_source_association), source_association_rows)

    except IntegrityError as e:
        logger.error("Integrity Error while upserting StructureServiceSourceDBModel: %s", e)
        raise DBIntegrityError(
            "Integrity Error while upserting StructureServiceSourceDBModel"
        ) from e
    except ValueError as e:
        logger.error("Value error while upserting StructureServiceSourceDBModel: %s", e)
        raise DBUpdateError("Value error while upserting StructureServiceSourceDBModel") from e
    except Exception as e:
        logger.exception("Unexpected error while upserting StructureServiceSourceDBModel")
        raise DBUpdateError("Unexpected error while upserting StructureServiceSourceDBModel") from e


def upsert_sinks(
    session: SQLAlchemySession,
    sinks: list[StructureServiceSink],
    existing_thing_nodes: dict[tuple[str, str], StructureServiceThingNodeDBModel],
) -> None:
    """Insert or update sink records in the database.

    For each StructureServiceSink, updates existing records if they are found;
    otherwise, creates new records.
    """
    if not sinks:
        return
    sink_dicts = [sink.model_dump() for sink in sinks]

    try:
        engine: Engine | Connection = session.get_bind()
        if isinstance(engine, Connection):
            raise ValueError("The session in use has to be bound to an Engine not a Connection.")

        upsert_stmt: sqlite_insert_typing | pg_insert_typing

        if is_postgresql(engine):
            upsert_stmt = pg_insert(StructureServiceSinkDBModel)
        elif is_sqlite(engine):
            upsert_stmt = sqlite_insert(StructureServiceSinkDBModel)
        else:
            raise ValueError(
                f"Unsupported database engine: {engine}. Please use either Postgres or SQLITE."
            )

        upsert_stmt = upsert_stmt.on_conflict_do_update(
            index_elements=[
                "external_id",
                "stakeholder_key",
            ],  # Columns where insert looks for a conflict
            set_={
                col: upsert_stmt.excluded[col] for col in sink_dicts[0] if col != "id"
            },  # Exclude primary key from update
        ).returning(StructureServiceSinkDBModel)  # type: ignore

        # ORM models returned by the upsert query
        sinks_dbmodels = session.scalars(
            upsert_stmt,
            sink_dicts,
            execution_options={"populate_existing": True},
        )

        # Replace the many-to-many thing-node associations in bulk (see upsert_sources).
        sink_ids, sink_association_rows = _collect_thing_node_associations(
            sinks_dbmodels, existing_thing_nodes, "sink_id"
        )
        session.execute(
            delete(thingnode_sink_association).where(
                thingnode_sink_association.c.sink_id.in_(sink_ids)
            )
        )
        if sink_association_rows:
            session.execute(insert(thingnode_sink_association), sink_association_rows)

    except IntegrityError as e:
        logger.error("Integrity Error while upserting StructureServiceSinkDBModel: %s", e)
        raise DBIntegrityError("Integrity Error while upserting StructureServiceSinkDBModel") from e
    except ValueError as e:
        logger.error("Value error while upserting StructureServiceSinkDBModel: %s", e)
        raise DBUpdateError("Value error while upserting StructureServiceSinkDBModel") from e
    except Exception as e:
        logger.exception("Unexpected error while upserting StructureServiceSinkDBModel")
        raise DBUpdateError("Unexpected error while upserting StructureServiceSinkDBModel") from e

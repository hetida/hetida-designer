import logging
from itertools import batched
from math import ceil
from uuid import UUID

from sqlalchemy import Connection, Engine
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

    logger.debug(
        "Successfully fetched collection of %d StructureServiceSources "
        "from the database for %d IDs. StructureServiceSources with IDs: %s",
        len(sources),
        len(src_ids),
        src_ids,
    )
    with get_session()() as session:
        for id_batch in batched(src_ids, ceil(len(src_ids) / batch_size)):
            batch_query = session.query(StructureServiceSourceDBModel).filter(
                StructureServiceSourceDBModel.id.in_(id_batch)
            )
            batch_results = batch_query.all()
            for src in batch_results:
                sources[src.id] = StructureServiceSource.from_orm_model(src)

    if not sources:
        raise DBNotFoundError(f"No StructureServiceSources found for IDs {src_ids}")

    logger.debug("Successfully fetched collection of StructureServiceSources.")
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

    logger.debug("Fetching collection of StructureServiceSinks with IDs: %s", sink_ids)

    logger.debug(
        "Successfully fetched collection of %d StructureServiceSinks from the database for %d IDs. "
        "StructureServiceSinks with IDs: %s",
        len(sinks),
        len(sink_ids),
        sink_ids,
    )
    with get_session()() as session:
        for id_batch in batched(sink_ids, ceil(len(sink_ids) / batch_size)):
            batch_query = session.query(StructureServiceSinkDBModel).filter(
                StructureServiceSinkDBModel.id.in_(id_batch)
            )
            batch_results = batch_query.all()
            for sink in batch_results:
                sinks[sink.id] = StructureServiceSink.from_orm_model(sink)

    if not sinks:
        raise DBNotFoundError(f"No StructureServiceSinks found for IDs {sink_ids}")

    logger.debug("Successfully fetched collection of StructureServiceSinks.")
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
                .filter(StructureServiceSourceDBModel.name.ilike(f"%{filter_string}%"))
                .all()
            )
            logger.debug(
                "Found %d StructureServiceSourceDBModel items matching filter "
                "string '%s' from %d total records.",
                len(matching_sources),
                filter_string,
                session.query(StructureServiceSourceDBModel).count(),
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
            logger.error(
                "Unexpected error while filtering StructureServiceSourceDBModel "
                "by substring match: %s",
                e,
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
                .filter(StructureServiceSinkDBModel.name.ilike(f"%{filter_string}%"))
                .all()
            )
            logger.debug(
                "Found %d StructureServiceSinkDBModel items matching "
                "filter string '%s' from %d total records.",
                len(matching_sinks),
                filter_string,
                session.query(StructureServiceSinkDBModel).count(),
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
            logger.error(
                "Unexpected error while filtering StructureServiceSinkDBModel "
                "by substring match: %s",
                e,
            )
            raise DBError(
                "Unexpected error while filtering StructureServiceSinkDBModel by substring match"
            ) from e


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
    source_dicts = [src.dict() for src in sources]

    try:
        engine: Engine | Connection = session.get_bind()
        if isinstance(engine, Connection):
            raise ValueError("The session in use has to be bound to an Engine not a Connection.")

        upsert_stmt: sqlite_insert_typing | pg_insert_typing

        if is_postgresql(engine):
            upsert_stmt = pg_insert(StructureServiceSourceDBModel).values(source_dicts)
        elif is_sqlite(engine):
            upsert_stmt = sqlite_insert(StructureServiceSourceDBModel).values(source_dicts)
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
            execution_options={"populate_existing": True},
        )

        # Assign relationships
        for source in sources_dbmodels:
            source.thing_nodes = [
                existing_thing_nodes.get((source.stakeholder_key, tn_external_id))
                for tn_external_id in source.thing_node_external_ids or []
                if (source.stakeholder_key, tn_external_id) in existing_thing_nodes
            ]

    except IntegrityError as e:
        logger.error("Integrity Error while upserting StructureServiceSourceDBModel: %s", e)
        raise DBIntegrityError(
            "Integrity Error while upserting StructureServiceSourceDBModel"
        ) from e
    except ValueError as e:
        logger.error("Value error while upserting StructureServiceSourceDBModel: %s", e)
        raise DBUpdateError("Value error while upserting StructureServiceSourceDBModel") from e
    except Exception as e:
        logger.error("Unexpected error while upserting StructureServiceSourceDBModel: %s", e)
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
    sink_dicts = [sink.dict() for sink in sinks]

    try:
        engine: Engine | Connection = session.get_bind()
        if isinstance(engine, Connection):
            raise ValueError("The session in use has to be bound to an Engine not a Connection.")

        upsert_stmt: sqlite_insert_typing | pg_insert_typing

        if is_postgresql(engine):
            upsert_stmt = pg_insert(StructureServiceSinkDBModel).values(sink_dicts)
        elif is_sqlite(engine):
            upsert_stmt = sqlite_insert(StructureServiceSinkDBModel).values(sink_dicts)
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
            execution_options={"populate_existing": True},
        )

        # Assign relationships
        for sink in sinks_dbmodels:
            sink.thing_nodes = [
                existing_thing_nodes.get((sink.stakeholder_key, tn_external_id))
                for tn_external_id in sink.thing_node_external_ids or []
                if (sink.stakeholder_key, tn_external_id) in existing_thing_nodes
            ]

    except IntegrityError as e:
        logger.error("Integrity Error while upserting StructureServiceSinkDBModel: %s", e)
        raise DBIntegrityError("Integrity Error while upserting StructureServiceSinkDBModel") from e
    except ValueError as e:
        logger.error("Value error while upserting StructureServiceSinkDBModel: %s", e)
        raise DBUpdateError("Value error while upserting StructureServiceSinkDBModel") from e
    except Exception as e:
        logger.error("Unexpected error while upserting StructureServiceSinkDBModel: %s", e)
        raise DBUpdateError("Unexpected error while upserting StructureServiceSinkDBModel") from e

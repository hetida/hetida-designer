import logging

from sqlalchemy import Connection, Engine
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.postgresql.dml import Insert as pg_insert_typing
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.dialects.sqlite.dml import Insert as sqlite_insert_typing
from sqlalchemy.exc import IntegrityError

from hetdesrun.persistence.db_engine_and_session import SQLAlchemySession
from hetdesrun.persistence.structure_service_dbmodels import StructureServiceElementTypeDBModel
from hetdesrun.structure.db.exceptions import DBIntegrityError, DBUpdateError
from hetdesrun.structure.models import StructureServiceElementType
from hetdesrun.structure.utils import is_postgresql, is_sqlite

logger = logging.getLogger(__name__)


def upsert_element_types(
    session: SQLAlchemySession,
    elements: list[StructureServiceElementType],
) -> dict[tuple[str, str], StructureServiceElementTypeDBModel]:
    """Insert or update element type records in the database.

    For each StructureServiceElementType, updates existing records if they are found;
    otherwise, creates new records. Returns the element type as a dictionary indexed
    by (stakeholder_key, external_id).
    """
    if not elements:
        return {}

    # Exclude non-column fields and ensure scalar types
    element_dicts = [
        {
            key: value
            for key, value in el.dict().items()
            if key != "thing_nodes" and not isinstance(value, list)
        }
        for el in elements
    ]

    try:
        engine: Engine | Connection = session.get_bind()
        if isinstance(engine, Connection):
            raise ValueError("The session in use has to be bound to an Engine, not a Connection.")

        upsert_stmt: sqlite_insert_typing | pg_insert_typing

        if is_postgresql(engine):
            upsert_stmt = pg_insert(StructureServiceElementTypeDBModel).values(element_dicts)
        elif is_sqlite(engine):
            upsert_stmt = sqlite_insert(StructureServiceElementTypeDBModel).values(element_dicts)
        else:
            raise ValueError(
                f"Unsupported database engine: {engine}. Please use either Postgres or SQLite."
            )

        upsert_stmt = upsert_stmt.on_conflict_do_update(
            index_elements=[
                "external_id",
                "stakeholder_key",
            ],  # Columns where insert looks for a conflict
            set_={
                col: upsert_stmt.excluded[col] for col in element_dicts[0] if col != "id"
            },  # Exclude primary key from update
        ).returning(StructureServiceElementTypeDBModel)  # type: ignore

        # ORM models returned by the upsert query
        element_dbmodels = session.scalars(
            upsert_stmt,
            execution_options={"populate_existing": True},
        )

        # Wrap DB models in dictionary for easier lookup
        element_dbmodel_dict = {(et.stakeholder_key, et.external_id): et for et in element_dbmodels}

        return element_dbmodel_dict

    except IntegrityError as e:
        logger.error("Integrity Error while upserting StructureServiceElementTypeDBModel: %s", e)
        raise DBIntegrityError(
            "Integrity Error while upserting StructureServiceElementTypeDBModel"
        ) from e
    except ValueError as e:
        logger.error("Value error while upserting StructureServiceElementTypeDBModel: %s", e)
        raise DBUpdateError("Value error while upserting StructureServiceElementTypeDBModel") from e
    except Exception as e:
        logger.error("Unexpected error while upserting StructureServiceElementTypeDBModel: %s", e)
        raise DBUpdateError(
            "Unexpected error while upserting StructureServiceElementTypeDBModel"
        ) from e

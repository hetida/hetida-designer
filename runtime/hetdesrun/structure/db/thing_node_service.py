import logging
from uuid import UUID

from sqlalchemy import Connection, Engine
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.postgresql.dml import Insert as pg_insert_typing
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.dialects.sqlite.dml import Insert as sqlite_insert_typing
from sqlalchemy.exc import IntegrityError

from hetdesrun.persistence.db_engine_and_session import SQLAlchemySession, get_session
from hetdesrun.persistence.structure_service_dbmodels import (
    StructureServiceElementTypeDBModel,
    StructureServiceThingNodeDBModel,
)
from hetdesrun.structure.db.exceptions import (
    DBIntegrityError,
    DBNotFoundError,
    DBUpdateError,
)
from hetdesrun.structure.models import StructureServiceThingNode
from hetdesrun.structure.utils import is_postgresql, is_sqlite

logger = logging.getLogger(__name__)


def fetch_single_thing_node_from_db_by_id(tn_id: UUID) -> StructureServiceThingNode:
    logger.debug("Fetching single StructureServiceThingNode from database with ID: %s", tn_id)
    with get_session()() as session:
        thing_node = (
            session.query(StructureServiceThingNodeDBModel)
            .filter(StructureServiceThingNodeDBModel.id == tn_id)
            .one_or_none()
        )
        if thing_node:
            logger.debug("StructureServiceThingNode with ID %s found.", tn_id)
            return StructureServiceThingNode.from_orm_model(thing_node)

    logger.warning("No StructureServiceThingNode found for ID %s.", tn_id)
    raise DBNotFoundError(f"No StructureServiceThingNode found for ID {tn_id}")


def update_parent_ids(
    thing_node_dbmodel_dict: dict[tuple[str, str], StructureServiceThingNodeDBModel],
) -> None:
    """Update parent IDs for thing nodes based on the current child-parent relationships.

    Ensures that `parent_node_id` attributes are updated in-place to reflect potential changes
    in the hierarchical structure defined in the incoming data.
    """
    for tn in thing_node_dbmodel_dict.values():
        if tn.parent_external_node_id:
            parent_key = (tn.stakeholder_key, tn.parent_external_node_id)
            parent = thing_node_dbmodel_dict.get(parent_key)
            if parent:
                tn.parent_node_id = parent.id


def upsert_thing_nodes(
    session: SQLAlchemySession,
    thing_nodes: list[StructureServiceThingNode],
    existing_element_types: dict[tuple[str, str], StructureServiceElementTypeDBModel],
) -> dict[tuple[str, str], StructureServiceThingNodeDBModel]:
    """Insert or update thing node records in the database.

    For each StructureServiceThingNode, updates existing records if they are found;
    otherwise, creates new records. Uses provided element types and returns the
    thing node as a dictionary indexed by (stakeholder_key, external_id).
    """

    # Prepare thing node records
    # Ensure the associated element type exists
    # to prevent foreign key constraint errors
    thing_node_dicts = []
    for node in thing_nodes:
        element_type = existing_element_types.get(
            (node.stakeholder_key, node.element_type_external_id)
        )
        if not element_type:
            logger.warning(
                "StructureServiceElementType with key (%s, %s) not found for "
                "StructureServiceThingNode %s. Skipping update.",
                node.stakeholder_key,
                node.element_type_external_id,
                node.name,
            )
            continue

        # Use node.dict() and add/override specific fields
        node_dict = node.dict()
        node_dict.update(
            {
                "element_type_id": element_type.id,  # Add foreign key
            }
        )
        thing_node_dicts.append(node_dict)

    if not thing_node_dicts:
        return {}

    try:
        engine: Engine | Connection = session.get_bind()
        if isinstance(engine, Connection):
            raise ValueError("The session in use has to be bound to an Engine, not a Connection.")

        upsert_stmt: sqlite_insert_typing | pg_insert_typing

        if is_postgresql(engine):
            upsert_stmt = pg_insert(StructureServiceThingNodeDBModel).values(thing_node_dicts)
        elif is_sqlite(engine):
            upsert_stmt = sqlite_insert(StructureServiceThingNodeDBModel).values(thing_node_dicts)
        else:
            raise ValueError(
                f"Unsupported database engine: {engine}. Please use either Postgres or SQLite."
            )

        excluded_dict = {}
        for col in thing_node_dicts[0]:
            # Exclude primary key (id) and parent_node_id as it is not read from db
            # but created in CompleteStructure
            if col in ("id", "parent_node_id"):
                continue
            excluded_dict[col] = upsert_stmt.excluded[col]

        upsert_stmt = upsert_stmt.on_conflict_do_update(
            index_elements=[
                "external_id",
                "stakeholder_key",
            ],  # Columns where insert looks for a conflict
            set_=excluded_dict,
        ).returning(StructureServiceThingNodeDBModel)  # type: ignore

        # ORM models returned by the upsert query
        thing_node_dbmodels = session.scalars(
            upsert_stmt,
            execution_options={"populate_existing": True},
        )

        # Wrap DB models in dictionary for easier lookup
        thing_node_dbmodel_dict = {
            (tn.stakeholder_key, tn.external_id): tn for tn in thing_node_dbmodels
        }

        update_parent_ids(thing_node_dbmodel_dict)

        return thing_node_dbmodel_dict

    except IntegrityError as e:
        logger.error("Integrity Error while upserting StructureServiceThingNodeDBModel: %s", e)
        raise DBIntegrityError(
            "Integrity Error while upserting StructureServiceThingNodeDBModel"
        ) from e
    except ValueError as e:
        logger.error("Value error while upserting StructureServiceThingNodeDBModel: %s", e)
        raise DBUpdateError("Value error while upserting StructureServiceThingNodeDBModel") from e
    except Exception as e:
        logger.error("Unexpected error while upserting StructureServiceThingNodeDBModel: %s", e)
        raise DBUpdateError(
            "Unexpected error while upserting StructureServiceThingNodeDBModel"
        ) from e

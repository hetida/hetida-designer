import json
import logging
from collections import defaultdict, deque
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy import and_, delete
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError

from hetdesrun.persistence.db_engine_and_session import get_session
from hetdesrun.persistence.structure_service_dbmodels import (
    StructureServiceElementTypeDBModel,
    StructureServiceSinkDBModel,
    StructureServiceSourceDBModel,
    StructureServiceThingNodeDBModel,
    thingnode_sink_association,
    thingnode_source_association,
)
from hetdesrun.structure.db.element_type_service import (
    upsert_element_types,
)
from hetdesrun.structure.db.exceptions import (
    DBAssociationError,
    DBConnectionError,
    DBError,
    DBIntegrityError,
    DBNotFoundError,
    DBUpdateError,
    JsonParsingError,
)
from hetdesrun.structure.db.source_sink_service import (
    upsert_sinks,
    upsert_sources,
)
from hetdesrun.structure.db.thing_node_service import upsert_thing_nodes
from hetdesrun.structure.models import (
    CompleteStructure,
    StructureServiceSink,
    StructureServiceSource,
    StructureServiceThingNode,
)

logger = logging.getLogger(__name__)


def load_structure_from_json_file(file_path: str) -> CompleteStructure:
    logger.debug("Loading structure from JSON file at %s.", file_path)
    try:
        with open(file_path) as file:
            structure_json = json.load(file)
        logger.debug("Successfully loaded JSON from %s.", file_path)

        # Attempt to create a CompleteStructure from the loaded JSON data
        complete_structure = CompleteStructure(**structure_json)
        logger.debug("Successfully created CompleteStructure from JSON data.")

        return complete_structure

    except FileNotFoundError:
        logger.error("File not found: %s", file_path)
        raise

    except json.JSONDecodeError as e:
        logger.error("JSON parsing error in file %s: %s", file_path, str(e))
        raise JsonParsingError(f"Error parsing JSON structure in file {file_path}: {str(e)}") from e

    except TypeError as e:
        logger.error("Type error while creating CompleteStructure from %s: %s", file_path, str(e))
        raise JsonParsingError(
            f"Error converting JSON data to CompleteStructure from file {file_path}: {str(e)}"
        ) from e

    except ValidationError as e:
        # Raised if JSON data doesn't match expected fields or formats in CompleteStructure
        logger.error(
            "Validation error while creating CompleteStructure from %s: %s", file_path, str(e)
        )
        raise JsonParsingError(
            f"Validation error for JSON data in file {file_path}: {str(e)}"
        ) from e

    except Exception as e:
        logger.error(
            "Unexpected error while loading or parsing structure from %s: %s", file_path, str(e)
        )
        raise JsonParsingError(
            f"Unexpected error while loading or parsing structure from {file_path}: {str(e)}"
        ) from e


def set_parent_ids(
    thing_nodes: list[StructureServiceThingNode],
) -> dict[UUID, list[StructureServiceThingNode]]:
    """Set parent IDs for thing nodes and return child mapping by parent node ID."""

    # Create a mapping for quick parent lookup by external_id
    thing_node_map = {(tn.stakeholder_key, tn.external_id): tn for tn in thing_nodes}

    # Collect child nodes under their parent's ID
    children_by_node_id: dict[UUID, list[StructureServiceThingNode]] = defaultdict(list)

    for tn in thing_nodes:
        if tn.parent_external_node_id:
            parent_key = (tn.stakeholder_key, tn.parent_external_node_id)
            parent_tn = thing_node_map.get(parent_key)
            if parent_tn:
                children_by_node_id[parent_tn.id].append(tn)
                logger.debug(
                    "StructureServiceThingNode %s added as child to parent ID %s.",
                    tn.name,
                    parent_tn.id,
                )
                # In-place modification: Setting parent_node_id directly on the node
                tn.parent_node_id = parent_tn.id
            else:
                # Skip orphan nodes (missing parents);
                # they won't be added to the child mapping
                logger.warning(
                    "Parent node with key %s not found for node %s. Skipping.",
                    parent_key,
                    tn.name,
                )

    return children_by_node_id


def sort_thing_nodes(
    thing_nodes: list[StructureServiceThingNode],
) -> list[StructureServiceThingNode]:
    """Sort thing nodes by hierarchical levels and set parent IDs."""

    # Set parent IDs for thing nodes and return child mapping by parent node ID
    children_by_node_id = set_parent_ids(thing_nodes)

    # Identify root nodes (nodes without a parent)
    root_nodes = [tn for tn in thing_nodes if tn.parent_external_node_id is None]

    logger.debug("Identified %d root nodes: %s", len(root_nodes), [tn.name for tn in root_nodes])

    # Sort nodes hierarchically using Breadth-First Search
    sorted_nodes_by_level = defaultdict(list)

    # Initialize BFS queue with root nodes at level 0
    queue = deque([(root_nodes, 0)])

    while queue:
        current_level_nodes, level = queue.popleft()
        next_level_nodes = []

        logger.debug("Processing level %d with %d nodes.", level, len(current_level_nodes))

        for node in current_level_nodes:
            sorted_nodes_by_level[level].append(node)
            children = children_by_node_id.get(node.id, [])
            # Sort children alphabetically by their external_id
            children_sorted = sorted(children, key=lambda x: x.external_id)
            next_level_nodes.extend(children_sorted)

        if next_level_nodes:
            queue.append((next_level_nodes, level + 1))
            logger.debug("Queueing %d nodes for level %d.", len(next_level_nodes), level + 1)

    # Flatten the sorted levels;
    # Orphan nodes were excluded in set_parent_ids()
    flattened_nodes = [
        node
        for level in sorted(sorted_nodes_by_level.keys())
        for node in sorted_nodes_by_level[level]
    ]
    logger.debug(
        "Flattened StructureServiceThingNodes into a list of %d nodes, excluding orphan nodes.",
        len(flattened_nodes),
    )

    return flattened_nodes


def update_structure(complete_structure: CompleteStructure) -> None:
    """Update or insert a complete structure into the database."""
    logger.debug("Starting update or insert operation for the complete structure in the database.")
    try:
        with get_session()() as session, session.begin():
            existing_element_types = upsert_element_types(session, complete_structure.element_types)

            sort_thing_nodes(complete_structure.thing_nodes)

            existing_thing_nodes = upsert_thing_nodes(
                session, complete_structure.thing_nodes, existing_element_types
            )

            upsert_sources(session, complete_structure.sources, existing_thing_nodes)
            upsert_sinks(session, complete_structure.sinks, existing_thing_nodes)

    except IntegrityError as e:
        logger.error("Integrity Error while updating or inserting the structure: %s", e)
        raise DBIntegrityError("Integrity Error while updating or inserting the structure") from e
    except OperationalError as e:
        logger.error("Operational Error while updating or inserting the structure: %s", e)
        raise DBConnectionError(
            "Operational Error while updating or inserting the structure"
        ) from e
    except DBAssociationError as e:
        logger.error("Association Error: %s", e)
        raise
    except DBUpdateError as e:
        logger.error("Update Error: %s", e)
        raise
    except DBError as e:
        logger.error("General DB Error: %s", e)
        raise
    except Exception as e:
        logger.error("Unexpected Error while updating or inserting the structure: %s", e)
        raise DBError("Unexpected Error while updating or inserting the structure") from e

    logger.debug("Completed update or insert operation for the complete structure.")


def update_structure_from_file(file_path: str) -> None:
    """Update the database structure using a JSON file.

    Loads the structure from the file and update the database records.
    """
    logger.debug("Updating structure from JSON file at path: %s.", file_path)

    # Load structure
    try:
        complete_structure: CompleteStructure = load_structure_from_json_file(file_path)
        logger.debug("Successfully loaded structure from JSON file.")
    except Exception as e:
        logger.error("Error while loading structure from JSON file: %s", e)
        raise

    # Update structure
    try:
        update_structure(complete_structure)
        logger.debug("Successfully updated structure in the database.")
    except Exception as e:
        logger.error("Error while updating structure in the database: %s", e)
        raise


def are_structure_tables_empty() -> bool:
    """Check if the structure-related tables in the database are empty.

    Verifies the presence of records in structure-specific tables.
    """
    logger.debug("Checking if the database is empty.")
    with get_session()() as session:
        is_empty = not (
            session.query(StructureServiceElementTypeDBModel).first() is not None
            or session.query(StructureServiceThingNodeDBModel).first() is not None
            or session.query(StructureServiceSourceDBModel).first() is not None
            or session.query(StructureServiceSinkDBModel).first() is not None
        )

    logger.debug("Database empty status: %s", is_empty)
    return is_empty


def get_children(
    parent_id: UUID | None,
) -> tuple[
    list[StructureServiceThingNode], list[StructureServiceSource], list[StructureServiceSink]
]:
    """Retrieve the child nodes associated with a given parent node from the database.

    If `parent_id` is None, returns the root nodes (nodes without a parent),
    along with any sources and sinks associated with the root nodes. Otherwise,
    fetches the direct child nodes, sources, and sinks associated with the
    specified parent node.
    """

    try:
        logger.debug("Fetching children for parent_id: %s", parent_id)

        with get_session()() as session:
            child_nodes_orm = (
                session.query(StructureServiceThingNodeDBModel)
                .filter(StructureServiceThingNodeDBModel.parent_node_id == parent_id)
                .all()
            )
            logger.debug(
                "Fetched %d child nodes out of %d total records.",
                len(child_nodes_orm),
                session.query(StructureServiceThingNodeDBModel).count(),
            )

            if parent_id is None:
                # Handle root nodes separately
                logger.debug("Fetching sources and sinks for root nodes.")
                sources_orm = []
                sinks_orm = []
            else:
                parent_node = (
                    session.query(StructureServiceThingNodeDBModel)
                    .filter(StructureServiceThingNodeDBModel.id == parent_id)
                    .one_or_none()
                )

                if parent_node is None:
                    logger.warning(
                        "The prodived ID %s has no corresponding node in the database", parent_id
                    )
                    raise DBNotFoundError(
                        f"The prodived ID {parent_id} has no corresponding node in the database"
                    )

                # Fetch StructureServiceSources associated with this StructureServiceThingNode
                sources_orm = (
                    session.query(StructureServiceSourceDBModel)
                    .join(
                        thingnode_source_association,
                        and_(
                            StructureServiceSourceDBModel.id
                            == thingnode_source_association.c.source_id,
                        ),
                    )
                    .filter(
                        thingnode_source_association.c.thingnode_id == parent_id,
                    )
                    .all()
                )
                logger.debug(
                    "Fetched %d sources out of %d total records.",
                    len(sources_orm),
                    session.query(StructureServiceSourceDBModel).count(),
                )

                # Fetch StructureServiceSinks associated with this StructureServiceThingNode
                sinks_orm = (
                    session.query(StructureServiceSinkDBModel)
                    .join(
                        thingnode_sink_association,
                        and_(
                            StructureServiceSinkDBModel.id == thingnode_sink_association.c.sink_id,
                        ),
                    )
                    .filter(
                        thingnode_sink_association.c.thingnode_id == parent_id,
                    )
                    .all()
                )
                logger.debug(
                    "Fetched %d sinks out of %d total records.",
                    len(sinks_orm),
                    session.query(StructureServiceSinkDBModel).count(),
                )

            return (
                [StructureServiceThingNode.from_orm_model(node) for node in child_nodes_orm],
                [StructureServiceSource.from_orm_model(source) for source in sources_orm],
                [StructureServiceSink.from_orm_model(sink) for sink in sinks_orm],
            )
    except IntegrityError as e:
        logger.error(
            "Integrity error while fetching children for parent_id %s: %s", parent_id, str(e)
        )
        raise DBIntegrityError(
            f"Integrity error while fetching children for parent_id {parent_id}"
        ) from e


def delete_structure() -> None:
    """Delete all structure-related data from the database.

    Clears all associations and related ORM records while maintaining referential integrity.
    """
    logger.debug("Starting deletion of all structure data from the database.")

    with get_session()() as session:
        try:
            logger.info("Deleting records from table: thingnode_source_association")
            session.execute(delete(thingnode_source_association))

            logger.info("Deleting records from table: thingnode_sink_association")
            session.execute(delete(thingnode_sink_association))

            logger.info("Deleting records from table: StructureServiceSourceDBModel")
            session.execute(delete(StructureServiceSourceDBModel))

            logger.info("Deleting records from table: StructureServiceSinkDBModel")
            session.execute(delete(StructureServiceSinkDBModel))

            logger.info("Deleting records from table: StructureServiceThingNodeDBModel")
            session.execute(delete(StructureServiceThingNodeDBModel))

            logger.info("Deleting records from table: StructureServiceElementTypeDBModel")
            session.execute(delete(StructureServiceElementTypeDBModel))

            session.commit()
            logger.info("Successfully deleted all structure data from the database.")

        except IntegrityError as e:
            msg = f"Integrity Error while deleting structure: {str(e)}"
            logger.error(msg)
            raise DBIntegrityError(msg) from e
        except SQLAlchemyError as e:
            msg = f"Database Error while deleting structure: {str(e)}"
            logger.error(msg)
            raise DBError(msg) from e
        except Exception as e:
            msg = f"Unexpected Error while deleting structure: {str(e)}"
            logger.error(msg)
            raise DBError(msg) from e

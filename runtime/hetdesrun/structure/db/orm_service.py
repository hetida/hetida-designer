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

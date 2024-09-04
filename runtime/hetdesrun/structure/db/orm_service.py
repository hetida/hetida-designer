import json
import logging
from collections import defaultdict, deque
from collections.abc import Sequence
from typing import Any
from uuid import UUID

from sqlalchemy import Table, delete

from hetdesrun.persistence.db_engine_and_session import SQLAlchemySession, get_session
from hetdesrun.persistence.structure_service_dbmodels import (
    ElementTypeOrm,
    SinkOrm,
    SourceOrm,
    ThingNodeOrm,
    thingnode_sink_association,
    thingnode_source_association,
)
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
    logger.debug("Fetched %d element types from the database.", len(element_types))
    return element_types


def fetch_all_thing_nodes(session: SQLAlchemySession) -> list[ThingNodeOrm]:
    thing_nodes = session.query(ThingNodeOrm).all()
    logger.debug("Fetched %d thing nodes from the database", len(thing_nodes))
    return thing_nodes


def fetch_all_sources(session: SQLAlchemySession) -> list[SourceOrm]:
    sources = session.query(SourceOrm).all()
    logger.debug("Fetched %d sources from the database.", len(sources))
    return sources


def fetch_all_sinks(session: SQLAlchemySession) -> list[SinkOrm]:
    sinks = session.query(SinkOrm).all()
    logger.debug("Fetched %d sinks from the database.", len(sinks))
    return sinks


# Structure Services
def load_structure_from_json_file(
    file_path: str,
) -> CompleteStructure:
    logger.debug("Loading structure from JSON file at %s.", file_path)
    try:
        with open(file_path) as file:
            structure_json = json.load(file)
        logger.debug("Successfully loaded JSON from %s.", file_path)
        complete_structure = CompleteStructure(**structure_json)
        logger.debug("Successfully created CompleteStructure from JSON data.")
        return complete_structure
    except Exception as e:
        logger.error("Failed to load or parse structure from %s: %s", file_path, str(e))
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
    logger.debug("Starting to sort ThingNodes into hierarchical levels.")
    logger.debug("Number of ThingNodes to process: %d", len(thing_nodes))
    logger.debug("Number of existing ThingNodes: %d", len(existing_thing_nodes))

    # Map existing ThingNodes from the database to a dictionary using a unique key
    existing_node_map = {
        (node.stakeholder_key or "") + (node.external_id or ""): node
        for node in existing_thing_nodes.values()
    }

    logger.debug("Mapped existing ThingNodes to keys: %s", list(existing_node_map.keys()))

    # Assign existing IDs to new nodes if they match by stakeholder_key + external_id
    for node in thing_nodes:
        key = node.stakeholder_key + node.external_id
        existing_node = existing_node_map.get(key)
        if existing_node:
            node.id = existing_node.id  # Retain the existing ID for the node
            logger.debug("Node %s matched with existing node, ID retained: %s", node.name, node.id)

    # Initialize a dictionary to hold the children of each node, and an empty list for root nodes
    children_by_node_id: dict[UUID, list[ThingNode]] = {node.id: [] for node in thing_nodes}
    root_nodes = []

    # Iterate through each node to populate the children list or identify root nodes
    for node in thing_nodes:
        if node.parent_node_id:
            if node.parent_node_id not in children_by_node_id:
                children_by_node_id[node.parent_node_id] = []
            children_by_node_id[node.parent_node_id].append(node)
            logger.debug("Node %s added as child to parent ID: %s", node.name, node.parent_node_id)
        else:
            root_nodes.append(node)
            logger.debug("Node %s identified as root node.", node.name)

    # Dictionary to hold nodes sorted by their hierarchical levels
    sorted_nodes_by_level = defaultdict(list)
    # Queue for breadth-first traversal, starting with root nodes
    queue = deque([(root_nodes, 0)])

    # Perform breadth-first traversal to sort nodes by levels
    while queue:
        current_level_nodes, level = queue.popleft()
        next_level_nodes = []

        logger.debug("Processing level %d with %d nodes.", level, len(current_level_nodes))

        for node in current_level_nodes:
            # Add the current node to its respective level in the sorted dictionary
            sorted_nodes_by_level[level].append(node)
            if node.id in children_by_node_id:
                # Sort the children nodes by their external_id
                children_by_node_id[node.id].sort(key=lambda x: x.external_id)
                # Prepare the nodes for the next level of traversal
                next_level_nodes.extend(children_by_node_id[node.id])

                logger.debug(
                    "Node %s at level %d has %d children.",
                    node.name,
                    level,
                    len(children_by_node_id[node.id]),
                )

        if next_level_nodes:
            logger.debug("Queueing %d nodes for next level %d.", len(next_level_nodes), level + 1)
            # Queue the next level nodes for processing
            queue.append((next_level_nodes, level + 1))

    logger.debug("Completed sorting ThingNodes into hierarchical levels.")
    return sorted_nodes_by_level


def fill_all_thingnode_element_type_ids_from_db(
    thing_nodes: list[ThingNode], existing_element_types: dict[str, ElementTypeOrm]
) -> None:
    """
    This function fills the element_type_id for each ThingNode using element types
    that have already been fetched from the database. The function itself does not
    query the database but relies on the provided existing_element_types.
    """
    logger.debug(
        "Filling element_type_id for each ThingNode using existing element types from the database."
    )
    for node in thing_nodes:
        if node.element_type_external_id:
            key = node.stakeholder_key + node.element_type_external_id
            db_et = existing_element_types.get(key)
            if db_et:
                node.element_type_id = db_et.id
                logger.debug(
                    "Set element_type_id %s for ThingNode with external_id %s.",
                    db_et.id,
                    node.external_id,
                )


def fill_all_thingnode_parent_uuids_from_db(
    thing_nodes: list[ThingNode], existing_thing_nodes: dict[str, ThingNodeOrm]
) -> None:
    """
    This function assigns parent_node_id for each ThingNode using parent nodes
    that have already been fetched from the database. It does not perform any direct
    database operations but works with the provided existing_thing_nodes.
    """
    logger.debug(
        "Assigning parent_node_id for each ThingNode using existing parent nodes from the database."
    )
    for node in thing_nodes:
        if node.parent_external_node_id:
            key = node.stakeholder_key + node.parent_external_node_id
            db_parent_tn = existing_thing_nodes.get(key)
            if db_parent_tn:
                node.parent_node_id = db_parent_tn.id
                logger.debug(
                    "Set parent_node_id for ThingNode with external_id %s.",
                    node.external_id,
                )
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
                    logger.debug(
                        "Found parent node in thing_nodes and set parent_node_id %s"
                        "for ThingNode with external_id %s.",
                        parent_node.id,
                        node.external_id,
                    )


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

    logger.debug(
        "Establishing associations between ThingNodes and their corresponding Sources and Sinks."
    )

    existing_thing_nodes = {
        tn.stakeholder_key + tn.external_id: tn for tn in session.query(ThingNodeOrm).all()
    }
    logger.debug(
        "Fetched %d existing ThingNodes from the database.",
        len(existing_thing_nodes),
    )

    existing_sources = {
        src.stakeholder_key + src.external_id: src for src in session.query(SourceOrm).all()
    }
    logger.debug(
        "Fetched %d existing Sources from the database.",
        len(existing_sources),
    )

    existing_sinks = {
        snk.stakeholder_key + snk.external_id: snk for snk in session.query(SinkOrm).all()
    }
    logger.debug(
        "Fetched %d existing Sinks from the database.",
        len(existing_sinks),
    )

    def process_db_associations(
        entities: list[Source | Sink],
        existing_entities: dict[str, Source | Sink],
        assoc_table: Table,
        entity_key: str,
    ) -> None:
        logger.debug("Processing associations for %d entities.", len(entities))
        for entity in entities:
            if not entity.thing_node_external_ids:
                logger.debug(
                    "Skipping entity with external_id %s as it has no associated ThingNodes.",
                    entity.external_id,
                )
                continue
            for tn_external_id in entity.thing_node_external_ids:
                tn_key = entity.stakeholder_key + tn_external_id
                thing_node = existing_thing_nodes.get(tn_key)
                if not thing_node:
                    logger.debug(
                        "ThingNode with key %s not found in existing ThingNodes, skipping.",
                        tn_key,
                    )
                    continue
                thing_node_id = thing_node.id
                entity_key_full = entity.stakeholder_key + entity.external_id
                db_entity = existing_entities.get(entity_key_full)
                if not db_entity:
                    logger.debug(
                        "Entity with key %s not found in existing entities, skipping.",
                        entity_key_full,
                    )
                    continue
                entity_id = db_entity.id
                association_exists = (
                    session.query(assoc_table)
                    .filter_by(thing_node_id=thing_node_id, **{entity_key: entity_id})
                    .first()
                )
                if association_exists:
                    logger.debug(
                        "Association already exists between ThingNode id %s and %s id %s.",
                        thing_node_id,
                        entity_key,
                        entity_id,
                    )
                else:
                    association = {
                        "thing_node_id": thing_node_id,
                        entity_key: entity_id,
                    }
                    session.execute(assoc_table.insert().values(association))
                    logger.debug(
                        "Created new association between ThingNode id %s and %s id %s.",
                        thing_node_id,
                        entity_key,
                        entity_id,
                    )

    logger.debug("Processing associations for Sources.")
    process_db_associations(
        complete_structure.sources,  # type: ignore
        existing_sources,
        thingnode_source_association,
        "source_id",
    )

    logger.debug("Processing associations for Sinks.")
    process_db_associations(
        complete_structure.sinks,  # type: ignore
        existing_sinks,
        thingnode_sink_association,
        "sink_id",
    )

    logger.debug(
        "Completed establishing associations between ThingNodes"
        " and their corresponding Sources and Sinks."
    )


def update_structure_from_file(file_path: str) -> CompleteStructure:
    logger.debug("Updating structure from JSON file at path: %s.", file_path)
    complete_structure = load_structure_from_json_file(file_path)
    logger.debug("Successfully loaded structure from JSON file.")
    return orm_update_structure(complete_structure)


def orm_update_structure(complete_structure: CompleteStructure) -> CompleteStructure:
    """
    This function updates or inserts the given complete structure into the database.
    """
    logger.debug("Starting update or insert operation for the complete structure in the database.")

    with get_session()() as session, session.begin():
        logger.debug("Fetching existing records from the database.")

        existing_element_types = fetch_existing_records(session, ElementTypeOrm)
        existing_thing_nodes = fetch_existing_records(session, ThingNodeOrm)
        existing_sources = fetch_existing_records(session, SourceOrm)
        existing_sinks = fetch_existing_records(session, SinkOrm)

        with session.no_autoflush:
            logger.debug("Updating or creating element types.")
            update_or_create_element_types(
                complete_structure.element_types, existing_element_types, session
            )
            session.flush()

            update_existing_elements(session, ElementTypeOrm, existing_element_types)

            logger.debug("Filling in element type IDs for thing nodes.")
            fill_all_thingnode_element_type_ids_from_db(
                complete_structure.thing_nodes, existing_element_types
            )

            logger.debug("Filling in parent node IDs for thing nodes.")
            fill_all_thingnode_parent_uuids_from_db(
                complete_structure.thing_nodes, existing_thing_nodes
            )

            logger.debug("Sorting and flattening the thing nodes hierarchy.")
            sorted_thing_nodes = sort_and_flatten_thing_nodes(
                complete_structure.thing_nodes, existing_thing_nodes
            )

            logger.debug("Updating or creating thing nodes.")
            update_or_create_thing_nodes(sorted_thing_nodes, existing_thing_nodes, session)
            session.flush()

            update_existing_elements(session, ThingNodeOrm, existing_thing_nodes)
            session.flush()

            logger.debug("Updating or creating sources.")
            update_or_create_sources_or_sinks(complete_structure.sources, existing_sources, session)
            session.flush()

            logger.debug("Updating or creating sinks.")
            update_or_create_sources_or_sinks(complete_structure.sinks, existing_sinks, session)
            session.flush()

            logger.debug("Establishing associations between thing nodes, sources, and sinks.")
            fill_source_sink_associations_db(complete_structure, session)

    logger.debug("Completed update or insert operation for the complete structure.")
    return complete_structure


def fetch_existing_records(session: SQLAlchemySession, model_class: Any) -> dict[str, Any]:
    """
    Fetches all records of the specified model class from the database and returns them as a
    dictionary with keys composed of stakeholder_key and external_id.
    """
    logger.debug("Fetching all records for model class %s from the database.", model_class.__name__)
    try:
        # Fetch all records of the given model class from the database
        records = session.query(model_class).all()
        logger.debug("Fetched %d records for model class %s.", len(records), model_class.__name__)
        # Create a dictionary mapping stakeholder_key + external_id to the record
        return {rec.stakeholder_key + rec.external_id: rec for rec in records}
    except Exception as e:
        # Log the error and re-raise the exception if something goes wrong
        logger.error("Error fetching records for model class %s: %s", model_class.__name__, str(e))
        raise


def update_or_create_element_types(
    elements: list[ElementType],
    existing_elements: dict[str, ElementTypeOrm],
    session: SQLAlchemySession,
) -> None:
    logger.debug("Updating or creating %d element types.", len(elements))
    for element in elements:
        key = element.stakeholder_key + element.external_id
        db_element = existing_elements.get(key)
        if db_element:
            logger.debug("Updating existing element with key %s.", key)
            element.id = db_element.id  # Set the existing ID
            db_element.name = element.name
            db_element.description = element.description
            db_element.stakeholder_key = element.stakeholder_key
        else:
            logger.debug("Creating new element with key %s.", key)
            new_element = element.to_orm_model()
            session.add(new_element)


def update_existing_elements(
    session: SQLAlchemySession, model_class: Any, existing_elements: dict[str, Any]
) -> None:
    """
    Updates the existing_elements dictionary with records
    from the database for the specified model class.
    """
    logger.debug("Updating existing elements dictionary for model class %s.", model_class.__name__)
    try:
        # Query the database for all records of the specified model class
        new_elements = {
            el.stakeholder_key + el.external_id: el for el in session.query(model_class).all()
        }
        # Update the existing_elements dictionary with the new elements from the database
        existing_elements.update(new_elements)
        logger.debug(
            "Successfully updated existing elements dictionary for model class %s.",
            model_class.__name__,
        )
    except Exception as e:
        # Log the error and re-raise the exception if something goes wrong
        logger.error(
            "Error updating existing elements for model class %s: %s", model_class.__name__, str(e)
        )
        raise


def sort_and_flatten_thing_nodes(
    thing_nodes: list[ThingNode], existing_thing_nodes: dict[str, ThingNodeOrm]
) -> list[ThingNode]:
    logger.debug("Sorting and flattening thing nodes.")
    sorted_nodes_by_level = sort_thing_nodes_from_db(thing_nodes, existing_thing_nodes)
    flattened_nodes = [node for nodes in sorted_nodes_by_level.values() for node in nodes]
    # Flattening the list of nodes is necessary to convert the hierarchical structure
    # into a single, ordered list.
    logger.debug("Flattened thing nodes into a list of %d nodes.", len(flattened_nodes))
    return flattened_nodes


def update_or_create_thing_nodes(
    thing_nodes: list[ThingNode],
    existing_thing_nodes: dict[str, ThingNodeOrm],
    session: SQLAlchemySession,
) -> None:
    """
    Updates existing thing nodes, or creates new ones if they do not exist.
    """
    logger.debug("Updating or creating %d thing nodes.", len(thing_nodes))
    for node in thing_nodes:
        key = node.stakeholder_key + node.external_id
        db_node = existing_thing_nodes.get(key)
        if db_node:
            logger.debug("Updating existing thing node with key %s.", key)
            node.id = db_node.id  # Set the existing ID
            db_node.name = node.name
            db_node.description = node.description
            db_node.element_type_id = node.element_type_id
            db_node.meta_data = node.meta_data
            db_node.parent_node_id = (
                node.parent_node_id if node.parent_node_id else db_node.parent_node_id
            )
        else:
            logger.debug("Creating new thing node with key %s.", key)
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
    logger.debug("Updating or creating %d sources or sinks.", len(sources_or_sinks))
    for item in sources_or_sinks:
        key = item.stakeholder_key + item.external_id
        db_item = existing_items.get(key)
        if db_item:
            logger.debug("Updating existing item with key %s.", key)
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
            logger.debug("Creating new item with key %s.", key)
            new_item = item.to_orm_model()
            session.add(new_item)


def orm_delete_structure(session: SQLAlchemySession) -> None:
    logger.debug("Deleting all structure data from the database.")
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
            logger.debug("Deleting records from table %s.", table)
            session.execute(delete(table))

        session.commit()
    except Exception as e:
        session.rollback()
        logger.error("Error during structure deletion: %s", str(e))
        raise


def orm_is_database_empty() -> bool:
    logger.debug("Checking if the database is empty.")
    with get_session()() as session:
        element_types = fetch_all_element_types(session)
        thing_nodes = fetch_all_thing_nodes(session)
        sources = fetch_all_sources(session)
        sinks = fetch_all_sinks(session)
        # TODO: Shorten function by only checking for ElementTypes?

    is_empty = not (element_types or thing_nodes or sources or sinks)
    logger.debug("Database empty status: %s", is_empty)

    return is_empty


def orm_get_children(
    parent_id: UUID | None,
) -> tuple[list[ThingNode], list[Source], list[Sink]]:
    """
    Retrieves the child nodes, sources, and sinks associated with a given parent
    node from the database.

    If `parent_id` is None, it returns the root nodes (nodes without a parent),
    along with any sources and sinks associated with the root nodes. Otherwise,
    it fetches the direct child nodes, sources, and sinks associated with the
    specified parent node.
    """

    logger.debug("Fetching children for parent_id: %s", parent_id)

    with get_session()() as session:
        if parent_id is None:
            logger.debug("No parent_id provided, fetching root nodes.")
            root_nodes = (
                session.query(ThingNodeOrm).filter(ThingNodeOrm.parent_node_id.is_(None)).all()
            )
            logger.debug("Fetched %d root nodes.", len(root_nodes))

            return (
                [ThingNode.from_orm_model(node) for node in root_nodes],
                [],
                [],
            )

        logger.debug("Fetching child nodes for parent_id: %s", parent_id)
        child_nodes = (
            session.query(ThingNodeOrm).filter(ThingNodeOrm.parent_node_id == parent_id).all()
        )
        logger.debug("Fetched %d child nodes.", len(child_nodes))

        logger.debug("Fetching sources for parent_id: %s", parent_id)
        sources = (
            session.query(SourceOrm)
            .join(
                thingnode_source_association,
                thingnode_source_association.c.source_id == SourceOrm.id,
            )
            .filter(thingnode_source_association.c.thing_node_id == parent_id)
            .all()
        )
        logger.debug("Fetched %d sources.", len(sources))

        logger.debug("Fetching sinks for parent_id: %s", parent_id)
        sinks = (
            session.query(SinkOrm)
            .join(thingnode_sink_association, thingnode_sink_association.c.sink_id == SinkOrm.id)
            .filter(thingnode_sink_association.c.thing_node_id == parent_id)
            .all()
        )
        logger.debug("Fetched %d sinks.", len(sinks))

        logger.debug(
            "Returning %d child nodes, %d sources, and %d sinks for parent_id: %s",
            len(child_nodes),
            len(sources),
            len(sinks),
            parent_id,
        )

        return (
            [ThingNode.from_orm_model(node) for node in child_nodes],
            [Source.from_orm_model(source) for source in sources],
            [Sink.from_orm_model(sink) for sink in sinks],
        )

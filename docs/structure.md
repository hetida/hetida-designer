
## Structure Package

The structure package provides a set of tools and services for managing hierarchical structures in IoT-based data systems. It includes utilities for interacting with databases, managing data entities like ThingNodes, Sources, and Sinks, and ensuring the integrity and consistency of these entities within the system.


## Components

### `structure_service_dbmodels.py`

The `structure_service_dbmodels.py` module defines the ORM (Object-Relational Mapping) models for the entities managed by the application, like ThingNodes, Sources, Sinks, and ElementTypes. These ORM models are used by SQLAlchemy to map Python objects to database records, allowing for smooth interaction with the underlying database.

### `models.py`

The `models.py` module defines Pydantic models that represent the data structures used within the application. These models are used to ensure that data remains consistent and valid as it moves through the application. Pydantic models are especially useful for structuring and validating data both internally within the application logic and when interacting with external APIs.

The `CompleteStructure` class in the `models.py` module encapsulates the entire hierarchical data structure within an IoT-based system, including all ThingNodes, Sources, Sinks, and ElementTypes. Its primary role is to provide a unified container that allows for comprehensive management of the hierarchical data. By maintaining consistent relationships between entities such as ThingNodes and their associated Sources and Sinks, `CompleteStructure` ensures data integrity throughout the system. Additionally, it simplifies operations involving multiple entities by offering a single interface for interacting with the entire structure, making it an essential tool for efficiently managing and manipulating the hierarchical data model within the application.

### `orm_service.py`

The `orm_service.py` module contains functions for direct database interactions using SQLAlchemy ORM models. These functions handle CRUD (Create, Read, Update, Delete) operations for entities such as ThingNodes, Sources, Sinks, and ElementTypes. Compared to `structure_service.py`, this module provides lower-level operations, which are useful for more detailed control over database actions.

### `structure_service.py`

The `structure_service.py` module offers high-level service functions that make it easier to interact with the database. These functions go beyond basic ORM operations and provide an abstracted interface for application use. They handle more complex tasks, like retrieving and managing hierarchical structures, deleting and updating data in the database, and checking the state of the database.

Some of the main features include:
- Retrieving child nodes, sources, and sinks that are associated with a specific parent node.
- Fetching single entities like ThingNodes, Sources, or Sinks from the database.
- Checking if the database is empty.
- Deleting the entire structure from the database.
- Updating the structure in the database with new or modified data.


### Integration with the Virtual Structure Adapter

The `structure_service.py` and `orm_service.py` modules manage the hierarchical data structure used by the [Virtual Structure Adapter](adapter_system/virtual_structure_adapter.md). They handle database operations like creating, reading, updating, and deleting elements. These modules keep the database data aligned with the requirements of the adapter. The `CompleteStructure` class is used to represent the entire hierarchy, allowing the adapter to work with the most recent data from the database. 


## Glossary of Classes and Functions

### Classes

- **`ThingNode`**: Represents a node in the hierarchical structure. It can have child nodes, and it might be linked with one or more Sources and Sinks.
- **`Source`**: Represents a data source within the system. Sources are linked with ThingNodes and provide data to the system.
- **`Sink`**: Represents a data sink within the system. Sinks are linked with ThingNodes and consume data from the system.
- **`ElementType`**: Represents the type of a ThingNode, defining its characteristics and behavior within the hierarchy.
- **`CompleteStructure`**: Encapsulates the entire hierarchical data structure, including all ThingNodes, Sources, Sinks, and ElementTypes. It ensures consistent relationships between these entities and provides a unified interface for managing and manipulating the entire structure as a single entity.


### Key Functions in `orm_service.py`

- **`fetch_all_element_types(session: SQLAlchemySession)`**: Fetches all ElementTypes from the database.

- **`fetch_all_sinks(session: SQLAlchemySession)`**: Fetches all Sinks from the database.

- **`fetch_all_sources(session: SQLAlchemySession)`**: Fetches all Sources from the database.

- **`fetch_all_thing_nodes(session: SQLAlchemySession)`**: Fetches all ThingNodes from the database.

- **`update_structure_from_file(file_path: str)`**: Loads a structure from a JSON file and updates the database with it.

- **`delete_structure(session: SQLAlchemySession)`**: Deletes all records from the database, effectively clearing the entire structure.

- **`is_database_empty()`**: Checks if the database is empty.


### Key Functions in `structure_service.py`

- **`get_children(parent_id: UUID | None)`**: Retrieves the child nodes, sources, and sinks associated with a given parent node. If `parent_id` is `None`, it returns the root nodes.
  
- **`get_single_thingnode_from_db(tn_id: UUID)`**: Fetches a single ThingNode from the database by its UUID. Raises an exception if the node is not found.

- **`get_collection_of_thingnodes_from_db(tn_ids: list[UUID])`**: Retrieves a collection of ThingNodes from the database, returned as a dictionary keyed by their UUIDs.

- **`get_single_source_from_db(src_id: UUID)`**: Fetches a single Source from the database by its UUID. Raises an exception if the source is not found.

- **`get_all_sources_from_db()`**: Fetches all Sources from the database.

- **`get_collection_of_sources_from_db(src_ids: list[UUID])`**: Retrieves a collection of Sources from the database, returned as a dictionary keyed by their UUIDs.

- **`get_single_sink_from_db(sink_id: UUID)`**: Fetches a single Sink from the database by its UUID. Raises an exception if the sink is not found.

- **`get_all_sinks_from_db()`**: Fetches all Sinks from the database.

- **`get_collection_of_sinks_from_db(sink_ids: list[UUID])`**: Retrieves a collection of Sinks from the database, returned as a dictionary keyed by their UUIDs.

- **`is_database_empty()`**: Checks if the database is empty.

- **`delete_structure()`**: Deletes the entire structure from the database.

- **`update_structure(complete_structure: CompleteStructure)`**: Updates or inserts the given complete structure into the database.


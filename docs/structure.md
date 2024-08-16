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

Some of the main features include:

- Retrieving all entities of a specific type (e.g., all ThingNodes, Sources, or Sinks) from the database.
- Fetching single entities like ThingNodes, Sources, or Sinks by their unique identifiers (UUIDs).
- Performing bulk updates or inserts of structures loaded from external JSON files into the database.
- Deleting the entire structure from the database, effectively clearing all related records.
- Checking if the database is empty, ensuring there are no residual records before new data is inserted.


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

- **`orm_delete_structure(session: SQLAlchemySession)`**: Deletes all records from the database, effectively clearing the entire structure.

- **`orm_is_database_empty()`**: Checks if the database is empty.

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

## Example JSON Structure for a Waterworks System

To provide a more concrete understanding of how the structure package is used in a real-world scenario, below is an example of a JSON configuration for a waterworks system. This example illustrates how the different entities such as ThingNodes, Sources, and Sinks are structured and connected within the hierarchical data model. The structure represents a waterworks facility with various nodes, including plants and storage tanks, and the associated data sources and sinks that manage and monitor energy consumption and anomaly detection.

This JSON configuration provides a comprehensive example of how to model and manage a complex IoT-based system like a waterworks within the structure package.

You can find this example in the file [`db_test_structure.json`](../runtime/tests/structure/data/db_test_structure.json).

```json
{
    "element_types": [
        {
            "external_id": "Wasserwerk_Typ",
            "stakeholder_key": "GW",
            "name": "Wasserwerk",
            "description": "Elementtyp für Wasserwerke"
        },
        {
            "external_id": "Anlage_Typ",
            "stakeholder_key": "GW",
            "name": "Anlage",
            "description": "Elementtyp für Anlagen"
        },
        {
            "external_id": "Hochbehaelter_Typ",
            "stakeholder_key": "GW",
            "name": "Hochbehälter",
            "description": "Elementtyp für Hochbehälter"
        }
    ],
    "thing_nodes": [
        {
            "external_id": "Wasserwerk1",
            "stakeholder_key": "GW",
            "name": "Wasserwerk 1",
            "description": "Root Node für das Wasserwerk 1",
            "parent_external_node_id": null,
            "element_type_external_id": "Wasserwerk_Typ",
            "meta_data": {
                "location": "Hauptstandort"
            }
        },
        {
            "external_id": "Wasserwerk1_Anlage1",
            "stakeholder_key": "GW",
            "name": "Anlage 1",
            "description": "Erste Anlage",
            "parent_external_node_id": "Wasserwerk1",
            "element_type_external_id": "Anlage_Typ",
            "meta_data": {
                "location": "Nord"
            }
        },
        {
            "external_id": "Wasserwerk1_Anlage2",
            "stakeholder_key": "GW",
            "name": "Anlage 2",
            "description": "Zweite Anlage",
            "parent_external_node_id": "Wasserwerk1",
            "element_type_external_id": "Anlage_Typ",
            "meta_data": {
                "location": "Süd"
            }
        },
        {
            "external_id": "Wasserwerk1_Anlage1_Hochbehaelter1",
            "stakeholder_key": "GW",
            "name": "Hochbehälter 1 Anlage 1",
            "description": "Erster Hochbehälter in Anlage 1",
            "parent_external_node_id": "Wasserwerk1_Anlage1",
            "element_type_external_id": "Hochbehaelter_Typ",
            "meta_data": {
                "capacity": "5000",
                "capacity_unit": "m³",
                "description": "Wasserspeicherungskapazität für Hochbehälter 1"
            }
        },
        {
            "external_id": "Wasserwerk1_Anlage1_Hochbehaelter2",
            "stakeholder_key": "GW",
            "name": "Hochbehälter 2 Anlage 1",
            "description": "Zweiter Hochbehälter in Anlage 1",
            "parent_external_node_id": "Wasserwerk1_Anlage1",
            "element_type_external_id": "Hochbehaelter_Typ",
            "meta_data": {
                "capacity": "6000",
                "capacity_unit": "m³",
                "description": "Wasserspeicherungskapazität für Hochbehälter 2"
            }
        },
        {
            "external_id": "Wasserwerk1_Anlage2_Hochbehaelter1",
            "stakeholder_key": "GW",
            "name": "Hochbehälter 1 Anlage 2",
            "description": "Erster Hochbehälter in Anlage 2",
            "parent_external_node_id": "Wasserwerk1_Anlage2",
            "element_type_external_id": "Hochbehaelter_Typ",
            "meta_data": {
                "capacity": "5500",
                "capacity_unit": "m³",
                "description": "Wasserspeicherungskapazität für Hochbehälter 1"
            }
        },
        {
            "external_id": "Wasserwerk1_Anlage2_Hochbehaelter2",
            "stakeholder_key": "GW",
            "name": "Hochbehälter 2 Anlage 2",
            "description": "Zweiter Hochbehälter in Anlage 2",
            "parent_external_node_id": "Wasserwerk1_Anlage2",
            "element_type_external_id": "Hochbehaelter_Typ",
            "meta_data": {
                "capacity": "7000",
                "capacity_unit": "m³",
                "description": "Wasserspeicherungskapazität für Hochbehälter 2"
            }
        }
    ],
    "sources": [
        {
            "external_id": "Energieverbraeuche_Pumpensystem_Hochbehaelter",
            "stakeholder_key": "GW",
            "name": "Energieverbräuche des Pumpensystems in Hochbehälter",
            "type": "multitsframe",
            "adapter_key": "sql-adapter",
            "source_id": "improvt_timescale_db/ts_table/ts_values",
            "meta_data": {
                "1010001": {
                    "unit": "kW/h",
                    "description": "Energieverbrauchsdaten für eine Einzelpumpe"
                },
                "1010002": {
                    "unit": "kW/h",
                    "description": "Energieverbrauchsdaten für eine Einzelpumpe"
                }
            },
            "preset_filters": {
                "metrics": "1010001, 1010002"
            },
            "passthrough_filters": [
                {
                    "name": "timestampFrom",
                    "type": "free_text",
                    "required": true
                },
                {
                    "name": "timestampTo",
                    "type": "free_text",
                    "required": false
                }
            ],
            "thing_node_external_ids": [
                "Wasserwerk1_Anlage1_Hochbehaelter1",
                "Wasserwerk1_Anlage2_Hochbehaelter2"
            ]
        },
        {
            "external_id": "Energieverbrauch_Einzelpumpe_Hochbehaelter",
            "stakeholder_key": "GW",
            "name": "Energieverbrauch einer Einzelpumpe in Hochbehälter",
            "type": "multitsframe",
            "adapter_key": "sql-adapter",
            "source_id": "improvt_timescale_db/ts_table/ts_values",
            "meta_data": {
                "1010003": {
                    "unit": "kW/h",
                    "description": "Energieverbrauchsdaten für eine Einzelpumpe"
                }
            },
            "preset_filters": {
                "metrics": "1010003"
            },
            "passthrough_filters": [
                {
                    "name": "timestampFrom",
                    "type": "free_text",
                    "required": true
                },
                {
                    "name": "timestampTo",
                    "type": "free_text",
                    "required": false
                }
            ],
            "thing_node_external_ids": [
                "Wasserwerk1_Anlage1_Hochbehaelter2",
                "Wasserwerk1_Anlage2_Hochbehaelter1"
            ]
        },
        {
            "external_id": "Energieverbrauch_Wasserwerk1",
            "stakeholder_key": "GW",
            "name": "Energieverbrauch des Wasserwerks",
            "type": "multitsframe",
            "adapter_key": "sql-adapter",
            "source_id": "improvt_timescale_db/ts_table/ts_values",
            "meta_data": {
                "1010004": {
                    "unit": "kW/h",
                    "description": "Energieverbrauchsdaten für das gesamte Wasserwerk"
                }
            },
            "preset_filters": {
                "metrics": "1010004"
            },
            "passthrough_filters": [
                {
                    "name": "timestampFrom",
                    "type": "free_text",
                    "required": true
                },
                {
                    "name": "timestampTo",
                    "type": "free_text",
                    "required": false
                }
            ],
            "thing_node_external_ids": [
                "Wasserwerk1"
            ]
        }
    ],
    "sinks": [
        {
            "external_id": "Anomaly_Score_Energieverbraeuche_Pumpensystem_Hochbehaelter",
            "stakeholder_key": "GW",
            "name": "Anomaly Score für die Energieverbräuche des Pumpensystems in Hochbehälter",
            "type": "multitsframe",
            "adapter_key": "sql-adapter",
            "sink_id": "improvt_timescale_db/ts_table/ts_values",
            "meta_data": {
                "10010001": {
                    "description": "Anomaly Score für eine Einzelpumpe",
                    "calculation_details": "Window size: 4h, Timestamp location: center"
                },
                "10010002": {
                    "description": "Anomaly Score für eine Einzelpumpe",
                    "calculation_details": "Window size: 4h, Timestamp location: center"
                }
            },
            "preset_filters": {
                "metrics": "10010001, 10010002"
            },
            "passthrough_filters": [
                {
                    "name": "timestampFrom",
                    "type": "free_text",
                    "required": true
                },
                {
                    "name": "timestampTo",
                    "type": "free_text",
                    "required": false
                }
            ],
            "thing_node_external_ids": [
                "Wasserwerk1_Anlage1_Hochbehaelter1",
                "Wasserwerk1_Anlage1_Hochbehaelter2"
            ]
        },
        {
            "external_id": "Anomaly_Score_Energieverbrauch_Einzelpumpe_Hochbehaelter",
            "stakeholder_key": "GW",
            "name": "Anomaly Score für den Energieverbrauch einer Einzelpumpe in Hochbehälter",
            "type": "multitsframe",
            "adapter_key": "sql-adapter",
            "sink_id": "improvt_timescale_db/ts_table/ts_values",
            "meta_data": {
                "10010003": {
                    "description": "Anomaly Score für eine Einzelpumpe",
                    "calculation_details": "Window size: 4h, Timestamp location: center"
                }
            },
            "preset_filters": {
                "metrics": "10010003"
            },
            "passthrough_filters": [
                {
                    "name": "timestampFrom",
                    "type": "free_text",
                    "required": true
                },
                {
                    "name": "timestampTo",
                    "type": "free_text",
                    "required": false
                }
            ],
            "thing_node_external_ids": [
                "Wasserwerk1_Anlage2_Hochbehaelter2",
                "Wasserwerk1_Anlage2_Hochbehaelter1"
            ]
        },
        {
            "external_id": "Anomaly_Score_Energieverbrauch_Wasserwerk1",
            "stakeholder_key": "GW",
            "name": "Anomaly Score für den Energieverbrauch des Wasserwerks",
            "type": "multitsframe",
            "adapter_key": "sql-adapter",
            "sink_id": "improvt_timescale_db/ts_table/ts_values",
            "meta_data": {
                "10010004": {
                    "description": "Anomaly Score für das gesamte Wasserwerk",
                    "calculation_details": "Window size: 4h, Timestamp location: center"
                }
            },
            "preset_filters": {
                "metrics": "10010004"
            },
            "passthrough_filters": [
                {
                    "name": "timestampFrom",
                    "type": "free_text",
                    "required": true
                },
                {
                    "name": "timestampTo",
                    "type": "free_text",
                    "required": false
                }
            ],
            "thing_node_external_ids": [
                "Wasserwerk1"
            ]
        }
    ]
}

# Virtual Structure Adapter

With the built-in Virtual Structure Adapter, users can create flexible, abstract hierarchical structures that superimpose a domain-specific view onto their data. The hierarchical organization ensures a high level of discoverability within the structure. Data can be located based on domain-specific criteria by navigating through the hierarchy. Unlike other adapters that deal directly with the input and output of data, the Virtual Structure Adapter serves as a conceptual overlay. It superimposes a domain-specific hierarchy over the sources and sinks managed by other adapters. These adapters are responsible for the actual data processing.

For example, this adapter can be used to specify a structure that represents the layout of a stock portfolio, an IoT system in the water industry, or any other domain-specific model.

## Key Concepts

The Virtual Structure Adapter relies on defined entities like ThingNodes, Sources, Sinks, and ElementTypes. These entities form the hierarchical structures managed by the adapter.

## Glossary of Concepts

The key concepts of the Virtual Structure Adapter are described below:

- **`ThingNode`**: Represents individual node elements within a hierarchical structure, e.g. a plant, a water treatment plant or a storage tank in a waterworks. ThingNodes can have parent-child relationships that help to create a clear, searchable structure of a system. They can be connected to one or more sources and sinks.
- **`Source`**: Represents data inputs within the system, e.g. sensor data from a pump in a waterworks plant. Sources are linked to ThingNodes and provide real-time or historical data that is fed into the system for analysis or monitoring.
- **`Sink`**:  Represents outputs or results within your system, such as calculated anomaly values based on energy consumption data. Sinks are linked to ThingNodes and are the endpoints where processed data is stored or used.
- **`ElementType`**: Defines the type of a ThingNode, e.g. 'Plant' or 'Storage Tank,' and encapsulates its properties and behavior within the hierarchy. This can help in conducting analyses based on specific criteria.
- **`CompleteStructure`**: Encapsulates the entire hierarchical data model, including ThingNodes, Sources, Sinks, and ElementTypes. Ensures the structure is managed as a unified whole with synchronized components. It validates and maintains consistent relationships between entities and provides a uniform interface for managing the entire structure.

## JSON Structure

### How to provide a structure

The hierarchical structure can be provided via a JSON assigned to the environment variable `STRUCTURE_TO_PREPOPULATE_VST_ADAPTER`. 

Below is a template for the JSON file:

```
{
    "element_types": [  // Contains element types for your data
        {
            "external_id": "string",  // An ID used in your organization
            "stakeholder_key": "string",  // Some short letter combination representing your org
            "name": "string",  // How you want to name the element type
            "description": "string"  // Arbitrary description
        },...
    ],
    "thing_nodes": [ // Contains thingnodes for your data
        {
            "external_id": "string",
            "stakeholder_key": "string",
            "name": "string",
            "description": "string",
            "parent_external_node_id": null or "string",  // referencing the parent of this node
            "element_type_external_id": "string", // referencing the element_type of this node
            "meta_data": {
                "key": "value"
            }
        },...
    ],
    "sources": [
        {
            "external_id": "string",
            "stakeholder_key": "string",
            "name": "string",
            "type": "string", // Representing the hetida designer datatype e.g. "timeseries(float)"
            "adapter_key": "string", // Key of the adapter that actually handles data in- and egestion, e.g. "demo-adapter-python"
            "source_id": "string",  // ID of the source in the target adapter
            "ref_key": "string",  // Optional key of the referenced metadatum, only used for sources of type metadata(any)
            "ref_id": "string",  // Optional ID of the thingnode in the mapped adapter hierarchy, which the mapped source references if source has type metadata(any)
            "meta_data": {
                "key": "value"
            },
            "passthrough_filters": [  // Values for filters that should be modifyable be the user
                {
                    "name": "string",
                    "type": "string",  // Which type the filter has, the designer defines specific types
                    "required": bool  // Whether this filter is required for the source to work properly
                },...
            ]
            "preset_filters": {"key": "value"},  // Values for filters that should not be modifyable by the user
            "thing_node_external_ids": [  // Parent IDs of this source
                "string1", "string2",...
            ]
        },...
    ],
    "sinks": [  // Analogous to source
        {
            "external_id": "string",
            "stakeholder_key": "string",
            "name": "string",
            "type": "string",
            "adapter_key": "string",
            "sink_id": "string",
            "ref_key": "string",
            "ref_id": "string",
            "meta_data": {
                "key": "value"
            },
            "passthrough_filters": [
                {
                    "name": "string",
                    "type": "string",
                    "required": bool
                },...
            ]
            "preset_filters": {"key": "value"},
            "thing_node_external_ids": [
                "string1", "string2",...
            ]
        }
    ]
}
```

### JSON structure example

An example of such a JSON file is provided below, demonstrating how the Virtual Structure Adapter can be used to organize an equity portfolio for a specific client.


```json
{
    "element_types": [  
        {
            "external_id": "et_portfolio",  
            "stakeholder_key": "ABC_BANK",  // ABC_BANK represents the client or stakeholder, e.g., a bank
            "name": "Portfolio",  
            "description": "A collection of various stocks in different sectors"
        },
        {
            "external_id": "et_sector",  
            "stakeholder_key": "ABC_BANK",  
            "name": "Sector",  
            "description": "A sector within the stock market, such as Technology or Healthcare"
        },
        {
            "external_id": "et_stock",  
            "stakeholder_key": "ABC_BANK",  
            "name": "Stock",  
            "description": "An individual stock within a sector"
        }
    ],
    "thing_nodes": [  
        {
            "external_id": "tn_portfolio_main",
            "stakeholder_key": "ABC_BANK",
            "name": "Main Portfolio",
            "description": "Main portfolio containing all sectors",
            "parent_external_node_id": null,
            "element_type_external_id": "et_portfolio",
            "meta_data": {
                "creation_date": "2023-01-01",
                "owner": "John Doe"
            }
        },
        {
            "external_id": "tn_technology_sector",
            "stakeholder_key": "ABC_BANK",
            "name": "Technology Sector",
            "description": "Technology stocks",
            "parent_external_node_id": "tn_portfolio_main",
            "element_type_external_id": "et_sector",
            "meta_data": {
                "sector_code": "TECH"
            }
        },
        {
            "external_id": "tn_healthcare_sector",
            "stakeholder_key": "ABC_BANK",
            "name": "Healthcare Sector",
            "description": "Healthcare stocks",
            "parent_external_node_id": "tn_portfolio_main",
            "element_type_external_id": "et_sector",
            "meta_data": {
                "sector_code": "HEALTH"
            }
        },
        {
            "external_id": "tn_stock_aapl",
            "stakeholder_key": "ABC_BANK",
            "name": "AAPL",
            "description": "Apple Inc. stock",
            "parent_external_node_id": "tn_technology_sector",
            "element_type_external_id": "et_stock",
            "meta_data": {
                "ticker": "AAPL",
                "exchange": "NASDAQ"
            }
        },
        {
            "external_id": "tn_stock_msft",
            "stakeholder_key": "ABC_BANK",
            "name": "MSFT",
            "description": "Microsoft Corp. stock",
            "parent_external_node_id": "tn_technology_sector",
            "element_type_external_id": "et_stock",
            "meta_data": {
                "ticker": "MSFT",
                "exchange": "NASDAQ"
            }
        },
        {
            "external_id": "tn_stock_jnj",
            "stakeholder_key": "ABC_BANK",
            "name": "JNJ",
            "description": "Johnson & Johnson stock",
            "parent_external_node_id": "tn_healthcare_sector",
            "element_type_external_id": "et_stock",
            "meta_data": {
                "ticker": "JNJ",
                "exchange": "NYSE"
            }
        }
    ],
    "sources": [
        {
            "external_id": "src_aapl_price_data",
            "stakeholder_key": "ABC_BANK",
            "name": "AAPL Price Data",
            "type": "timeseries(float)",  
            "adapter_key": "market-data-adapter",  
            "source_id": "aapl_timeseries",  
            "meta_data": {
                "unit": "USD"
            },
            "thing_node_external_ids": ["tn_stock_aapl"]
        },
        {
            "external_id": "src_msft_price_data",
            "stakeholder_key": "ABC_BANK",
            "name": "MSFT Price Data",
            "type": "timeseries(float)",  
            "adapter_key": "market-data-adapter",  
            "source_id": "msft_timeseries",  
            "meta_data": {
                "unit": "USD"
            },
            "thing_node_external_ids": ["tn_stock_msft"]
        },
        {
            "external_id": "src_jnj_price_data",
            "stakeholder_key": "ABC_BANK",
            "name": "JNJ Price Data",
            "type": "timeseries(float)",  
            "adapter_key": "market-data-adapter",  
            "source_id": "jnj_timeseries",  
            "meta_data": {
                "unit": "USD"
            },
            "thing_node_external_ids": ["tn_stock_jnj"]
        }
    ],
    "sinks": [
        {
            "external_id": "sink_aapl_volatility",
            "stakeholder_key": "ABC_BANK",
            "name": "AAPL Volatility Data",
            "type": "timeseries(float)",  
            "adapter_key": "storage-adapter",  
            "sink_id": "aapl_volatility_timeseries",  
            "meta_data": {
                "calculation": "volatility",
                "unit": "%"
            },
            "thing_node_external_ids": ["tn_stock_aapl"]
        },
        {
            "external_id": "sink_portfolio_return",
            "stakeholder_key": "ABC_BANK",
            "name": "Portfolio Return Data",
            "type": "timeseries(float)",  
            "adapter_key": "storage-adapter",  
            "sink_id": "portfolio_return_timeseries",  
            "meta_data": {
                "calculation": "return",
                "unit": "%"
            },
            "thing_node_external_ids": ["tn_portfolio_main"]
        }
    ]
}
```

## Configuration

There are several environment variables which can be used to configure the use of the virtual structure adapter.  
* `VST_ADAPTER_ACTIVE` (default `True`): Whether the adapter is active (registered in the designer application)
* `VST_ADAPTER_SERVICE_IN_RUNTIME` (default `True`): Whether the adapter is part of the backend or the runtime
* `PREPOPULATE_VST_ADAPTER_AT_HD_STARTUP` (default `False`): Set to `True` if you wish to provide a structure for the adapter at designer startup
* `STRUCTURE_TO_PREPOPULATE_VST_ADAPTER` (default `None`): One can assign a JSON defining a structure to this variable
* `COMPLETELY_OVERWRITE_EXISTING_VIRTUAL_STRUCTURE_AT_HD_STARTUP` (default `True`): This option controls whether a potentially existing structure in the database is removed during startup. When set to `True` (default), the existing structure is deleted entirely before the new structure specified in `STRUCTURE_TO_PREPOPULATE_VST_ADAPTER` is inserted. If set to `False`, the existing structure is retained and updated. New elements from the provided JSON structure will be added, and existing elements will be updated. Existing elements not specified in the new JSON structure will remain unchanged. To fully replace an existing structure, it must first be deleted, before inserting the new one.

## Technical Information

To process wirings with virtual structure adapter sources and sinks, an additional step in the execution pipeline of the hetida designer was introduced.  
Before the data is actually loaded from or passed to an adapter, all virtual structure adapter related information is removed from the wiring and replaced with information on the referenced source or sink. 
### Virtual Structure Adapter

The built-in Virtual Structure Adapter enables users to create flexible, abstract hierarchical structures that apply specific business logic to their data. Unlike other adapters that directly handle the in- and egestion of data, the Virtual Structure Adapter serves as a conceptual overlay. It imprints a business hierarchy or structure onto the sources and sinks managed by other adapters, which are responsible for the actual data processing.

This means that while the Virtual Structure Adapter does not interact with the data directly, it organizes and categorizes the data flow based on the business logic defined by the user. For instance, you can use this adapter to impose a structure that represents the layout of a stock portfolio, an IoT system in water management, or any other business-relevant model. This structure is then mapped onto the actual data-handling adapters, ensuring that the data is processed according to the defined business perspective.

## Key Concepts

The Virtual Structure Adapter relies on a set of defined entities, such as ThingNodes, Sources, Sinks, and ElementTypes, which collectively form the basis of the hierarchical structures that the adapter manages. These concepts help ensure that data is organized, categorized, and processed according to the business logic defined by the user.

## Glossary of Concepts

- **`ThingNode`**: Represents a node in the hierarchical structure. It can have child nodes, and it might be linked with one or more Sources and Sinks.
- **`Source`**: Represents a data source within the system. Sources are linked with ThingNodes and provide data to the system.
- **`Sink`**: Represents a data sink within the system. Sinks are linked with ThingNodes and consume data from the system.
- **`ElementType`**: Represents the type of a ThingNode, defining its characteristics and behavior within the hierarchy.
- **`CompleteStructure`**: Encapsulates the entire hierarchical data structure, including all ThingNodes, Sources, Sinks, and ElementTypes. It ensures consistent relationships between these entities and provides a unified interface for managing and manipulating the entire structure as a single entity.

## JSON Structure Example

The hierarchical structure can be provided via a JSON file assigned to the environment variable STRUCTURE_TO_PREPOPULATE_VST_ADAPTER. Below is an example of such a JSON file, illustrating how you might use the Virtual Structure Adapter to organize an equity portfolio for a specific client.


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
* `COMPLETELY_OVERWRITE_EXISTING_VIRTUAL_STRUCTURE_AT_HD_STARTUP` (default `True`): Determines whether an existing structure is completely deleted and then reinserted into the database. If this option is set to False, the existing structure can be updated by adding new elements or updating the content of existing elements based on the JSON file. However, elements that are not included in the new JSON structure will not be deleted. To fully replace the structure, it must first be deleted before reinserting the new one.
* `STRUCTURE_TO_PREPOPULATE_VST_ADAPTER` (default `None`): One can assign a JSON defining a structure to this variable

## Technical Information

To process wirings with virtual structure adapter sources and sinks, an additional step in the execution pipeline of the hetida designer was introduced.  
Before the data is actually loaded from or passed to an adapter, all virtual structure adapter related information is removed from the wiring and replaced with information on the referenced source or sink. 
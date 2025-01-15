# Virtual Structure Adapter

With the built-in Virtual Structure Adapter, users can create flexible, abstract hierarchical structures that provide a domain-specific view of their data and provides discoverability.

Unlike other adapters that deal directly with the input and output of data, the Virtual Structure Adapter serves as a conceptual overlay. It superimposes a domain-specific hierarchy over the sources and sinks managed by other adapters. For actual data receiving and sending the original adapters are used.

For example, this can be used to specify a structure that represents the layout of a stock portfolio, an IoT system in the water industry, or any other domain-specific model, where actual data is provided by a combination of sources from e.g. the sql adapter, kafka adapter or the local file adapter.

## Key Concepts

The Virtual Structure Adapter relies on defined entities like thing nodes, sources, sinks, and element types. These entities form the hierarchical structures managed by the adapter.

## Glossary of Concepts

The key concepts of the Virtual Structure Adapter are described below:

- **`Thing node`**: Represents individual node elements within a hierarchical structure, e.g. a plant, a water treatment plant or a storage tank in a waterworks. Thing nodes can have parent-child relationships that help to create a clear, searchable structure of a system. They can be connected to one or more sources and sinks.
- **`Source`**: References a source of an adapter, which handles actual data in- and egestion.
- **`Sink`**:  References a sink of an adapter, which handles actual data in- and egestion.
- **`Element type`**: Defines the type of a thing node, e.g. 'Plant' or 'Storage Tank,' and encapsulates its properties and behavior within the hierarchy. This attached information could be used as metadata in analyses, for example.

## JSON Structure

### How to provide a structure

The hierarchical structure can be provided in two configurative ways:
1. Via a JSON directly assigned to the environment variable `STRUCTURE_TO_PREPOPULATE_VST_ADAPTER` in the backend container.
2. Via a filepath pointing to a JSON-file assigned to the environment variable `STRUCTURE_FILEPATH_TO_PREPOPULATE_VST_ADAPTER` in the backend container.

During start of the hetida designer backend this configuration is applied and persisted according to the configuration described below. This process is called prepopulation.

Below is a specification for the JSON file:

```
{
    "element_types": [  // Contains element types for your data
        {
            "external_id": STRING,  // An ID used in your organization
            "stakeholder_key": STRING,  // Some short letter combination representing your org
            "name": STRING,  // How you want to name the element type
            "description": STRING  // Arbitrary description
        },...
    ],
    "thing_nodes": [ // Contains thingnodes for your data
        {
            "external_id": STRING,
            "stakeholder_key": STRING,
            "name": STRING,
            "description": STRING,
            "parent_external_node_id": null or STRING,  // referencing the parent of this node
            "element_type_external_id": STRING, // referencing the element_type of this node
            "meta_data": {
                "<key>": <value>
            }
        },...
    ],
    "sources": [
        {
            "external_id": STRING,
            "stakeholder_key": STRING,
            "name": STRING,
            "type": STRING, // Representing the hetida designer datatype e.g. "timeseries(float)"
            "adapter_key": STRING, // Key of the adapter that actually handles data in- and egestion, 
                                   // e.g. "demo-adapter-python"
            "source_id": STRING,   // ID of the source in the target adapter
            "ref_key": STRING,  // Optional key of the referenced metadatum, 
                                // only used for sources of type metadata(any)
            "ref_id": STRING,  // Optional ID of the thingnode in the mapped adapter hierarchy,
                               // which the mapped source references if source has type metadata(any)
            "meta_data": {
                "<key>": <value>
            },
            "passthrough_filters": [  // Values for filters that should be modifyable be the user
                {
                    "name": STRING,
                    "type": STRING,   // Which type the filter has, the designer defines specific types
                    "required": BOOL  // Whether this filter is required for the source to work properly
                },...
            ]
            "preset_filters": {"<key>": <value>},  // Values for filters that should not be modifyable by the user
            "thing_node_external_ids": [  // Parent IDs of this source
                STRING, STRING,...
            ]
        },...
    ],
    "sinks": [  // Analogous to source
        {
            "external_id": STRING,
            "stakeholder_key": STRING,
            "name": STRING,
            "type": STRING,
            "adapter_key": STRING,
            "sink_id": STRING,
            "ref_key": STRING,
            "ref_id": STRING,
            "meta_data": {
                "<key>": <value>
            },
            "passthrough_filters": [
                {
                    "name": STRING,
                    "type": STRING,
                    "required": BOOL
                },...
            ]
            "preset_filters": {"<key>": <value>},
            "thing_node_external_ids": [
                STRING, STRING,...
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

Configuration can be set via an env file which must be configured via the `HD_VST_ADAPTER_ENVIRONMENT_FILE` environment variable.
Additionally environment variables can be set directly (overriding possible settings from an env file).

Note that all configuration options have to be set for the backend service, where the adapter runs.

### Adapter Registration
`VST_ADAPTER_ACTIVE` (default `true`) determines whether the adapter is registered or not.

### Prepopulation configuration
All the following configuration options must be set for the hetida designer backend.

Prepopulation works as follows:

* `PREPOPULATE_VST_ADAPTER_AT_HD_STARTUP` (default `false`): Only if this is `true` prepopulation will be run at each hetida designer backend startup. 
* `PREPOPULATE_VST_ADAPTER_VIA_FILE` (default `false`): Whether to load the structure from a JSON-file or not. This has precedence over setting the structure directly via `STRUCTURE_TO_PREPOPULATE_VST_ADAPTER`. The path to the file has to be set via `STRUCTURE_FILEPATH_TO_PREPOPULATE_VST_ADAPTER`.
* `STRUCTURE_TO_PREPOPULATE_VST_ADAPTER` (default `null`): If no file is used, one can assign a JSON string defining the structure to this variable.
* `STRUCTURE_FILEPATH_TO_PREPOPULATE_VST_ADAPTER` (default `null`): One can assign a filepath pointing to a JSON-file containing the structure, which is used if `PREPOPULATE_VST_ADAPTER_VIA_FILE` is `true`.
* `COMPLETELY_OVERWRITE_EXISTING_VIRTUAL_STRUCTURE_AT_HD_STARTUP` (default `true`): This option controls whether a potentially existing structure in the database is removed during startup of the backend, provided that prepopulation is enabled. When set to `true` (default), the existing structure is deleted entirely before the new structure specified in `STRUCTURE_TO_PREPOPULATE_VST_ADAPTER` or via the file from `STRUCTURE_FILEPATH_TO_PREPOPULATE_VST_ADAPTER` is inserted. If set to `false`, the existing structure is retained and updated. New elements from the provided JSON structure will be added, and existing elements will be updated. Existing elements not specified in the new JSON structure will remain unchanged. However, any structure provided for an update must be self-contained, i.e. all referenced elements must be included in the structure. Consequently, the structure must contain a root node. To fully replace an existing structure, it must first be deleted, before inserting the new one.

## Technical Information

To process wirings with virtual structure adapter sources and sinks, an additional step in the execution pipeline of the hetida designer was introduced.  
Before the execution input object (WorkflowExecutionInput) is prepared, all virtual structure adapter related wiring information is resolved to the referenced source or sink.
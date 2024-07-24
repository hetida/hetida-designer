# Virtual Structure Adapter
The built-in virtual structure adapter enables the user to create a flexible, abstract hierarchical structures for their data.  
This allows the user to provide names, descriptions and metadata for each element of the hierarchy as seen fit.  
The adapter does not handle the in- and egestion of data itself. The sources and sinks of each defined structure map onto other adapters that actually handle the data in- and egestion.  
The structure can be provided via a JSON assigned to the environment variable `STRUCTURE_TO_PREPOPULATE_VST_ADAPTER`.  
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
    "thing_nodes": [ // Contains thing nodes for your data
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
            "meta_data": {
                "key": "value"
            },
            "passthrough_filters": [ // TODO will probably be changed
                "timestampFrom",
                "timestampTo"
            ],
            "preset_filters": {"key": "value"},  // Values for filters that should not be modifyable be the user
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
            "meta_data": {
                "key": "value"
            },
            "passthrough_filters": [
                "timestampFrom",
                "timestampTo"
            ],
            "preset_filters": {"key": "value"},
            "thing_node_external_ids": [
                "string1", "string2",...
            ]
        }
    ]
}
```

## Configuration
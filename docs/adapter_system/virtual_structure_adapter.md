# Virtual Structure Adapter
The built-in virtual structure adapter enables the user to create flexible, abstract hierarchical structures for their data.  
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

## Configuration

There are several environment variables which can be used to configure the use of the virtual structure adapter.  
* `VST_ADAPTER_ACTIVE` (default `True`): Whether the adapter is active (registered in the designer application)
* `VST_ADAPTER_SERVICE_IN_RUNTIME` (default `True`): Whether the adapter is part of the backend or the runtime
* `PREPOPULATE_VST_ADAPTER_AT_HD_STARTUP` (default `False`): Set to `True` if you wish to provide a structure for the adapter at designer startup
* `COMPLETELY_OVERWRITE_EXISTING_VIRTUAL_STRUCTURE_AT_HD_STARTUP` (default `True`): Whether an existing structure is completely deleted and inserted or (partially) updated in the database. ⚠️ **Disclaimer:** Presently, partial updates of the structure are not yet supported
* `STRUCTURE_TO_PREPOPULATE_VST_ADAPTER` (default `None`): One can assign a JSON defining a structure to this variable

## Technical Information

To process wirings with virtual structure adapter sources and sinks, an additional step in the execution pipeline of the hetida designer was introduced.  
Before the data is actually loaded from or passed to an adapter, all virtual structure adapter related information is removed from the wiring and replaced with information on the referenced source or sink. 
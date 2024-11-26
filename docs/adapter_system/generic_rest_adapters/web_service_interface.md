# Generic Rest adapter web service interface documentation

This page describes the web service endpoints which a generic Rest adapter must implement. If not statet differently all endpoints provide JSON responses (application/JSON) and POST endpoints require JSON bodies.

You may also have a look at an OpenAPI description by running the docker-compose setup as is described in the project Readme and then access the Python Demo Adapter OpenAPI docs at: http://localhost:8092/docs

## Enumerations used in endpoints

The following enumerations are used in the interface:

### Enumeration “datatype“

Possible values

- `int`

- `float`

- `string`

- `boolean`,

- `any`

- `numeric`,

### Enumeration "type"

- `metadata({datatype})`(for example “metadata(string)” or “metadata(float)”)

- `timeseries({datatype})` (for example "timeseries(float)" or "timeseries(int)")

- `dataframe`

- `multitsframe`

## Endpoints for browsing, filtering and wiring construction in UIs

These endpoints enable user interfaces (like the hetida designer test execution dialog) to construct wirings. They provide information on which data sources and sinks are available.

### /info endpoint (GET)

Basic information about the adapter. This endpoint is currently not used by hetida designer itself.

* no query parameters

* Response:

  ```
  {
    "id": STRING,
    "name": STRING,
    "version": STRING
  }
  ```

### /structure endpoint (GET)

This endpoints allows for hierarchical browsing of data sources / data sinks. It returns exactly one level of the hierarchy (used by the hetida designer frontend for lazy loading). The nodes of the hierarchy are called thingNodes.

* query parameters:

  * `parentId`(optional, String): If not provided the response only consists of the root thingNodes and no sources or sinks. If provided the response contains all  sources and sinks which have the `parentId` as `thingNodeId` (sources, sinks)  and all thingNodes which have the `parentId` as parentId. (i.e. everything directly attached to the parentId thingNode)

Response:

```
{
  "id": STRING // id of adapter
  "name": STRING // name of adapter
  "thingNodes": [
    {
      "id": STRING,
      "parentId": STRING,
      "name": STRING,
      "description": STRING
    }
  ],
  "sources": [
    {
      "id": STRING,
      "thingNodeId": STRING,
      "name": STRING,
      "type": TYPE, // enumeration (see above)
      "metadataKey": STRING, // optional/null if type not of form metadata(...)
      "visible": BOOL, // optional, default is true
      "path": STRING, // path to this element that is shown in frontend
      "filters":{  // may be used to request additional filters
        "<key>": {
          "name": STRING,
          "type": FILTERTYPE, // enumeration, possible value: "free_text"
          "required": BOOLEAN
        },
        ...
      }
    }
  ],
  "sinks": [
    {
      "id": STRING,
      "thingNodeId": STRING,
      "name": STRING,
      "metadataKey": STRING, // optional/null if type not of form metadata(...)
      "type": STRING, // enumeration (see above)
      "visible": BOOL,
      "path": STRING, // path to this element that is shown in frontend
      "filters":{  // may be used to request additional filters
        "<key>": {
          "name": STRING,
          "type": FILTERTYPE, // enumeration, possible value: "free_text"
          "required": BOOLEAN
        },
        ...
      }
    }
  ]
}
```

Some details:

- sources and sinks have an optional (default true) `visible` attribute. In future versions hetida designer might not show sources and sinks in the tree with visible being false.

- `filters` may request additional filters. Currently this can either be an empty mapping object (`{}`) or a mapping with filters of type `free_text`. Note that for timeseries type sources, the frontend asks for the time interval automatically, so there is no need to specify this as a filter for now.  If additional filters are required, the user interface provides additional input fields where the value for each filter can be entered.
Via the REST API these filters are used by adding a corresponding key-value pair in the `filters` attribute of the input wiring.
**Note**: If the adapter requests filters it must handle the respective additional query parameters of form filterkey=filtervalue at the respective endpoint.
The value is always sent as a string. If other data types are desired, the value must be parsed accordingly within the adapter. If no value is entered in the user interface, an empty string is sent.

- `path` should be a human readable "breadcrumb"-like path to the source or sink. This attribute is used in the designer frontend for example when filtering.

Note on metadata in hierarchy: Metadata sources (and sinks) can be part of the hierarchy, i.e. as a source or sink leaf in the hierarchy tree. Internally they will then be handled as if they are attached to the thingNode at which they occur. In particular metadata occurring this way will be requested/send from/to the thingNode metadata endpoint (see below):

```
/thingNodes/{thingNodeId}/metadata/{metadataKey}
```

So the adapter implementation must then provide/accept data at that endpoint accordingly.

In general it is of course necessary that the adapter implementation actually provides/accepts data at the appropriate endpoints if it offers sources/sinks for them.

### Sources sinks and thingNodes endpoints

These endpoints provide direct information on sources and sinks and allow to search/filter them. They are used by the user interface to provide fulltext filtering functionality and to store and load wirings in the test execution dialog.

#### /sources/{id} (id is optional) (GET)

parameters:

* filter (String). Only available for /sources/ (without id)!. The fulltext filter search string.

Response of /sources/ (without id):

```
{
"resultCount": INTEGER
"sources":
  [
    {
      "id": STRING,
      "thingNodeId": STRING,
      "name": STRING,
      "type": TYPE,
      "visible": BOOL,
      "path": STRING,
      "filters":{
        "<key>": {
          "name": STRING,
          "type": STRING,
          "required": BOOLEAN
        },
        ...
      }
    }
  ]
}
```

Response of /sources/{id} (with id):

```
{
  "id": STRING,
  "thingNodeId": STRING,
  "name": STRING,
  "type": TYPE,
  "visible": BOOL
  "path": STRING,
  "filters":{
    "<key>": {
      "name": STRING,
      "type": STRING,
      "required": BOOLEAN
    },
    ...
  }
}
```

#### /sinks/{id} (id is optional) (GET)

This is completely analogous to /sources.

parameters:

- filter (String). Only available for /sinks/ (without id)!. The fulltext filter search string.

Response of /sinks/ (without id):

```
{
  "resultCount": INTEGER
  "sinks": [
    {
      "id": STRING,
      "thingNodeId": STRING,
      "name": STRING,
      "visible": BOOL,
      "path": STRING,
      "type": TYPE
      "filters":{
        "<key>": {
          "name": STRING,
          "type": STRING,
          "required": BOOLEAN
        },
        ...
      }
    },
    ...
  ]
}
```

Response of /sinks/{id} (with id):

```
{
  "id": STRING,
  "thingNodeId": STRING,
  "name": STRING,
  "visible": BOOL,
  "path": STRING,
  "type": TYPE
  "filters":{
    "<key>": {
      "name": STRING,
      "type": STRING,
      "required": BOOLEAN
    },
    ...
  }
}
```

#### /thingNodes/{id} (GET)

This only needs to implement the endpoint with id, i.e. retrieval of a single thingNode. And there is no filter here.

Response:

```
{
    "id": STRING,
    "parentId": STRING,
    "name": STRING,
    "description": STRING
}
```

## Metadata Endpoints

On the one side metadata endpoints tell which metadatum is available at every source / sink or thingNode to make it available in the user interface. This is necessary for the frontend to construct wirings which access metadata.

On the other side these endpoints directly return metadata values and are accessed from the runtime-side generic rest adapter implementation to obtain wired metadata or to send them.

**Note:** If you do not need metadata in your adapter, just implement these endpoints to return empty lists as response or NotFound HTTP errors for those endpoints accessing a single metadatum.

#### /sources/{id}/metadata/ (GET)

Get all metadata attached to a specific source. `id` is the source's id.

Response:

```
[
    {
        "key": STRING,
        "value": value // json datatype corresponding to the dataType
                       // field. For "any" dataType this can be either
                       // a Json object or a string containing a Json
                       // object.
        "dataType": DATATYPE // see "datatype" enum description above
        "isSinK": BOOL // optional (default: False). Will be used in
                       // a later version to determine which metadata
                       // is writable
    },
    ...
]
```

This endpoint should always exist and return an empty list if no metadata is provided/accepted by the adapter.

#### /sources/{id}/metadata/{key} (GET, POST)

Get/Post a specific metadatum. `id` is the source's id and `key` is the `metdataKey` of the corresponding source.

Response (GET):

```
{
    "key": STRING,
    "value": value // json datatype corresponding to the dataType
                    // field. For "any" dataType this can be either
                    // a Json object or a string containing a Json
                    // object.
    "dataType": DATATYPE // see "datatype" enum description above
    "isSinK": BOOL // optional (default: False). Will be used in
                    // a later version to determine which metadata
                    // is writable / wirableto workflow outputs
}
```

Payload (POST):

```
{
    "key": STRING,
    "value": value // json datatype corresponding to the dataType
                    // field. When posting this must be the
                    // JSON datatype corresponding to dataType
}
```

#### /sinks/{id}/metadata/ (GET)

Analogous to /sources/{id}/metadata/ (GET) but handles metadata attached to sinks.

#### /sinks/{id}/metadata/{key} (GET, POST)

Analogous to /sources/{id}/metadata/{key} (GET, POST) but handles metadata attached to sinks.

#### /thingNodes/{id}/metadata/ (GET)

Analogous to /sources/{id}/metadata/ (GET) but handles metadata attached to thingNodes. This includes metadata occurring directly in the hierarchy tree (they are considered attached to their parent thingNode).

#### /thingNodes/{id}/metadata/{key} (GET, POST)

Analogous to /sources/{id}/metadata/{key} (GET, POST) but handles metadata attached to thingNodes. This includes metadata occurring directly in the hierarchy tree (they are considered attached to their parent thingNode).

## Data Endpoints

#### /timeseries (GET)

This endpoint streams several timeseries together. This endpoint is only necessary if the adapter provides timeseries data.

Query parameters:

* `id` (can occur multiple times, must occur at least once): The ids of the requested timeseries. These will be the source ids of the timeseries sources as they occur in the structure endpoint.
* `from`: The timestamp from which on datapoints of the source are requested. The frontend will send a Zulu timestamp to nanosecond precision, e.g. "2020-03-11T13:45:18.194000000Z".
* `to`: Analogous to the `from` query parameter, the timestamp until which datapoints of the source are requested.

Response (Line delimited Stream of Json records):

```
{"timeseriesId": STRING, "timestamp": "2020-03-11T13:45:18.194000000Z", "value": 42.3}
{"timeseriesId": STRING, "timestamp": "2020-03-11T14:45:18.194000000Z", "value": 41.7}
{"timeseriesId": STRING, "timestamp": "2020-03-11T15:45:18.194000000Z", "value": 15.89922333}
```

The `timestamp` entries have to be ISO-8601 timestamps and should always have UTC timeszone and nanosecond resolution.

`timeseriesId` is always one of the ids provided by the id query parameter.

Type of value must be the datatype of the timeseries source, i.e. if the timeseries source with that id has type `timeseries(int)` the value of a corresponding record must be a Json integer.

##### Attaching metadata to each timeseries
Additionally, metadata in the form of (arbitrarily nested) JSON mappings can be provided that is then attached to the Pandas Series objects' `attrs` attribute in the designer runtime during component/workflow execution. See [metadata attrs documentation](../../metadata_attrs.md) for details and the conventions for fields that an adapter should provide. We strongly recommend to send at least the metadata fields described there!

For this the response is allowed to send a header `Data-Attributes` which must contain a base64 encoded UTF8-encoded JSON String representing a mapping from timeseries ids to their metadata, e.g.:

```json
{
  "id_1": {
    "ref_interval_start_timestamp": "2020-03-11T13:00:00.000000000Z",
    "ref_interval_end_timestamp": "2020-03-11T16:00:00.000000000Z",
    "ref_interval_type": "closed"
  },
  "id_2": {
    "ref_interval_start_timestamp": "2020-03-11T13:00:00.000000000Z",
    "ref_interval_end_timestamp": "2020-03-11T16:00:00.000000000Z",
    "ref_interval_type": "closed",
    "anomalies": ["2020-03-11T14:45:00.000000000Z", "2020-03-11T14:48:00.000000000Z"]
  }
}
```

Note: The designer runtime will default to an empty dictionary if no metadata is provided for a timeseries.

#### /timeseries (POST)

This endpoint accepts a single timeseries per POST request.

Query parameters:

* `timeseriesId`: required, must occur exactly once. This is a sink id of a timeseries sink occurring in the structure endpoint.

Payload (List of timeseries records):

```
[
    {"timestamp": "2020-03-11T13:45:18.194000000Z", "value": 42.3},
    {"timestamp": "2020-03-11T14:45:18.194000000Z", "value": 41.7},
    {"timestamp": "2020-03-11T15:45:18.194000000Z", "value": 15.89922333}
]
```

The same rules as described in the corresponding GET apply to `timestamp` and `value`

##### Retrieving attached timeseries metadata
Metadata stored in the Pandas Series `attrs` attribute will be sent by the designer runtime in a header `Data-Attributes` as a base64-encoded UTF8-encoded JSON string.

See [metadata attrs documentation](../../metadata_attrs.md) for details and conventions.

It is up to your adapter implementation what you do with that metadata.

#### /dataframe (GET)

Query parameters:

* `id`: required exactly once: This is a source id of a dataframe source occurring in the structure endpoint

Response (Line delimited Stream of Json records):

```
{"columnA": "UK", "timestamp": "2020-03-11T13:45:18.194000000Z", "column_B": 42.3}
{"columnA": "UK", "timestamp": "2020-03-11T14:45:18.194000000Z", "column_B": 41.3}
{"columnA": "Germany", "timestamp": "2020-03-11T15:45:18.194000000Z", "column_B": 19.5}
```

This response can have arbitrary entries in the record which then correspond to columns of a table of data. Coming from a table of data imposes restrictions which should be clear, like every key should occur in every record.

There is a special convention on "timestamp" columns: If a timestamp column exists the runtime will try to parse this column as datetimes and if this is successful will set the index of the Pandas DataFrame to this column and sort by it. If that does not work the index of the resulting Pandas DataFrame will be the default RangeIndex. In every case the column timestamp will also be available as column in the resulting Pandas DataFrame.

##### Attaching metadata to the dataframe
Additionally, [metadata](../../metadata_attrs.md) in the form of an (arbitrarily nested) JSON mapping can be provided that is then attached to the Pandas DataFrame objects' `attrs` attribute in the designer runtime during component/workflow execution.

For this the response is allowed to send a header `Data-Attributes` which must contain a base64 encoded UTF8-encoded JSON String representing the metadata, e.g.:

```json
{
  "column_units": {
    "main_engine_pw": "W",
    "pump_throughput": "l/s",
  },
  "plant_name": "north-west 3"
}
```

#### /dataframe (POST)

Query parameters:

* `id`: required exactly once: This is a sink id of a dataframe sink occurring in the structure endpoint

Payload:

```
[
  {"columnA": "UK", "timestamp": "2020-03-11T13:45:18.194000000Z", "column_B": 42.3},
  {"columnA": "UK", "timestamp": "2020-03-11T14:45:18.194000000Z", "column_B": 41.3},
  {"columnA": "Germany", "timestamp": "2020-03-11T15:45:18.194000000Z", "column_B": 19.5}
]
```

Same rules as in the corresponding GET endpoint apply here, only timestamp handling is different. The runtime will not try to convert a DateTimeIndex of the Pandas DataFrame to send into a timestamp column. Actually when Posting results, the index will be completely ignored. If index data should be send it should be converted into a column as part of the workflow.

##### Retrieving attached timeseries metadata
Again, metadata stored in the Pandas DataFrame `attrs` attribute will be sent by the designer runtime in a header `Data-Attributes` as a base64-encoded UTF8-encoded JSON string.

See [metadata attrs documentation](../../metadata_attrs.md) for details and conventions.

It is up to your adapter implementation what you do with that metadata.

#### /multitsframe (GET)

Query parameters:

* `id`: required exactly once: This is a source id of a multitsframe source occurring in the structure endpoint
* `from`: The timestamp from which on datapoints of the source are requested. The frontend will send a Zulu timestamp to nanosecond precision, e.g. "2020-03-11T13:45:18.194000000Z".
* `to`: Analogous to the `from` query parameter, the timestamp until which datapoints of the source are requested.

Response (Line delimited Stream of Json records):

```
{"metric": "Milling Influx Temperature", "timestamp": "2020-03-11T13:45:18.194000000Z", "value": 42.3}
{"metric": "Milling Outfeed Temperature", "timestamp": "2020-03-11T14:45:18.237000000Z", "value": 41.7}
{"metric": "Pickling Influx Temperature", "timestamp": "2020-03-11T15:45:18.081000000Z", "value": 18.4}
{"metric": "Pickling Outfeed Temperature", "timestamp": "2020-03-11T15:45:18.153000000Z", "value": 18.3}
```

This response will always have the entries `metric`, `timestamp` and `value`. Neither `metric` nor `timestamp` may be `null`. The `timestamp` entries have to be ISO-8601 timestamps and should always have UTC timeszone and nanosecond resolution.


##### Attaching metadata to the multitsframe
Additionally, metadata in the form of an (arbitrarily nested) JSON mapping can be provided that is then attached to the Pandas DataFrame objects' `attrs` attribute in the designer runtime during component/workflow execution. See [metadata attrs documentation](../../metadata_attrs.md) for details and the conventions for fields that an adapter should provide. We strongly recommend to send at least the metadata fields described there!

For this the response is allowed to send a header `Data-Attributes` which must contain a base64 encoded UTF8-encoded JSON String representing the metadata, e.g.:

```json
{
  "ref_interval_start_timestamp": "2020-03-11T13:00:00.000000000Z",
  "ref_interval_end_timestamp": "2020-03-11T16:00:00.000000000Z",
  "ref_interval_type": "closed",
  "ref_metrics": [
      "Milling Influx Temperature",
      "Milling Outfeed Temperature",
      "Pickling Influx Temperature",
      "Pickling Outfeed Temperature"
    ],
  "column_units": {
    "Milling Influx Temperature": "C",
    "Milling Outfeed Temperature": "C",
    "Pickling Influx Temperature": "C",
    "Pickling Outfeed Temperature": "C",
  },
}
```

#### /multitsframe (POST)

Query parameters:

* `id`: required exactly once: This is a sink id of a multitsframe sink occurring in the structure endpoint

Payload:

```
[
  {"metric": "Milling Influx Temperature", "timestamp": "2020-03-11T13:45:18.194000000Z", "value": 42.3}
  {"metric": "Milling Outfeed Temperature", "timestamp": "2020-03-11T14:45:18.237000000Z", "value": 41.7}
  {"metric": "Pickling Influx Temperature", "timestamp": "2020-03-11T15:45:18.081000000Z", "value": 18.4}
  {"metric": "Pickling Outfeed Temperature", "timestamp": "2020-03-11T15:45:18.153000000Z", "value": 18.3}
]
```

Same rules as in the corresponding GET endpoint apply here, only timestamp handling is different.

##### Retrieving attached multitsframe metadata
Analogous to the corresponding GET endpoint, metadata stored in the underlying Pandas DataFrame `attrs` attribute will be sent by the designer runtime in a header `Data-Attributes` as a base64-encoded UTF8-encoded JSON string.

See [metadata attrs documentation](../../metadata_attrs.md) for details and conventions.

It is up to your adapter implementation what you do with that metadata.

## A minimal Generic Rest adapter

Lets imagine you want to make some tables from a SQL database available as sources in hetida designer as DataFrames. There is no metadata around. And you don't want to send result data anywhere (You take result directly from the workflow execution response, i.e. use direct provisioning (Only Output) for accessing result)

In this case you have to implement the following endpoints:

* /info (GET) endpoint

* /structure (GET) endpoint where the tables occur as sources

* all /sources/* (GET) endpoints responding with appropriate sources for your tables

* the /sinks (GET) endpoint returning an empty list.

* /thingNodes/{id} (GET) endpoint where the thingNodes you offer in /structure occur.

* All metadata (GET) endpoints of the form /source|sink|thingNode/metadata/ (those that return a list, without key) responding with empty lists.

* The /dataframe (GET) endpoint delivering your tables

In particular you do not need:

* the /sources|sinks|thingNodes/metadata/{key} endpoints

* the /timeseries endpoints

* the /multitsframe endpoints

* /dataframe (POST) endpoint

## Registering your generic Rest adapter

see [adapter registration documentation](../adapter_registration.md)!

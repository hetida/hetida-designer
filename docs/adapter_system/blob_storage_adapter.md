# Blob Storage Adapter

The built-in blob storage adapter allows to read and write objects in buckets of an S3 compatible blob storage.

It allows to store and reload e.g. trained machine learning models.

## Configuration

This section explains how to make blob storage available via the blob storage adapter for the default docker-compose setup.

### Mounting the adapter hierarchy configuration

The S3 data model is flat, consisting only of buckets in which objects can be stored.
There is no hierarchy of sub-buckets of sub-folders.
The blob storage adapter can infer a more complex hierarchical structure by using delimiters.
Hyphens `-` are used as delimiters in bucket names, and slashes `/` are used as delimiters within object keys to mimic paths to files in nested folders.
Some tools for S3 blob storages can infer hierarchy in the user interface from object keys with such delimiters.

The blob storage adapter offers resources from the blob storage in a hierarchical structure.
This hierarchy is defined in a file named `blob_storage_adapter_hierarchy.json` which must be available to the runtime service and is loaded at startup.
For example, a demo hierarchy can be mounted in the docker-compose setup as follows:

```yaml
  hetida-designer-runtime:
    ...
    volumes:
      ...
      - ./runtime/demodata/blob_storage_adapter_hierarchy.json:/mnt/blob_storage_adapter_hierarchy.json
```

You just need to replace the path `./runtime/demodata/blob_storage_adapter_hierarchy.json` with a path to the file on your machine.

This [file](../../runtime/demodata/blob_storage_adapter_hierarchy.json) contains an example of such a json starting with:

```json
{
    "structure": [
        {
            "name": "PlantA",
            "description": "Plant A",
            "substructure": [
                {
                    "name": "PicklingUnit",
                    "description": "Plant A Pickling Unit",
                    "below_structure_defines_object_key": true,
                    "substructure": [
                        {
                            "name": "Influx",
                            "description": "Plant A Pickling Unit Influx",
                            "substructure": [
                                {
                                    "name": "Anomalies",
                                    "description": "Plant A Pickling Unit Influx Anomalies"
                                }, //...
                            ]
                        }
                    ]
                }, //...
            ]
        }, //...
    ]
}
```

The names for the hierarchy nodes should consist only of alphanumeric upper and lower case letters without spaces, because they are interpreted as parts of the bucket names and object keys. Since bucket names cannot contain uppercase letters, the hierarchy node names are converted to lowercase when the corresponding bucket names are generated. When naming hierarchy nodes, note that bucket names must consist of a minimum of 3 and a maximum of 63 characters.

The `below_structure_defines_object_key` attribute is `false` by default.
If it is not set, only the names of the hierarchy end nodes are used as prefix of the object key, which is supplemented by the respective creation time stamp, and the bucket name is composed of the names of all higher hierarchy nodes.
If this attribute is set to "true" for a hierarchy node, the names of all lower hierarchy nodes are used as prefix of the object key.

The buckets defined by the adapter structure must already be present in the blob storage. For the example adapter hierarchy these would be buckets with the following names:
* `planta-picklingunit`
* `planta-millingunit`
* `plantb`

A generic sink is generated for each end node of the hierarchy. Using it will always create a new object, the creation timestamp is appended to the object key. Vice-versa object keys are expected to have such a suffix to be available as sources via the adapter.

For the example adapter hierarchy e.g. the following objects would be available as source:
* in bucket `planta-picklingunit` an object with key `Influx/Anomalies_2023-02-14T12:19:38+00:00`
* in bucket `plantb` an object with key `PicklingUnit/Influx/Anomalies_2023-02-14T12:19:38+00:00`


### Configuring the runtime

The blob storage adapter is configured by the following environment variables:

* BLOB_STORAGE_ADAPTER_HIERARCHY_LOCATION
* BLOB_STORAGE_ACCESS_DURATION
* BLOB_STORAGE_ENDPOINT_URL
* BLOB_STORAGE_REGION_NAME
* BLOB_STORAGE_VERSION
* BLOB_STORAGE_ROLE_ARN

The environment variable  `BLOB_STORAGE_ACCESS_DURATION` is used to set the [request parameter](https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRoleWithWebIdentity.html#API_AssumeRoleWithWebIdentity_RequestParameters) `DurationSeconds` in the authentication towards the blob storage.
It sets the duration of the role session in seconds and must be in the range between 900 (15 min) and the maximum session duration setting for the role.
Its default value is 3600 (1 hour).
The environment variable `BLOB_STORAGE_REGION_NAME` should be set to the region name matching your blob storage setup.
Its default value is "eu-central-1".
The environment variable `BLOB_STORAGE_VERSION` should be set to the STS API version. The default value is "2011-06-15".
The environment variable `BLOB_STORAGE_ROLE_ARN` is used to set the Amazon Resource Name (ARN) of the role that the hetida designer should be assuming. Its default value is an empty string.

An example using a minio instance as blob storage provider:

```yaml
  hetida-designer-runtime:
    ...
    environment:
      BLOB_STORAGE_ADAPTER_HIERARCHY_LOCATION: /mnt/blob_storage_adapter_hierarchy.json
      BLOB_STORAGE_ENDPOINT_URL: http://minio:9000
      ...
```

### Configuring the backend

The blob storage adapter needs to be [registered](./adapter_registration.md) in the designer backend. The blob storage adapter's part of the environment variable `HETIDA_DESIGNER_ADAPTERS` could for example look like this:
```
blob-storage-adapter|Blob-Storage-Adapter|http://localhost:8090/adapters/blob|http://hetida-designer-runtime:8090/adapters/blob
```

## Usage
All sources and sinks of the blob storage adapter are of type `Any`, thus only inputs and outputs of type `Any` can be wired to the blob storage adapter.
The `dump` and `load` methods of the Python package `pickle` are used to serialize and deserialize these inputs and outputs.

### Basic Usage

The workflows "Get ExampleClass Object Attributes" and "Create ExampleClass Object" provide a minimal example of how objects with a self defined class can be stored and loaded.

Selecting "Blob Storage Adapter" for an input in the Execution dialog sources should be available for all objects for which bucket name and object key match the adapter hierarchy:

<img src="./assets/blob_storage_adapter_assign_source.png" height="630" width=530 data-align="center">

Similarly a sink should be available for each end node in the hierarchy via selecting "Blob Storage Adapter" for an output in the Execution dialog:

<img src="./assets/blob_storage_adapter_assign_sink.png" height="630" width=530 data-align="center">
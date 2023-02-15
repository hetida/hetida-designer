# Blob Storage Adapter

The built-in blob storage adapter allows to read and write objects in buckets of an S3 compatible blob storage.

It allows to store and reload e.g. trained machine learning models.

## Configuration

This section explains how to make blob storage available via the blob storage adapter for the default docker-compose setup.

### Mounting the adapter hierarchy configuration

The S3 data model is flat, consisting only of buckets in which objects can be stored. There is no hierarchy of sub-buckets of sub-folders. The blob storage adapter can infer a more complex hierarchical structure to increase  by using delimiters. Hyphens `-` are used as delimiters in bucket names and slashes `/` are used as delimiters within object keys to mimic the paths to files in nested folders. Some tools for S3 blob storages can infer hierarchy in the user interface from object keys with such delimiters.

The blob storage adapter offers resources from blob storage in a hierarchical structure. This hierarchy is defined in a file named `blob_storage_adapter_hierarchy.json` which needs to be available to the runtime service and is loaded at startup. E.g. a demo hierarchy can be mounted in the docker-compose setup as follows:
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
                    "end_of_bucket": true,
                    "substructure": [
                        {
                            "name": "InfluxAnomalies",
                            "description": "Plant A Pickling Unit Influx Anomalies"
                        }, //...
                    ]
                }, //...
            ]
        }, //...
    ]
}
```

The names for the categories should consist only of alphanumeric upper and lower case letters without spaces, because they are interpreted as parts of the bucket names and object keys. Since bucket names cannot contain uppercase letters, the category names are converted to lowercase when the corresponding bucket names are generated. When naming categories, note that bucket names must consist of a minimum of 3 and a maximum of 63 characters.

The buckets defined by the adapter structure must already be present in the blob storage. For the example adapter hierarchy these would be buckets with the following names:
* `planta-picklingunit`
* `planta-millingunit`
* `plantb`

A generic sink is generated for each end node of the hierarchy. Using it will always create a new object, the creation timestamp is appended to the object key. Vice-versa object keys are expected to have such a suffix to be available as sources via the adapter.

For the example adapter hierarchy e.g. the following objects would be available as source:
* in bucket `planta-picklingunit` an object with key `InfluxAnomalies_2023-02-14T12:19:38+00:00`
* in bucket `plantb` an object with key `PicklingUnit/InfluxAnomalies_2023-02-14T12:19:38+00:00`


### Configuring the runtime

The blob storage adapter is configured by the following environment variables:

* BLOB_STORAGE_ADAPTER_HIERARCHY_LOCATION
* BLOB_STORAGE_ACCESS_DURATION
* BLOB_STORAGE_ENDPOINT_URL
* BLOB_STORAGE_REGION_NAME

The `BLOB_STORAGE_REGION_NAME` should be one of the [AWS regional endpoint codes](https://docs.aws.amazon.com/de_de/general/latest/gr/rande.html#regional-endpoints).
The `BLOB_STORAGE_ACCESS_DURATION` should provide the access duration of the storage in seconds.

An example using a minio instance as blob storage provider:

```yaml
  hetida-designer-runtime:
    ...
    environment:
      BLOB_STORAGE_ADAPTER_HIERARCHY_LOCATION: /mnt/blob_storage_adapter_hierarchy.json
      BLOB_STORAGE_ACCESS_DURATION: 3600
      BLOB_STORAGE_ENDPOINT_URL: http://minio:9000
      BLOB_STORAGE_REGION_NAME: eu-central-1
      ...
```

### Configuring the backend

The blob storage adapter needs to be [registered](./adapter_registration.md) in the designer backend. The blob storage adapter's part of the environment variable `HETIDA_DESIGNER_ADAPTERS` could for example look like this:
```
blob-storage-adapter|Blob-Storage-Adapter|http://localhost:8090/adapters/blob|http://hetida-designer-runtime:8090/adapters/blob
```

## Usage

### Basic Usage

After having made adaptions to the configuration described above you need to (re)start with

```bash
docker-compose stop
docker-compose up
```

Now all all objects for which bucket name and object key match the adapter hierarchy should be available as sources via selecting "Blob Storage Adapter" for an input in the Execution dialog:
<img src="./assets/blob_storage_adapter_selected.png" height="100" width=450>
<img src="./assets/blob_storage_adapter_assign_source.png" height="780" width=700>

Similarly a sink should be available for each end node in the hierarchy via selecting "Blob Storage Adapter" for an output in the Execution dialog:
<img src="./assets/blob_storage_adapter_assign_sink.png" height="780" width=700>
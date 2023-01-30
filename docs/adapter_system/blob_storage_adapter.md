# Blob Storage Adapter

The built-in blob storage adapter allows to read and write objects in buckets of an S3 compatible blob storage.

It allows to store and reload e.g. trained machine learning models.

## Configuration

This section explains how to make blob storage available for the blob storage adapter via the default docker-compose setup.

### Mounting the adapter hierarchy configuration

The blob storage adapter is built into the runtime and needs to know which hierarchy of sinks and sources to offer in the adapter dialog. This is configured via a file named `blob_storage_adapter_hierarchy.json` which needs to be mounted into the runtime service by adding the line in your docker compose file:

```yaml
  hetida-designer-runtime:
    ...
    volumes:
      ...
      - ./runtime/demodata/blob_storage_adapter_hierarchy.json:/mnt/blob_storage_adapter_hierarchy.json
```

You just need to replace the path `./runtime/demodata/blob_storage_adapter_hierarchy.json` with a path to the file on your machine.

This file should contain a json file with the attribute `structure`. The value of this attribute must contain a list of categories each with attributes `name`, `description`, and `substructure`. The latter must either itself contain a list of nested categories or be omitted. The nested categories correspond to a tree data structure. The optional boolean attribute `end_of_bucket` must be set to `True` for exactly one category for each branch of this tree, but not for the deepest category. The json file is read only once, thus when changes to the structure are made in the json file, the Docker container of the blob storage adapter must be restarted to implement these changes.

The S3 data model is flat, consisting only of buckets in which objects can be stored. There is no hierarchy of sub-buckets of sub-folders. Therefore, the hierarchy of the adapter is transferred to the bucket names and object keys by using delimiters. Hyphens `-` are used as delimiters in bucket names and slashes `/` are used as delimiters within object keys to mimic the paths to files in nested folders. Some tools for S3 blob storages can infer hierarchy in the user interface from object keys with such delimiters.

The names for the categories should consist only of alphanumeric upper and lower case letters without spaces, because they are interpreted as parts of the bucket names and object keys. Since bucket names cannot contain uppercase letters, the category names are converted to lowercase when the corresponding bucket names are generated. When naming categories, note that bucket names must consist of a minimum of 3 and a maximum of 63 characters.

Only those objects whose bucket name and object key match the hierarchy are available in the adapter. A sink is generated for each end node of the hierarchy, to which data can then be sent to be stored in the blob storage. Sending data twice over the same sink does not overwrite the contents of an object; instead, the timestamp (in second-by-second isoformat) is appended to the object key as a suffix, with an underscore `_` as a delimiter. Accordingly, object keys are expected to have such a suffix, otherwise no corresponding sink is added to the adapter.

### Configuring the runtime

The information required to access the blob storage is expected to be provided by the following environment variables:

* BLOB_STORAGE_ADAPTER_HIERARCHY_LOCATION
* BLOB_STORAGE_ACCESS_DURATION
* BLOB_STORAGE_ENDPOINT_URL
* BLOB_STORAGE_REGION_NAME

The `BLOB_STORAGE_REGION_NAME` should be one of the [AWS regional endpoint codes](https://docs.aws.amazon.com/de_de/general/latest/gr/rande.html#regional-endpoints).
The `BLOB_STORAGE_ACCESS_DURATION` should provide the access duration of the storage in seconds.

These can be provided in the docker compose file as following:

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

Additionally the blob storage adapter itself needs to be [registered](./adapter_registration.md) in the environment variable `HETIDA_DESIGNER_ADAPTERS` in the designer backend. The blob storage adapter's part of the environment variable could for example like this:

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

Similarly a sink should be available for each end node in the hierarchy via selecting "Blob Storage Adapter" for an output in the Execution dialog:
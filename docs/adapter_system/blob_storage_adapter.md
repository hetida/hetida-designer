# Blob Storage Adapter

The built-in blob storage adapter allows to read and write objects in buckets of an S3 compatible blob storage.

It allows to store and reload e.g. trained machine learning models.

## Configuration

This section explains how to make blob storage available for the blob storage adapter via the default docker-compose setup.

### Mounting the adapter hierarchy configuration

The blob storage adapter is built into the runtime and needs to know which hierarchy of sinks and sources it should offer in the adapter dialog. This is configured via a file named `blob_storage_adapter_hierarchy.json` which needs to be mounted into the runtime service, by adding the line in your docker compose file:

```yaml
  hetida-designer-runtime:
    ...
    volumes:
      ...
      - ./runtime/demodata/blob_storage_adapter_hierarchy.json:/mnt/blob_storage_adapter_hierarchy.json
```

You just need to replace the path `./runtime/demodata/blob_storage_adapter_hierarchy.json` with a path to the file on your machine.

This file should contain a json with the two attributes `object_key_depth` and `structure`. The former being a positive integer saying how many hierarchy levels should be considered part of the object key. The latter contains a list of categories each with attributes `name`, `description`, and `substructure`, which can itself contain a list of nested categories or be omitted.

The S3 data model is flat, it consists only of buckets in which objects can be stored. There is no hierarchy of subbuckets of subfolders. Thus, the hierarchy of the adapter is transferred to the bucket names and object keys by using delimiters. Hyphens `-` are used as delimiters in bucket names and slashes `/` are used as delimiters within object keys, mimicking the paths to files in nested folders. Some tools for S3 blob storages can infer hierarchy in the UI from object keys with such delimiters.

The names for the categories should only consist of upper- and lower-case alphanumeric characters with no spaces since they will be interpreted as parts of bucket names and object keys. Since bucket names may not contain capital letters the category names will be transformed in small letters when generating the corresponding bucket names. Keep in mind, that bucket names must consist of minimal 3 charcaters and maximal 63 characters when naming categories.

Only those buckets and objects for which bucket name and object key match the hierarchy will be available in the adapter. A sink will be generated for each end node of the hierarchy to which then data can be send to be stored in the blob storage. Sending data twice via the same sink will not result in overwriting the content of an object, instead the timestamp (in isoformat to the second) will be added as a suffix to the object key with an underscore `_` as delimiter. Accordingly the keys of objects are expected to have such a suffix.

### Configuring the runtime

The information required to access the blob storage is expected to be provided by the following environment variables:

* BLOB_STORAGE_ADAPTER_HIERARCHY_LOCATION
* BLOB_STORAGE_ACCOUNT_ID
* BLOB_STORAGE_RESOURCE_ID
* BLOB_STORAGE_ENDPOINT_URL
* BLOB_STORAGE_REGION_NAME

The `REGION_NAME` should be one of the [AWS regional endpoint codes](https://docs.aws.amazon.com/de_de/general/latest/gr/rande.html#regional-endpoints).

These can be provided in the docker compose file as following:

```yaml
  hetida-designer-runtime:
    ...
    environment:
      BLOB_STORAGE_ADAPTER_HIERARCHY_LOCATION:
      BLOB_STORAGE_ENDPOINT_URL: http://localhost:9000
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
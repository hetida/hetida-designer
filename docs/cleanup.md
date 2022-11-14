# Clean Up the Components and Transformations in the Database

There are cleanup options of varying scope:

1. Deprecate old transformation revisions

2. Delete draft transformation revisions

3. Delete unused deprecated transformation revisions

4. Purge: Delete all transformation revisions and refill with base transformation revisions

The first two actions can easily be performed for individual transformation revisions via the user interface, doing so regularly is recommended. Apart from that, there are also functions for all four actions that automatically apply them to all matching transformation revisions.

## 1. Deprecate Old Transformation Revisions

In this case a transformation revision is considered "old" if it is released and there is another  released transformation revision in the same revision group, which has a later release timestamp.

After inserting the hetida designer backend API URL of your instance you can use the following command to deprecate all these old transformation revisions:

```shell
docker run --rm \
  -e "HETIDA_DESIGNER_BACKEND_API_URL=<...>" \
  --name htdruntime_export \
  --entrypoint python \
  hetida/designer-runtime -c 'from hetdesrun.exportimport.purge import deprecate_all_but_latest_per_group; deprecate_all_but_latest_per_group();'
```

## 2. Delete Draft Transformation Revisions

To delete all draft transformation revisions just execute the following command:

```shell
docker run --rm \
  -e "HETIDA_DESIGNER_BACKEND_API_URL=<...>" \
  --name htdruntime_export \
  --entrypoint python \
  hetida/designer-runtime -c 'from hetdesrun.exportimport.purge import delete_drafts; delete_drafts();'
```

## 3. Delete Unused Deprecated Transformation Revisions

In this case "unused" deprecated transformation revisions are those that are either not used in workflows or only in workflows that are deprecated, which themselves will be deleted by this command.

```shell
docker run --rm \
  -e "HETIDA_DESIGNER_BACKEND_API_URL=<...>" \
  --name htdruntime_export \
  --entrypoint python \
  hetida/designer-runtime -c 'from hetdesrun.exportimport.purge import delete_unused_deprecated; delete_unused_deprecated();'
```

## 4. Purge 

To delete all transformation revisions and deploy the specified version of base components and sample workflows from the hetida designer git repository in the version correspond execute the following command. The version must be at least 8.0.2, earlier versions do not contain this feature.

```shell
docker run --rm \
  -e "HETIDA_DESIGNER_BACKEND_API_URL=<...>" \
  --name htdruntime_export \
  --entrypoint python \
  hetida/designer-runtime:<version> -c 'from hetdesrun.exportimport.purge import delete_all_and_refill; delete_all_and_refill();'
```

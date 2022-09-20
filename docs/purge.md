# Purge your Database: Clean Up the Components and Transformations

There are cleanup options of varying scope:

1. Deprecate old transformation revisions

2. Delete draft transformation revisions

3. Delete unused deprecated transformation revisions

4. Delete all transformation revisions and restart

The first two actions can easily be performed for individual transformation revisions via the user interface, doing so regularly is recommended. Apart from that, there are also functions for all four actions that automatically apply them to all matching transformation revisions.

## Deprecate Old Transformation Revisions

In this case a transformation revision is considered "old" if it is released and there is another  released transformation revision in the same revision group, which has a later release timestamp.

After inserting the hetida designer backend API URL of your instance you can use the following command to deprecate all these old transformation revisions:

```shell
docker run --rm \
  -e "HETIDA_DESIGNER_BACKEND_API_URL=<...>" \
  --name htdruntime_export \
  --mount type=bind,source="$(pwd)",target=/mnt/obj_repo \
  --entrypoint python \
  hetida/designer-runtime -c 'from hetdesrun.exportimport.purge deprecate_all_but_latest_per_group; deprecate_all_but_latest_per_group();'
```

## Delete Draft Transformation Revisions

To delete all draft transformation revisions just execute the following command:

```shell
docker run --rm \
  -e "HETIDA_DESIGNER_BACKEND_API_URL=<...>" \
  --name htdruntime_export \
  --mount type=bind,source="$(pwd)",target=/mnt/obj_repo \
  --entrypoint python \
  hetida/designer-runtime -c 'from hetdesrun.exportimport.purge delete_drafts; delete_drafts();'
```

## Delete Unused Deprecated Transformation Revisions

In this case "unused" deprecated transformation revisions are those that are either not used in workflows or only in workflows that are deprecated.

```shell
docker run --rm \
  -e "HETIDA_DESIGNER_BACKEND_API_URL=<...>" \
  --name htdruntime_export \
  --mount type=bind,source="$(pwd)",target=/mnt/obj_repo \
  --entrypoint python \
  hetida/designer-runtime -c 'from hetdesrun.exportimport.purge delete_unused_deprecated; delete_unused_deprecated();'
```

## Delete All Transformation Revisions and Restart

To delete all transformation revisions and deploy the latest version of base components and sample workflows from the hetida designer git repository execute the following command.

```shell
docker run --rm \
  -e "HETIDA_DESIGNER_BACKEND_API_URL=<...>" \
  --name htdruntime_export \
  --mount type=bind,source="$(pwd)",target=/mnt/obj_repo \
  --entrypoint python \
  hetida/designer-runtime -c 'from hetdesrun.exportimport.purge delete_all_restart; delete_all_restart();'
```

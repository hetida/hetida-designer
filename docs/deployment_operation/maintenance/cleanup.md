# Clean Up the Components and Transformations in the Database

There are cleanup options of varying scope:

1. Restore Release Wirings

2. Deprecate old transformation revisions

3. Delete draft transformation revisions

4. Delete unused deprecated transformation revisions

5. Purge: Delete all transformation revisions and refill with base transformation revisions

The first two actions can easily be performed for individual transformation revisions via the user interface, doing so regularly is recommended. Apart from that, there are also functions for all four actions that automatically apply them to all matching transformation revisions.

!!! note
All commands listed below assume an external hetida designer installation, i.e. not the local docker compose setup. For the former you may need authentication configuration according to your setup. For the later you may need to add `--network hetida-designer-network ` and set `http://hetida-designer-backend:8090/api/` as `HETIDA_DESIGNER_BACKEND_API_URL`.

Below we show how to execute these cleanup actions by running them from a docker container. Note that they also can be invoked through [other means](../maintenance/)

## 1. Restore Release Wirings

This resets the current test wiring to the release wiring (i.e. the test wiring stored at release time).

After inserting the hetida designer backend API URL of your instance you can use the following command to deprecate all these old transformation revisions:

```shell
docker run --rm \
  -e "HETIDA_DESIGNER_BACKEND_API_URL=<...>" \
  --name htdruntime_export \
  --entrypoint python \
  hetida/designer-runtime -c 'from hetdesrun.exportimport.purge import reset_test_wiring_to_release_wiring; reset_test_wiring_to_release_wiring();'
```

## 2. Deprecate Old Transformation Revisions

In this case a transformation revision is considered "old" if it is released and there is another released transformation revision in the same revision group, which has a later release timestamp.

After inserting the hetida designer backend API URL of your instance you can use the following command to deprecate all these old transformation revisions:

```shell
docker run --rm \
  -e "HETIDA_DESIGNER_BACKEND_API_URL=<...>" \
  --name htdruntime_export \
  --entrypoint python \
  hetida/designer-runtime -c 'from hetdesrun.exportimport.purge import deprecate_all_but_latest_per_group; deprecate_all_but_latest_per_group();'
```

## 3. Delete Draft Transformation Revisions

To delete all draft transformation revisions just execute the following command:

```shell
docker run --rm \
  -e "HETIDA_DESIGNER_BACKEND_API_URL=<...>" \
  --name htdruntime_export \
  --entrypoint python \
  hetida/designer-runtime -c 'from hetdesrun.exportimport.purge import delete_drafts; delete_drafts();'
```

## 4. Delete Unused Deprecated Transformation Revisions

In this case "unused" deprecated transformation revisions are those that are either not used in workflows or only in workflows that are deprecated, which themselves will be deleted by this command.

```shell
docker run --rm \
  -e "HETIDA_DESIGNER_BACKEND_API_URL=<...>" \
  --name htdruntime_export \
  --entrypoint python \
  hetida/designer-runtime -c 'from hetdesrun.exportimport.purge import delete_unused_deprecated; delete_unused_deprecated();'
```

## 5. Purge

To delete all transformation revisions and deploy the versions of base components and example workflows included in the executing image's code run:

```shell
docker run --rm \
  -e "HETIDA_DESIGNER_BACKEND_API_URL=<...>" \
  --name htdruntime_export \
  --entrypoint python \
  hetida/designer-runtime -c 'from hetdesrun.exportimport.purge import delete_all_and_refill; delete_all_and_refill();'
```

# Maintenance

Typical maintenance and devops task around a hetida designer installation, possibly over multiple environments like dev / test / prod include

* Backup / Restore
* Export / Import (e.g. between instances)
* Automatic deployment of base components / workflows
* Autoimport of sets of components / workflows
* Updating base components / workflows or other specific sets of transformation revisions
* Cleanup operations, like 
  * resetting test wirings to release wirings (i.e. wiring during release)
  * deleting drafts
  * deprecating "old" revisions
  * delete unused deprecated revisions
  * purging a dev / test system

This page gives an overview over these tasks and provides recommendations and links to documentation and tooling that may help you manage your hetida designer installations.

## How to invoke maintenance actions

### via running docker images
The documentation typically shows how to invoke actions by running docker containers. See for example
* [Import / Export](import_export.md) documentation.
* [Cleanup](cleanup.md) documentation.

### via backend maintenance endpoints
The backend provides maintenance endpoints under /api/maintenance if a `HD_MAINTENANCE_SECRET` environment variable is set to a non-zero-length string. This secret has to be provided on each request to allow maintenance operations to be triggered this way.

See the openapi documentation of the backend's /api/maintenance/* endpoints (when active) for details on available operations and options.

### via hdctl Bash Tool
hetida designer comes with a small bash tool called [hdctl](../hdctl), that can invoke export / import and maintenance actions by making requests to backend endpoints.

See the [script file](../hdctl) for installation instructions and run `./hdctl usage` for usage details.

Note that for maintenance actions the maintenance endpoints must be active.

## Tasks
### Backup / Restore
* [Database Backup and Restore](backup.md)
* You can also use [Import / Export](import_export.md) for this task.
* The [hdctl](../hdctl) Bash tool's `fetch` and `push` subcommands can be used for this purpose as well.

### Deploy / Export / Import (transporting between instances) / Update
* [Import / Export](import_export.md).
* The [hdctl](../hdctl) Bash tool's fetch and push subcommands can be used for this purpose as well.
  * Note that this simply uses the backend's /api/transformations GET and PUT endpoints which can of cause be used directly.

#### Automatically
On startup of the backend
* [Automatic deployment of base trafos](base_component_deployment.md)
* [Automatic import of sets of trafos](autoimport.md)

Note:
* Both can also be triggered via the [hdctl](../hdctl) Bash tool
* This simply uses some of the /api/maintenance/* endpoints described above.
* Using the `allow_overwrite_released` query parameter (or in config files for [autoimport](autoimport.md)) this allows to update (overwrite) existing transformation revisions. **Warning**: This may introduce bugs in existing workflows and compromise reproducibility.

### Cleanup operations
* See [cleanup docs](cleanup.md)
* If maintenance endpoints are available, [hdctl](../hdctl) can trigger each cleanup action as well.

## Maintenance Risks
Some maintenance operations naturally are affecting reproducibility and deserialization. See [here](./repr_pitfalls.md) for typical pitfalls and how to avoid them.

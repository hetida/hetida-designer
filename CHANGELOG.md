## 0.9.1
* add [restricted-to-execution-of-preselected trafos webservice mode](./docs/execution/restricted_webservice.md)

## 0.9.0
* add [optional inputs with default parameters](./docs/default_values.md)
* add [structured exception handling](./docs/structuring_exceptions.md)
  :warning: **BREAKING CHANGE**: The attribute `error` in the response JSON of the execute endpoint is no longer a string but a mapping/dictionary 
* add [free text filters for outputs (adapter system)](./docs/adapter_system/)
* add blob storage adapter config options
* add general [sql adapter](./docs/adapter_system/sql_adapter.md) with timeseries table support
* add [improved metadata attrs handling](./docs/metadata_attrs.md) - in particular a manual input method
  * **BREAKING CHANGE**: Consequently the output json format for direct provisioning has changed to include metadata for dataframes, multitsframes and (time)series objects.
* add python demo adapter sources and output free text filters
* add additional validations
* fix workflow validation issues via db migration
* fix filter for categories in export
* upgrade to python 3.11
* upgrade dependencies
* **WARNING/BREAKING CHANGE**: One of the introduced bugfixes includes a database migration fixing affected workflows. However if you export(ed) transformations with an earlier version than 0.9 and afterwards import them into a version >=0.9 the transforamtions may again include the bug. We therefore strongly recommend that you **make a backup and/or export both before and after upgrading**.

## 0.8.9
* free text filters for inputs (adapter system)
* add blob storage configuration options
* improved blob storage adapter performance
* type-specific blob storage serialization (keras models)
* new data type: MultiTSFrames (collections of multiple timeseries with non-simultaneous timestamps)
* api improvements / fixes
* frontend adaption to new transformations endpoints.
* NOTE: The endpoints deprecated since 0.7.* may be actually removed in one of the next releases
* new workflows / components: When upgrading it is recommended to re-deploy the base components/workflows

## 0.8.8
* add automatic bucket creation to blob storage adapter
## 0.8.7
* add S3 compatible built-in blob storage adapter
* add pickle persistence for ANY type to local file adapter
* fix docker-compose reverse proxy config
## 0.8.6
* (frontend) add configurable user info text on main tab
* fixes, in particular around validation
* fixes around updating components
* add maintenance backend endpoints (deactivated by default)
* add hdctl command line bash script for maintenance / devops tasks via those endpoints
## 0.8.5
* fix NaN value serialization (should now be serialized to null json values)
* fix broken pure plot execution config
* more bug fixes
* improvements for example workflows
## 0.8.4
* fix outgoing auth config parsing
## 0.8.3
* some new timeseries related base components and example workflows
* improved export / import supporting clean-up operations and filters
* more flexible authentication for outgoing requests
* bug fixes
## 0.8.2
* add some time measurement to successful execution output
* update base images
## 0.8.1
* improve contextualized logging
* add async (web hook / callback) execution web endpoint
* minor improvements and fixes
## 0.8.0
* authentication via OpenID Connect. See [documentation](https://github.com/hetida/hetida-designer/blob/develop/docs/enabling_openidconnect_auth.md). **When upgrading, you may have to explicitely deactivate auth via `HD_USE_AUTH=false` environment variables for runtime and backend service in your setup, since it is activated per default for both these services. See the changed default docker-compose setup!** 
* automatic deployment of base components. Documented [here](https://github.com/hetida/hetida-designer/blob/develop/docs/base_component_deployment.md).
* usability improvements wiring / selection dialog
* adapter system: directly attach any metadata as attributes to dataframes / series. See for example [here](https://github.com/hetida/hetida-designer/blob/develop/docs/adapter_system/generic_rest_adapters/web_service_interface.md#dataframe-get)
* additional playwright end2end tests
* bug fixes, refactorings

## 0.7.6
* fix db config management bug
* add more logging
## 0.7.5
* fix db config password secret handling
## 0.7.4
* fix DB user config environment variable name
* small documentation fixes
## 0.7.3
* Allow special characters in adapter source/sink ids
* small bug fixes
* documentation restructuring and improvements
## 0.7.2
* Bugfixes concerning migration and importing
* documentation fixes and improvements
## 0.7.1
* Bug fixes!
* you may now write async components by making your main function async
* improve execution logging: now contains operator names and level/hierarchy
* new endpoint to run latest revision of a revision group
* restore the Kafka execution consumer and add improvements, in particular allow many configuration options to be set
* Kafka execution also allows to execute latest revision of a revision group
* add user interface end-to-end test suite (using playwright)
## 0.7.0
* Complete Rewrite of the backend service in Python (formerly Java). This includes a lot of bug fixes.

> :warning: IMPORTANT: Upgrading from 0.6.* to 0.7 requires [manual migration steps](./docs/migration_from_0.6_to_0.7.md)!
* update frontend dependencies
* export/import of components/workflows feature (see [docs](./docs/import_export.md))

## 0.6.19
* fix runtime POST errors caused by https://github.com/encode/uvicorn/issues/1345
## 0.6.18
* (security fix) upgrade java dependencies (see [Issue #9](https://github.com/hetida/hetida-designer/issues/9))
* upgrade Python dependencies
* preparations for export / import feature
* add docker build and push script replacing Travis build
## 0.6.17
* (security fix) upgrade log4j to 2.16.0
## 0.6.16
Important: It is strongly recommended to upgrade designer installations to this version or higher
due to the critical log4j security vulnerability known as "Log4Shell" (0-day Remote Code Execution)!
* update log4j dependency (important security fix!)
* fix workflow deployment
* minor documentation updates
## 0.6.15
* fix [Issue #6](https://github.com/hetida/hetida-designer/issues/6)
* add documentation for postgres backup
* add documentation for using R via rpy2
## 0.6.14
* add output information to /workflows endpoint
## 0.6.13
* minor fixes and improvements
## 0.6.12
* update some dependencies
* add ortools to default runtime dependencies
## 0.6.11
* improve default timeout settings and add some documentation
* add component export/import facilities from/to only a Python code file
* extend component code generation to include information enabling export/import from just the component code.
## 0.6.10
* remove buggy demo workflows
## 0.6.9
* security updates dependencies
* minor fixes and improvements
## 0.6.8
* minor fixes and improvements
## 0.6.7
* upgrade Python dependencies
## 0.6.6
* switch/adapt to unprivileged docker images
* add some more default Python dependencies to runtime
* add info endpoints for liveness probes
* minor documentation fix

## 0.6.5
* add documentation for workflow execution via web endpoint

## 0.6.4
* add built-in local file adapter to runtime

## 0.6.1, 0.6.2, 0.6.3
* fix adapter documentation
* fix travis build process (reduce log output to handle maximum log size limitations)
* fix [Issue #4](https://github.com/hetida/hetida-designer/issues/4)

## 0.6.0
* introducing the hetida designer adapter system
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
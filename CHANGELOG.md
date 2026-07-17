- allow component import and hetdesrun usage in components during unit testing
- replace python-jose with joserfc for JWT verification. BREAKING CHANGE: if an expected audience (`HD_AUTH_AUDIENCE`, default `account`) or issuer (`HD_AUTH_ISSUER`) is configured, the respective claim must now be present in tokens and match — tokens lacking the claim are rejected. Set `HD_AUTH_AUDIENCE` to an empty string to disable audience checking.
- more secure and precise auth configuration
- sql adpater config BREAKING CHANGE: requires explicit flag to allow arbitrary sql query sources from now on, default being not to allow them. Table allowlist is now enforced at read/write
- BREAKING CHANGE: async execution endpoint callback urls must now be pre-configured via `HD_ALLOWED_CALLBACK_URL_PATTERNS`
- introduce JWT algorithm pinning via `HD_AUTH_ALLOWED_ALGORITHMS` and fix exp claim being now required as intended
- many smaller fixes
- BREAKING CHANGE: tighten model object loading path handling to avoid path traversals. This may affect existing stored objects with very unusual object names or tag names.

## 0.14.0
- Added configurable Opentelemetry support via logfire
- documentation rewrite + documentation building via static site generator (see https://hetida.github.io/hetida-designer)
- add simple cron-based **scheduling**.
- **MIGRATION NOTE**: If you have multiple backend service instances, e.g. if using additional restricted webservices you need to ensure that only the one frontend facing backend instance has `HETIDA_DESIGNER_SCHEDULING_ACTIVE=true` and all others have `HETIDA_DESIGNER_SCHEDULING_ACTIVE=false`. See the scheduling docs for details.
- **MIGRATION NOTE**: In order for scheduling to work in authenticated setups you need to configure `HD_SCHEDULING_INTERNAL_AUTH_MODE=CLIENT` and `HD_SCHEDULING_INTERNAL_AUTH_CLIENT_SERVICE_CREDENTIALS` to some service user credentials.
- **DEPRECATION WARNING**: gunicorn mode will be removed in a future version. pure uvicorn mode (already the default) will be the only remaining mode for backend and runtime webservice. Note that scheduling will not work if you are still using gunicorn mode.
- Proper obj / model repo path directory in nix shell setup
- fix component adapter metadata wiring handling
- fix hetida platform channel timeseries data component metadata allowing relativeNamePath as metric_key for accessing metadata.
- Upgrade to Python 3.14
- **BREAKING CHANGE**: dependency upgrades: In particular Pandas was upgraded from <=2.x to major release 3.x. This may affect / break component code in multiple ways.
- **BREAKING CHANGE**: When using auth, audience and issuer checks are now active by default and will be carried out if environment variables `HD_AUTH_AUDIENCE` (defaults to `account`) or respectively `HD_AUTH_ISSUER` are set, which we recommend to always do.
- maintenance endpoint for deleting old deprecated trafos now has two exclusion parameters (explicit revisions and one to only those that were disabled before a cutoff timestamp)
- A new **[hdhelpers](https://github.com/hetida/hdhelpers)** library provides functionality to faciliate component writing, in particular for visualization components and for integration into hetida platform. E.g. to respect locale / language settings, different themes and use provided metadata of timeseries data. As an example, there is a new version of the "Single Timeseries Plot" component, that uses this helpers.
- **Builtin Drop adapter**: When outputs are wired to this adapter, they are simply dropped. This faciliates writing components / workflows with multiple outputs where it depends on the concrete use case, which output is relevant.
- **Builtin Plot adapter**: When outputs are wired to this adapter, these outputs are converted into a basic predefined plot suitable for the output type. This faciliates writing components / workflows so that the same workflow can be used in automation and to visually inspect results without the need to include a plot operator.
- frontend / angular update to angular 19
- make final docker images compatible with trivy scans.
- minor fixes in forecast component

## 0.13.10

- fix overwriting during autodeployment
- new version of hetida platform channel timeseries component adapter source component
- fixing component adapter concurrency context handling, in particular logging
- describe concurrency behaviour better in documentation

## 0.13.9

- new metadata convention and helper functions to access structured metadata for MULTITSFRAME and SERIES object handling fallback behaviour. See [docs](./docs/metadata_attrs.md) for details.
- add support for frames / animations for rendering Plotly plots
- add hetida platform data source base components

## 0.13.8

- Add hotkey for test execution dialog (Shift+Enter)
- Add hotkey for quick test execution (using the current test wiring, without opening the execution/wiring dialog) (Alt+Enter)
- Add hotkey (ESC) for closing the execution result / protocol view.
- Add autosave status indicator
- option to deprecate other revisions when releasing a new one
- recommend semver patch version increase for version tag upon creating a new revision in frontend if previous revision has a simple semver version tag
- add logging import + setup to default component code template

## 0.13.7

- compatibility fix for psycopg3 for structure upserting for large number of sources / sinks

## 0.13.6

- forward context into component adapter component execution

## 0.13.5

- Execution dialog now allows to specify timeranges with relative dtexp expressions.
- New generic forecasting base component
- Improved error handling for runtime service worker process termination
- Add endpoint to obtain complete structure from backend structure service

## 0.13.4

- make metadata column adding more flexible and adaptable to different metadata structures

## 0.13.3

- add function in hdutils to add columns to a multitsframe from its metadata.
- Virtual Structure adapter provides metadata
- Input wirings support an attrs field that allows to update / override .attrs metadata for objects loaded from adapters
- Execution/wiring dialog allows to enter time ranges directly, allowing possibly relative datetime expressions like `now-15min, now` (to e.g. specify interval of last 15 minutes) and more (see [dtexp](https://github.com/stewit/dtexp) docs)
- Fixing validation in UI to allow entering `null` as manual input for optional inputs.
- free text filters now can have default values.
- Plotly config can now be specified under key `"config"` on the plotly fig dict object. The designer frontend will respect and use these configurations. Additionally, German Plotly locale package is installed into the frontend.

## 0.13.2

- More lenient runtime execution context parsing

## 0.13.1

- support int metric columns for timeseries tables in sql adapter

## 0.13.0

- **BREAKING CHANGE** Upgraded to psycopg3. When using postgres you need to replace psycopg2 with psycopg in respective URLs (configurations, component code if you use it there). Since psycopg3 is stricter, you may need to adapt code to that.
- Add backend support for relative timerange filters (like "now - 10d") for input wirings for sql adapter and generic rest adapters. Now is inferred from reproducibility context exec start timestamp.
- From and to timestamps for time intervals are now resolved using dtexp library, allowing them to express timeranges relative to execution start timestamp from the reproducibility context. This impacts adapters and dashboarding. In particular any input wiring that uses "timestampFrom" and "timestampTo" filters can now be provided expressions like "now -2d" or "now". This functionality is currently only available via API, not via the frontend.
- **POSSIBLY BREAKING CHANGE**: Generic rest adapters will now be requested with isoformat timestamps using offsets ("+00:00" for UTC) in "from" and "to" params (formerly Zulu format was used for UTC). Furthermore timeseries timestamps will be preferably be sent with "+00:00" offset instead of Zulu "Z" instead. External services and adapters interacting with hetida designer should ensure to be able to parse all typical isoformat timestamps everywhere where timestamps are received from designer.
- add Pegelonline component which is an example for a source component for the component adapter.
- **BREAKING CHANGE**: Removed `import_transformations` function and replaced entirely with `import_transformations_from_dir`. This may affect import script operations. The new function should be a drop-in replacement.
- Add support for specifying wirings via uris in the backend. It is planned to add this possibility to the Frontend in an upcoming release.
- Components can now import other components. This allows to reuse functions, classes etc that you may require in multiple components and therefore reduces the need to install custom packages to the designer runtime just for this purpose.
- Remove long-outdated / deprecated web endpoints for base-items, components, workflows, wirings and documentation.
- Remove exporting capabilities for exporting from the long-outdated / deprecated pre 0.7 Java backend
- Allow to change a single operator revision to a DRAFT revision in a DRAFT Workflow.

## 0.12.1

- dependency upgrades and upgrade to Python 3.13
- **BREAKING CHANGE**: removed u8darts from runtime image due to non-maintained transitive dependencies
- improve traceback presentation on errors.

## 0.12.0

- new feature: draft operators: workflows in draft state can now contain operators in draft state
  - releasing requires that all operators are released
  - the toolbar button for upgrading operators now also upgrades draft operators to the current state of the draft revision.
  - detects / prevents cycles
- fixed crushed workflow icon
- fixed bug in blob storage adapter
- structured logging
- some updates to base components
- improve auth token refresh option documentation
- several smaller fixes

## 0.11.4

- Fix component code logging, enrich messages and make them part of execution responses. In particular it can be viewed in the test result display.
- reduce autosave interval and provide some error message if updating trafos fails.
- include job id to load/send requests against generic rest adapters to improve tracability of execution jobs
- improve / clearify test execution result / protocol view
- fix component adapter sink search backend endpoint
- replace hyphens by underscore in hdctl. This allows to import component py files directly.
- fix / improve some outdated docs
- fix newline handling in String outputs or in json representation of ANY outputs leading to problems in the test execution result / protocol view.

## 0.11.3

- Avoid unnecessary direct output parsing / serialization between runtime and backend. Also mitigates some issues related to automatic dtype detection / conversion of Pandas read_json function.
- Add additional request measurements for communication between backend and runtime
- Fix auth role checking resulting in 403 when role checking is deactivated but some roles are present in the default role key.
- Fix getting dependant trafos / nested trafos

## 0.11.2

- Add pure uvicorn mode, allowing to circumvent usage of gunicorn for now.

## 0.11.1

- include docker-compose changes

## 0.11.0

- **BREAKING CHANGE**: Pydantic V2 migration.
  - validation is more strict, in particular for component/workflow outputs
  - serialization is less tolerant: If your workflow actually provides a string value for a float this will raise an Exception now
  - components using Pydantic need to migrate as well
    - **UPGRADE NOTE**: base components/workflows should be redeployed overwriting released trafos
  - overhauling parsing and validation may result in minor differences generally. E.g.
    serialization of UTC datetimes may use "Z" instead of "+00:00" to indicate the timezone.
- performance improvements through pydantic V2 and avoiding some serialization/desiralization loops.
- improved logging and execution results:
  - Include information on loaded and sent data and memory usage.
  - Additional steps of the execution process are measured.
  - Restructure execution logging and provide more hints on executed trafo. Make some details of execution logging configurable.
- dependency / library upgrades. In particular plotly upgrade.
- fix component editor cursor jumping
- improve docker-compose files
- **BREAKING CHANGE**: New default of gunicorn MAX_WORKERS: 1

## 0.10.2

- fix buggy comparison to "null" string for optional input default values

## 0.10.1

- fix buggy detection of async component main functions
- add pendulum dependency for better datetime calculations in components
- dependency upgrades

## 0.10.0

- add component adapter: Write components that acts as sources/sinks for the adapter system
- improve workflow operator upgrading:
  - upgrading keeps links into and out of the operator if possible (types agree)
  - new button for auto-upgrading all operators in a DRAFT workflow with respect to released_timestamp of the respective transformation revisions
- add import transformations button in frontend / home tab: Allows to import components and workflows by pasting json or component code directly in the user interface.
- add component unit test button: Run component unit tests from designer frontend.
- add component code cleanup button: formatting, test wiring, release wiring, add documentation as module docstring (if no docstring is present)
- bugfixes and dependency upgrades

## 0.9.10

- dependency upgrades / Docker image upgrades / security upgrades
- fix Python demo adapter tests

## 0.9.9

- Add structure service / [virtual structure adapter](https://github.com/hetida/hetida-designer/blob/release/docs/adapter_system/virtual_structure_adapter.md)
- add modify_timezone helper function to hdutils
- allow more than one value columns when sending data to a generic rest adapter MultiTFFrame sink
- add a numeric external type (aka "timeseries(numeric)") to the adapter system to be less strict when serializing series data.
- add new components to faciliate switching between long format (MultiTsFrame) and wide format multivariate timeseries data
- upgrade Angular to version 17
- add [tips and tricks](https://github.com/hetida/hetida-designer/blob/release/docs/tips_and_tricks.md) documentation concerning handling of Pandas objects and their indices
- improve [documentation](https://github.com/hetida/hetida-designer/blob/release/docs/sync.md) for writing unit tests for components
- improve and update auth / keycloak documentation and example image version.
- Allow caching of released trafo revisions for execution
- deep links to workflows / components and open selections of them
- improve experimental dashboarding: tables, expose workflow inputs in dashboards
- add [external sources adapter](https://github.com/hetida/hetida-designer/blob/release/docs/adapter_system/external_sources_adapter.md) providing builtin access to some relevant external data sources.

## 0.9.8

- Add Kafka adapter to send and receive data via Kafka individually per input/output. See [docs](./docs/adapter_system/kafka_adapter.md).
- Some frontend bug fixes

## 0.9.7

- Log execution performance metrics
- UI: Add deep links to (multiple) workflows and components
- Allow to provide parsing options for manual input / direct_provisioning adapter for Pandas-like data. In particular this allows to choose other orients of the json representation, like "split". "split" is relevant for SERIES objects since it allows to enter series data with duplicate entries in the index, which is otherwise not possible.
  - **BREAKING_CHANGE**: For SERIES objects hetida designer now outputs the wrapped format with `orient="split"` parsing option to guarantee inclusion of duplicate indices for "direct_provisioning" output wirings.
- Add url parameters to multiple trafo put and get endpoints for more fine-granular test wiring stripping. Use this for example when transfering trafos between instanced where adapters are
  not present on the target system
- Several new components and example workflows
- Add an --add parameter to hdctl which allows to add files to an existing export directory
  instead of overwriting the whole directory every time.

## 0.9.6

- fix receiving duplicates with inlcude_dependencies param in trafo GET endpoints
- expand_component_code now also supports adding test wirings to code with non direct_provisioning adapters
- add instance support for non-sync commands in hdctl

## 0.9.5

- Add hdctl sync feature, allowing for comfortable "hybrid development" of component code, i.e. switching frequently between working locally in your IDE and development in the hetida designer UI. Among other things this enables and streamlines several aspects of component/workflow development and operations tasks:
  - Keep your components/workflows versioned in a git repo.
  - Develop unit tests / doctests along with your components.
  - Develop component code in Jupyter.
  - Simplified component/workflow GitOps.
  - See the [sync documentation](https://github.com/hetida/hetida-designer/tree/release/docs/sync.md) for details.
- Allow /transformations GET and PUT endpoints to emit / receive components as python code instead of json objects
- new (possibly code-changing!) parameters to the /api/transformations GET endpoint that when set to true make sure that the component code contains everything (test wiring, documentation as module docstring, COMPONENT_INFO dict containing metadata)
- **BREAKING CHANGE**: Importing components from python code which only contain the old @register decorator will no longer work. Component code must contain the new COMPONENT_INFO dictionary from now on instead in order to be importable from code via the various [importing means](./docs/import_export.md). Importing from json files is not affected.
- **BREAKING CHANGE**: All transformations in the open source repo have changed insignificantly:
  In component code, the @register decorater has been replaced by COMPONENT_INFO dictionaries.
  In addition, attributes that have already been added to the respective classes in previous releases are now added to the transformation JSONs as well.
  If you re-import them (note: this is not done automatically when updating the docker image) into an existing hd instance where you have [persisted models](./docs/persisting_models.md) you may be affected by [deserialization problems](./docs/repr_pitfalls.md) and need to re-create those persisted models.
- Bugfixes and improvements on handling default values. Default values can now include metadata.
- some new base components

## 0.9.4

- bug fixes around default value handling
- **BREAKING CHANGE**: DRAFT transformation revisions with a released timestamp will no longer be accepted but cause a ValueError. A database migration fixing affected components and workflows is added. However if you export(ed) transformations with an earlier version than 0.9 and afterwards import them into a version >=0.9.4 the transformations may again include the bug. We therefore strongly recommend that you **make a backup and/or export both before and after upgrading**.

## 0.9.3

- improve dashboarding token refresh
- minor fixes and documentation improvements

## 0.9.2

- **BREAKING CHANGE**: Fixed environment variable name `HETIDA_DESIGNER_RUNTIME_ENGINE_URL` (from mispelled `HETIDA_DESIGNER_RUNTIME_EGINE_URL`)
- Add experimental [dashboarding](./docs/dashboarding.md) feature

## 0.9.1

- add [restricted-to-execution-of-preselected trafos webservice mode](./docs/execution/restricted_webservice.md)

## 0.9.0

- add [optional inputs with default parameters](./docs/default_values.md)
- add [structured exception handling](./docs/structuring_exceptions.md)
  :warning: **BREAKING CHANGE**: The attribute `error` in the response JSON of the execute endpoint is no longer a string but a mapping/dictionary
- add [free text filters for outputs (adapter system)](./docs/adapter_system/)
- add blob storage adapter config options
- add general [sql adapter](./docs/adapter_system/sql_adapter.md) with timeseries table support
- add [improved metadata attrs handling](./docs/metadata_attrs.md) - in particular a manual input method
  - **BREAKING CHANGE**: Consequently the output json format for direct provisioning has changed to include metadata for dataframes, multitsframes and (time)series objects.
- add python demo adapter sources and output free text filters
- add additional validations
- fix workflow validation issues via db migration
- fix filter for categories in export
- upgrade to python 3.11
- upgrade dependencies
- **WARNING/BREAKING CHANGE**: One of the introduced bugfixes includes a database migration fixing affected workflows. However if you export(ed) transformations with an earlier version than 0.9 and afterwards import them into a version >=0.9 the transformations may again include the bug. We therefore strongly recommend that you **make a backup and/or export both before and after upgrading**.

## 0.8.9

- free text filters for inputs (adapter system)
- add blob storage configuration options
- improved blob storage adapter performance
- type-specific blob storage serialization (keras models)
- new data type: MultiTSFrames (collections of multiple timeseries with non-simultaneous timestamps)
- api improvements / fixes
- frontend adaption to new transformations endpoints.
- NOTE: The endpoints deprecated since 0.7.\* may be actually removed in one of the next releases
- new workflows / components: When upgrading it is recommended to re-deploy the base components/workflows

## 0.8.8

- add automatic bucket creation to blob storage adapter

## 0.8.7

- add S3 compatible built-in blob storage adapter
- add pickle persistence for ANY type to local file adapter
- fix docker-compose reverse proxy config

## 0.8.6

- (frontend) add configurable user info text on main tab
- fixes, in particular around validation
- fixes around updating components
- add maintenance backend endpoints (deactivated by default)
- add hdctl command line bash script for maintenance / devops tasks via those endpoints

## 0.8.5

- fix NaN value serialization (should now be serialized to null json values)
- fix broken pure plot execution config
- more bug fixes
- improvements for example workflows

## 0.8.4

- fix outgoing auth config parsing

## 0.8.3

- some new timeseries related base components and example workflows
- improved export / import supporting clean-up operations and filters
- more flexible authentication for outgoing requests
- bug fixes

## 0.8.2

- add some time measurement to successful execution output
- update base images

## 0.8.1

- improve contextualized logging
- add async (web hook / callback) execution web endpoint
- minor improvements and fixes

## 0.8.0

- authentication via OpenID Connect. See [documentation](https://github.com/hetida/hetida-designer/blob/develop/docs/enabling_openidconnect_auth.md). **When upgrading, you may have to explicitely deactivate auth via `HD_USE_AUTH=false` environment variables for runtime and backend service in your setup, since it is activated per default for both these services. See the changed default docker-compose setup!**
- automatic deployment of base components. Documented [here](https://github.com/hetida/hetida-designer/blob/develop/docs/base_component_deployment.md).
- usability improvements wiring / selection dialog
- adapter system: directly attach any metadata as attributes to dataframes / series. See for example [here](https://github.com/hetida/hetida-designer/blob/develop/docs/adapter_system/generic_rest_adapters/web_service_interface.md#dataframe-get)
- additional playwright end2end tests
- bug fixes, refactorings

## 0.7.6

- fix db config management bug
- add more logging

## 0.7.5

- fix db config password secret handling

## 0.7.4

- fix DB user config environment variable name
- small documentation fixes

## 0.7.3

- Allow special characters in adapter source/sink ids
- small bug fixes
- documentation restructuring and improvements

## 0.7.2

- Bugfixes concerning migration and importing
- documentation fixes and improvements

## 0.7.1

- Bug fixes!
- you may now write async components by making your main function async
- improve execution logging: now contains operator names and level/hierarchy
- new endpoint to run latest revision of a revision group
- restore the Kafka execution consumer and add improvements, in particular allow many configuration options to be set
- Kafka execution also allows to execute latest revision of a revision group
- add user interface end-to-end test suite (using playwright)

## 0.7.0

- Complete Rewrite of the backend service in Python (formerly Java). This includes a lot of bug fixes.

> :warning: IMPORTANT: Upgrading from 0.6.\* to 0.7 requires [manual migration steps](./docs/migration_from_0.6_to_0.7.md)!

- update frontend dependencies
- export/import of components/workflows feature (see [docs](./docs/import_export.md))

## 0.6.19

- fix runtime POST errors caused by https://github.com/encode/uvicorn/issues/1345

## 0.6.18

- (security fix) upgrade java dependencies (see [Issue #9](https://github.com/hetida/hetida-designer/issues/9))
- upgrade Python dependencies
- preparations for export / import feature
- add docker build and push script replacing Travis build

## 0.6.17

- (security fix) upgrade log4j to 2.16.0

## 0.6.16

Important: It is strongly recommended to upgrade designer installations to this version or higher
due to the critical log4j security vulnerability known as "Log4Shell" (0-day Remote Code Execution)!

- update log4j dependency (important security fix!)
- fix workflow deployment
- minor documentation updates

## 0.6.15

- fix [Issue #6](https://github.com/hetida/hetida-designer/issues/6)
- add documentation for postgres backup
- add documentation for using R via rpy2

## 0.6.14

- add output information to /workflows endpoint

## 0.6.13

- minor fixes and improvements

## 0.6.12

- update some dependencies
- add ortools to default runtime dependencies

## 0.6.11

- improve default timeout settings and add some documentation
- add component export/import facilities from/to only a Python code file
- extend component code generation to include information enabling export/import from just the component code.

## 0.6.10

- remove buggy demo workflows

## 0.6.9

- security updates dependencies
- minor fixes and improvements

## 0.6.8

- minor fixes and improvements

## 0.6.7

- upgrade Python dependencies

## 0.6.6

- switch/adapt to unprivileged docker images
- add some more default Python dependencies to runtime
- add info endpoints for liveness probes
- minor documentation fix

## 0.6.5

- add documentation for workflow execution via web endpoint

## 0.6.4

- add built-in local file adapter to runtime

## 0.6.1, 0.6.2, 0.6.3

- fix adapter documentation
- fix travis build process (reduce log output to handle maximum log size limitations)
- fix [Issue #4](https://github.com/hetida/hetida-designer/issues/4)

## 0.6.0

- introducing the hetida designer adapter system

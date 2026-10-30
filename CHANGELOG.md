- runtime Python dependency upgrades
- complete refactoring of the startup behaviour: Misconfigurations that lead to silent data loss, e.g. by accidently configuring or fallback to an in-memory database, are now avoided at several places. Migrations, autodeployment do not run twice anymore as could happen before in some configurations. The backend container now refuses to start with an in-memory database unless it is allowed explicitly via `HD_ALLOW_IN_MEMORY_DB=true` to avoid misconfigurations. An in-memory database additionally requires a single web server process (`WEB_CONCURRENCY` unset or `1`). Unified [autoimport](https://hetida.github.io/hetida-designer/deployment_operation/trafo_import_export/autoimport/) behaviour with respective maintenance action. Improved parsing of the respective env variables. Added more logging and warnings for possibly undesired configurations. Improved documentation for database configuration, transformation autodeployment etc.
- **POSSIBLY BREAKING CHANGE**: The runtime parses the metadata of SERIES, SINGLETSFRAME and MULTITSFRAME workflow inputs loaded from adapters, including manual input via direct provisioning, once and attaches it as immutable model under `attrs["hd_metadata"]` if it follows the metadata conventions, in place of the keys `dataset_metadata`, `metrics` and `value_dimensions_shared`. pandas shares the model instead of deep-copying the metadata for every derived object. Component code must read the metadata via `read_metadata` of `hdhelpers.metadata` (or the helper functions of hdhelpers) instead of accessing e.g. `attrs["dataset_metadata"]` directly, attach changed metadata to its results via `set_metadata` and use `attrs_to_json` where it serializes attrs itself, e.g. for `json.dumps` or `to_parquet`. Outputs, the generic REST adapters, the local file adapter and the blob storage adapter receive the JSON form of the metadata, also in pickles, which therefore contain no hdhelpers classes. Metadata not following the conventions is left as it is. Older metadata structures, e.g. `by_metric` or `column_units`, are no longer supported. Requires hdhelpers 0.1.0, which now specifies the metadata conventions and is required by `hdutils.py` (also as exported by `hdctl`). See [Metadata attached as model](https://hetida.github.io/hetida-designer/user_guide/attached_metadata/#metadata-attached-as-model).
- New endpoint `POST /api/metadata-conventions/check/{data_type}` checks metadata against the [metadata conventions](https://hetida.github.io/hetida-designer/user_guide/attached_metadata/#specification-and-validation) for SERIES, SINGLETSFRAME and MULTITSFRAME. It expects the metadata and optionally the data in the wrapped format of the direct provisioning adapter and returns the found errors and warnings, e.g. metrics of the data missing in the metadata. The JSON Schemas `SeriesMetadata`, `SingleTSFrameMetadata` and `MultiTSFrameMetadata` documenting the metadata of its request body specify the metadata conventions in the openapi.json, so they are versioned together with the backend and third party projects like adapters can validate metadata against them. In component code and tests `check_metadata_conventions` of `hdhelpers.metadata` provides the same checks. The metadata examples of the generic REST adapter API documentation now follow the current metadata conventions.
- The metadata conventions are strict: Metadata adhering to them provides the dataset metadata with `metric_key`, `queried_metrics`, the ref interval (unless `ref_dataset_discrete` is true) and for SERIES and SINGLETSFRAME `single_metric`, as well as each metric with `id`, `name` and a value dimension for each value column with `column`, `unit` and `measurement` (the latter two may be null if unknown, the unit of a dimensionless quantity is ""). The value dimension "value" of a SERIES is described under `value_dimensions` like for the other data types. `value_data_type` of a value dimension is one of "float", "integer", "boolean" and "string". `default_aggregation_method` is one of MEAN (with alias AVG), MEDIAN, SUM, MIN, MAX, FIRST, LAST and COUNT, defaulting to LAST for boolean and string values and to MEAN otherwise, and `inherited` holds arbitrary properties without predefined fields, which should not repeat fields the conventions define for metrics and value dimensions, like "name", "id" or "unit". Timestamps are UTC isoformat strings which must be actual points in time. `single_metric` must be one of the `queried_metrics`. Checking metadata reports metrics or value columns of the data which the metadata does not describe as errors and warns about fields the conventions do not define, which may be misspelled, about queried metrics without metric metadata and about data outside of the ref interval. Components nevertheless cope with missing or incomplete metadata, since it is only validated where configured.
- The field `channel_id` of the metric metadata in the metadata conventions is deprecated in favour of the new field `signal_id`, since the hetida platform calls channels signals now. Checking metadata warns about `channel_id`.
- The metadata conventions specify the structure of the comments of a metric as the hetida platform provides them: time range (`start_date`, `end_date`), `created_at`, `edited_at`, `content`, `username`, `tags` and `replies`. Checking metadata reports comments with an incomplete or reversed time range.
- The metadata conventions include the further fields the hetida platform provides: `default_aggregation_method` of a metric as well as `signal_group`, `ref_data_frequency` and `ref_data_frequency_offset` of the dataset metadata.
- The metadata conventions describe more about the data: `query_timestamp` (the point in time whose state of the data was delivered, for reproducing reads) and `default_aggregation_interval` in the dataset metadata, the `path` of a metric in the hierarchy of its source system, its `origin`, and how its values are recorded: `recording_mode` ("periodic", "on_change" or "irregular"), `data_frequency` and `data_frequency_offset` per metric (taking precedence over `ref_data_frequency` and `ref_data_frequency_offset` of the dataset metadata), `recording_aggregation_method` for values aggregating their interval and the `deadband` of value dimensions recorded on change. Frequencies must be positive Pandas date offset aliases or timedelta strings with unit, offsets non-negative timedelta strings smaller than their frequency (0 if missing). `data_frequency_timezone` (`ref_data_frequency_timezone` in the dataset metadata) aligns the intervals to local time instead of UTC: For frequencies shorter than a day they restart at each local midnight, longer ones follow the calendar of the time zone, e.g. local days for "1D". This describes e.g. values aggregating 2 hours or a day starting at local midnight, whose offset against UTC changes with daylight saving time. The frequency of a metric falls back as a whole: Its `data_frequency_offset` and `data_frequency_timezone` only apply together with its `data_frequency`, otherwise `ref_data_frequency`, `ref_data_frequency_offset` and `ref_data_frequency_timezone` of the dataset metadata apply. `recording_mode` "periodic" requires a frequency. Inherited properties should have the JSON type matching their meaning. See [Recording of the values](https://hetida.github.io/hetida-designer/user_guide/attached_metadata/#recording-of-the-values).
- The metadata conventions include a `default_timezone` of each metric and of the dataset metadata as fallback: the time zone the timeseries should be evaluated in by default, e.g. by components aggregating days. It is an IANA time zone name like "Europe/Berlin" (one of Python's `zoneinfo.available_timezones()`, so the check does not depend on the system's time zone database) or a fixed UTC offset like "+02:00". In contrast to the plot target timezone of the execution context, which determines how timestamps are displayed, it belongs to the data. See [Time zones](https://hetida.github.io/hetida-designer/user_guide/attached_metadata/#time-zones).
- The metadata conventions include `decimals` for value dimensions: the number of decimal places numeric values should be displayed with, e.g. in tables, tooltips or reports. It only concerns the display, the values themselves are not rounded.
- The metadata conventions specify in which order information is looked up on the different levels of the metadata, with inherited properties only as last resort and not for information describing the metric itself, like its unit or names. The documentation now refers to the functions of hdhelpers for accessing metadata in component code.
- New runtime configuration `ADAPTER_METADATA_VALIDATION`: per adapter (`direct_provisioning` for manual input), the metadata of SERIES, SINGLETSFRAME and MULTITSFRAME workflow inputs is checked against the metadata conventions. "WARN" logs a warning listing the found issues together with the adapter, the inputs and their sources, "ERROR" lets the execution fail if errors are found. Missing metadata does not adhere to the conventions either. The warning lists each distinct issue once, with the number of occurrences and the inputs, so that e.g. the same unknown field in the metadata of every input or metric does not flood the logs. Defaults to "OFF", which leaves metadata not following the conventions as it is without notice. See [Validating received metadata](https://hetida.github.io/hetida-designer/integration_guide/adapter_system/adapter_registration/#validating-received-metadata).
- The docker compose setups and the nix based development setup, which the end-to-end tests use, configure `ADAPTER_METADATA_VALIDATION` with "ERROR" for the demo adapter, so that executions fail if its metadata does not adhere to the metadata conventions.
- **POSSIBLY BREAKING CHANGE**: The `attrs` of input wirings are merged into the metadata of the loaded data recursively instead of by a shallow update, and the same applies to the `meta_data` of virtual structure adapter sources. Dicts occurring in both are merged, so e.g. `{"dataset_metadata": {"default_timezone": "Europe/Berlin"}}` adds this field without losing the dataset metadata provided by the adapter. All other values, including lists like `metrics`, still replace same-named entries. Previously such an entry replaced the whole `dataset_metadata`. See [Adapter system and adapter support](https://hetida.github.io/hetida-designer/user_guide/attached_metadata/#adapter-system-and-adapter-support).
- **POSSIBLY BREAKING CHANGE**: The helper functions of `hetdesrun.helpers.metadata` are thin wrappers over those of `hdhelpers.metadata` now, so that they also work with metadata attached as model. Requested information is a field name or a dotted path like "inherited.site", glom specs are no longer supported, and metadata not following the metadata conventions, including older structures, gives no information. `add_columns_from_metric_metadata` of `hdutils` reads the metric metadata of the metadata conventions instead of `by_metric` or `metric_metadata`.
- The Python demo adapter provides metadata following the metadata conventions for all its SERIES, SINGLETSFRAME and MULTITSFRAME sources, built via the models of hdhelpers, including names, units, measurements and default aggregation methods of the timeseries, the `path` of the metrics from the hierarchy and for its simulated values `origin`, `recording_mode` "periodic" and `data_frequency`. Previously it provided metadata in an outdated format and for SERIES only for the anomaly scores. Metadata received with written data is still stored, but no longer returned when loading the data. Dimensionless quantities (anomaly scores, the state of the temperature SINGLETSFRAMEs) have the unit "". Written anomaly MULTITSFRAMEs are read in the closed interval their metadata states, instead of leaving out values at the interval boundaries. Plant A (located in Bremen) now uses °C and bar, and plant B got a location (Pittsburgh) and uses °F and psi. Their timeseries have the `default_timezone` of their plant ("Europe/Berlin", "America/New_York"), the MULTITSFRAMEs written to a plant on dataset level. The value dimensions of the simulated timeseries and of the anomaly scores have `decimals` (temperatures 1, pressures 2 in bar and 1 in psi, anomaly scores 3). A timeseries resampled via the frequency filter has `recording_aggregation_method` "FIRST", and its values are now timestamped with the start of their interval. Intervals starting before the queried start are left out, since they are only partially queried.
- **POSSIBLY BREAKING CHANGE**: The SQL adapter provides metadata following the metadata conventions for MULTITSFRAMEs loaded from timeseries tables: the requested metrics (with `ALL` those occurring in the data) as `queried_metrics`, the `query_timestamp` and an entry under `metrics` for each of them with database and table as `path`, instead of `by_metric`. When writing to timeseries tables allowing deletion (`allow_invalidation` and `delete_invalidated`), the metrics whose data is deleted are taken from `queried_metrics` of the dataset metadata, also if attached as model. `by_metric` and `ref_metrics` are no longer read, and the unused field `ref_metric` of the dataset metadata is removed. So writing a MULTITSFRAME whose metadata follows the conventions, e.g. passed on from loaded data, now deletes data of its queried metrics, where previously nothing was deleted for lack of metrics. See [SQL Adapter](https://hetida.github.io/hetida-designer/integration_guide/adapter_system/builtin_adapters/sql_adapter/).
- The external sources adapter provides metadata following the metadata conventions for its Open Meteo and Energy-Charts sources: the queried interval, the `query_timestamp` and an entry for each weather variable or the day-ahead price with the unit provided by the API, instead of the former top-level `ref_interval_start_timestamp` and `ref_interval_end_timestamp`. The Open Meteo ref interval starts and ends at the full hours the data is queried for, without the seconds of the requested interval. See [External Sources Adapter](https://hetida.github.io/hetida-designer/integration_guide/adapter_system/builtin_adapters/external_sources_adapter/).
- **POSSIBLY BREAKING CHANGE**: "Load Pegelonline Timeseries" (0.1.0) provides metadata following the metadata conventions, attached as model: the queried interval, the interval of the values as `ref_data_frequency`, the `query_timestamp` and the timeseries as metric with name, unit, measurement, default aggregation method, the water and station as `path`, `origin`, `recording_mode` "periodic" with `data_frequency` and `default_timezone` "Europe/Berlin". Water levels have `decimals` matching their resolution of 1 cm (0 in "cm", 2 in "m+NN" and "m+PNP"), other values none. The information on the station, previously available under `attrs["station"]`, is available under `inherited` of the metric, e.g. "latitude" or "station_shortname". This requires an additional request to Pegelonline for the unit and interval of the timeseries.
- new revision "Hetida Platform Signal Timeseries Data" (0.1.12): the metadata is everything hetida platform provides when loading the data, also fields the component does not know: each metric as provided, plus the `use_as_metric` field with the value of the metric column, and the dataset metadata (e.g. the ref interval and its type or `query_timestamp`) and further top level fields if they are the same for all signals. Differing dataset metadata is taken over by the metrics where the metadata conventions allow it (`default_timezone`, `data_frequency` with its offset and time zone), other differing fields are left out with a warning. The fields of the signal from the hierarchy (e.g. `externalTimeSeriesId`, `properties`, `hierarchy_object`, `relativeNamePath`) are no longer included. The default of `use_as_metric` is "external_id" now, the field name of the metadata, with the same values as "externalTimeSeriesId". Requires hetida platform 2603.1012 or newer. To use it via the `hd://timeseries` uri wiring shortcut, point the shortcut (`HETIDA_DESIGNER_URI_WIRING_SHORTCUTS`) to its id `329b1f21-b8aa-4c80-bb5f-8fa1dcae75ef`. It checks the metadata of the loaded signals, since the runtime only checks workflow inputs: It logs a warning summarizing the issues of the signals whose metadata does not adhere to the metadata conventions, or fails if "ERROR" is configured for the hetida platform adapter via `ADAPTER_METADATA_VALIDATION` and errors are found. Metadata following the conventions is attached as model. 0.1.11 is deprecated.
- The connectors "Convert Series to SingleTSFrame", "Convert SingleTSFrame to Series", "Convert SingleTSFrame to MultiTSFrame" and "Extract SingleTSFrame from MultiTSFrame" (1.0.0) convert metadata following the metadata conventions via the models of hdhelpers, so that it follows them for their output, too, and attach it: They rename the value dimension "value" to a custom value column name, reduce the value dimensions to the selected one renamed to "value" for a SERIES, set the metric in `single_metric`, `queried_metrics` and the single entry under `metrics` to a provided metric name, and reduce `queried_metrics` to the extracted metric. "Convert SingleTSFrame to MultiTSFrame" keeps the field identifying the metric, e.g. its `id` or `external_id`, when another metric name is provided: The name is set in the field named by `dataset_metadata.metric_key` if the metric lacks it, otherwise in the new field `metric` of the metric, and `dataset_metadata.metric_key` becomes "metric". Other metadata is handled as before. "Extract SingleTSFrame from MultiTSFrame" returns an empty SingleTSFrame with the narrowed metadata for a metric without data which is listed in `queried_metrics` or described under `metrics`, instead of failing.
- The "Extract Attributes" components output metadata attached as model in its JSON form. The "Add/Update Attributes" components update it in its JSON form and, for SERIES, SINGLETSFRAMEs and MULTITSFRAMEs, attach the result as model again if it still follows the metadata conventions. "SingleTSFrame Plot with multiple Y Axes" reads names and units via hdhelpers.
- "Gap Detection Intervals" and "Replacement Locations for Gaps" (1.0.0) take the queried interval and the frequency the values are recorded with (the `data_frequency` of the metric or else `ref_data_frequency` of the dataset metadata, each with its offset) from metadata following the metadata conventions via hdhelpers, with the former top-level keys (e.g. `ref_interval_start_timestamp` or `from` directly in the attrs) as fallback. Previously they ignored metadata following the conventions.
- The example metadata of base components follows the metadata conventions, in the test and release wirings of "Extract Attributes (SingleTSFrame)", "Single Timeseries Plot", "SingleTSFrame Plot with multiple Y Axes" and "MultiTsFrame Plot with multiple Y Axes" as well as in the documentation of "Single Timeseries Plot", "µplot Single Timeseries Plot" and "Gap Detection Intervals". The same applies to the examples of the wrapped format on the documentation pages on attached metadata, MultiTSFrames and SingleTSFrames.

## 0.14.7

- Updates, including security updates for frontend and backend as well as docker images
- Fix: darkmode should generally work now
- New API endpoints to obtain the latest (by release timestamp) or the highest (by semantic versioning of the version tags) revision of revision groups, as full transformation revisions or as stubs: `GET /api/transformations/revision_groups/{revision_group_id}` and `GET /api/transformations/revision_groups/{revision_group_id}/stub` for a single revision group, `GET /api/transformations/revision_groups` and `GET /api/transformations/revision_groups/stubs` for all revision groups matching filters similar to `GET /api/transformations` (type, category, category prefix, name, revision group id). The query parameter `by` selects `latest` (default) or `highest`. Only released revisions are considered by default, deprecated revisions can be included via `include_deprecated` and, for `highest`, drafts via `include_drafts`. Version tags which are no semantic versions are ignored for `highest`. See [A note on version tags](https://hetida.github.io/hetida-designer/user_guide/versioning_and_lifecycle/#a-note-on-version-tags).
- New endpoints `POST /api/transformations/execute-highest` and `POST /api/transformations/execute-highest-async` execute the highest revision of a revision group. Kafka execution messages for revision groups accept `"by": "highest"`. The execute-latest / execute-highest endpoints and Kafka messages execute exactly the revision the new GET endpoints provide and accept `include_deprecated` (and for highest `include_drafts`) in their payload. If several released revisions of a revision group have the same release timestamp, the latest is now determined deterministically by the revision id. Kafka execution of revision groups now passes `runtime_execution_context` and `resolved_reproducibility_references` of the message on, like the REST endpoints.
- The button for upgrading the operators of a DRAFT workflow upgrades released and deprecated operators to the latest released revision of their revision group exactly as determined for `GET /api/transformations/revision_groups/{revision_group_id}` and the execute-latest endpoints. Previously, if several released revisions of a revision group had the same release timestamp, which of them was chosen was not defined.
- The edit details dialog ("Properties...") of components and workflows lists the workflows using them, directly as operator or nested in other workflows. Imports in component code are not considered. The new endpoint `GET /api/transformations/{id}/containing_workflows` provides this information.
- For released and deprecated trafos, the wiring dialog now has a button to reset the wiring to the release wiring.
- extend API documentation page to include maintenance endpoints and Blob storage adapter
- Telemetry (`HD_OTEL_VIA_LOGFIRE_ACTIVE`): logs with a traceback record the exception on their log span as span event with the standard OpenTelemetry attributes `exception.type`, `exception.message` and `exception.stacktrace`, instead of a non-standard attribute `exception` containing the traceback. Logs of level error additionally set the span status to error. All recorded exceptions get attributes `hetida_designer.exception.root_cause.*` with type, message and location of the root cause, e.g. of the actual error in component code. They can be queried and remain complete if backends like Grafana Tempo truncate the stacktrace. The JSON log output contains the trace context (`trace_id`, `span_id`, `trace_flags`) for linking logs and traces. See [Monitoring and Observability](https://hetida.github.io/hetida-designer/deployment_operation/monitoring/).
- **POSSIBLY BREAKING CHANGE**: base components and example workflows are auto-deployed at backend start also if the database is not empty, i.e. `HD_BACKEND_PRESERVE_DB_ON_AUTODEPLOY` defaults to `false` now. Together with `HD_BACKEND_ALLOW_OVERWRITE_RELEASED`, which defaults to `true`, this overwrites the base components and example workflows in the database by those of the image, so that fixes made in released revisions arrive with new images. Set `HD_BACKEND_PRESERVE_DB_ON_AUTODEPLOY` to `true` to keep the previous behaviour. See [Deployment of Base Component and Workflows](https://hetida.github.io/hetida-designer/deployment_operation/trafo_import_export/base_trafo_deployment/).
- fix: "Load Pegelonline Timeseries" (0.1.0) returns its timeseries with a UTC datetime index. Pegelonline provides timestamps in German local time, so previously the index had a fixed offset like +02:00, and loading failed for time ranges containing a daylight saving time change (mixed offsets). Time ranges without data now result in an empty timeseries instead of an error.
- fix: executions sporadically failed within milliseconds with an "unexpected" error caused by an empty `ReadError`, without the runtime receiving the execution request. The backend reused an idle connection to the runtime just as the runtime closed it, since both used 5 seconds as idle limit. The backend and runtime now keep idle connections open for 65 seconds (keep-alive timeout), configurable via `UVICORN_TIMEOUT_KEEP_ALIVE` and in the deprecated gunicorn mode via `KEEP_ALIVE`. The same applies to the Python demo adapter. The error message of such failures now names the type of the error. See [Keep-alive timeout](https://hetida.github.io/hetida-designer/deployment_operation/timeouts/#keep-alive-timeout).
- fix: with telemetry activated (`HD_OTEL_VIA_LOGFIRE_ACTIVE`) and `OTEL_EXPORTER_OTLP_ENDPOINT` set, backend and runtime sent every span twice, the second time without logfire's processing, e.g. without scrubbing of sensitive values. Since 0.14.6, FastAPI configured an additional export of its own from the same environment variables. This automatic export configuration of FastAPI (`FASTAPI_OTEL_AUTO_CONFIGURE`) is now deactivated if telemetry is activated via logfire. See [Monitoring and Observability](https://hetida.github.io/hetida-designer/deployment_operation/monitoring/).
- fix: base components "Moving Time Window Mean" (1.0.0), "Moving Time Window Median" (1.0.0) and "Convert DataFrame to MultiTSFrame" (1.0.0) no longer modify their input: they sorted the input series in place, respectively moved the timestamp column of the input dataframe to its index. Other operators receiving the same input could see these modifications. Their outputs are unchanged. Together with the hetida platform timeseries source components and the SQL and external sources adapters they no longer use pandas' `inplace` keyword, which is deprecated since pandas 3.1.
- fix: base component "2D Scatter Plot colored by other Series" (1.0.0) triggered a pandas deprecation warning for categorical and string color series. "2D Scatter Plot colored by Index" (1.0.0) contains the same code and was fixed as well.
- fix: the deprecated "Hetida Platform Channel Timeseries Data" (0.1.9) lost the adapter metadata if no data was loaded, so the metric metadata lacked the inherited properties and comments.
- fix: "Gap Detection Intervals" (1.0.0) can be executed again: It failed with a TypeError for every input. Its documentation names the input `deactivate_freq_based_gap_detection` correctly. "Gap Detection Intervals" and "Replacement Locations for Gaps" (1.0.0) no longer change the gap intervals passed to them, and their documentation mentions that `ref_data_frequency_offset` from the metadata of the timeseries is used if no `expected_data_frequency_offset` is provided.
- fix: "Gap Detection Intervals" and "Replacement Locations for Gaps" (1.0.0) no longer cut off a gap at the end of a shorter gap contained in it, e.g. at a missing expected datapoint inside a larger gap. Without an offset, "Replacement Locations for Gaps" aligns the replacement locations to the first datapoint (or the interval start) as documented, instead of a mirrored rhythm.
- fix: "Gap Detection Intervals" and "Replacement Locations for Gaps" (1.0.0) reject calendar based frequencies and offsets like "MS" or "W" in their inputs and in the metadata with an error naming the input or metadata field, instead of silently reading e.g. "1MS" as 1 millisecond or failing with an unexpected error. Use fixed frequencies like "7D" instead. Unparseable frequencies fail with a validation error instead of an unexpected error.
- Loading SERIES inputs from generic REST adapters is considerably faster if many timeseries with large metadata are loaded together: Extracting each timeseries no longer lets pandas copy the metadata of all of them. E.g. for 500 timeseries with about 1.3 MB of metadata including comments, extracting them took about 70 seconds, now 0.2 seconds.
- "MultiTsFrame Plot with multiple Y Axes", "Convert MultiTSFrame to DataFrame" and "to Wide Format" (1.0.0) compute on their input without its metadata, since pandas copies the metadata on every operation. For a MULTITSFRAME of 500 metrics with about 1.1 MB of metadata (comments, inherited properties) the plot takes 0.9 instead of 32 seconds, the conversion to a DataFrame 0.7 instead of 51 seconds and the wide format 15 instead of 340 milliseconds. The user guide page on attached metadata explains this pitfall for own components.
- fix: "to Wide Format" (1.0.0) no longer changes the dtype of the "metric" column of its input.
- fix: "Add/Update Attributes (SingleTSFrame)" (1.0.0) no longer changes the attributes of its input, which other operators receiving the same input could see.
- fix: when writing to timeseries tables, the SQL adapter treats fields of the dataset metadata provided as null like missing fields, i.e. applies their defaults. Previously writing failed for null in e.g. `invalidate_dataset` or `ref_dataset_discrete`, as the hetida platform provides them for loaded data.
- fix: the Python demo adapter no longer sends records without timeseriesId for intervals without a value of a timeseries resampled via the frequency filter, which let loading fail, e.g. for "30min". Written anomaly MULTITSFRAMEs are read in the closed interval their metadata states, instead of leaving out values at the interval boundaries.
- fix: "Hetida Platform Signal Timeseries Data" (0.1.11) includes the metadata hetida platform provides for the loaded signals again. Since hetida platform provides it following the metadata conventions (hetida platform 2603.1012), the inherited properties and comments were lost. Now each metric additionally contains the name, description and external id, the value dimension with unit, measurement and value data type, and the default aggregation method provided by hetida platform.
- fix: notes, tips and warnings on the documentation pages about attached metadata, direct provisioning, the Kafka adapter, default values, MULTITSFRAMEs and SINGLETSFRAMEs as well as in the generic REST adapter API specification are displayed with their content again. The payload examples of the generic REST adapter API specification are valid JSON, and the documentation of URI wirings names "Hetida Platform Signal Timeseries Data" as target of `hd://timeseries`.

## 0.14.6

- fix: loading data from generic REST adapters failed with "Receive buffer too long" if the response headers exceeded 16 KiB, e.g. due to a large `Data-Attributes` header (metadata). This affected versions 0.14.3 to 0.14.5. The limit now defaults to 5 MiB and can be configured via the `GENERIC_REST_ADAPTER_MAX_RESPONSE_HEADER_SIZE` environment variable, see the [adapter REST API interface documentation](https://hetida.github.io/hetida-designer/integration_guide/adapter_system/adapter_rest_api_interface/#http-version-and-header-sizes). Framelike data fetching from generic REST adapters now always uses HTTP/1.1.
- fixes and improvements: hetida platform source components working with hetida platform versions >= 2603.1010. New revisions "Hetida Platform Assets" 0.1.6 and "Hetida Platform Signal Timeseries Data" 0.1.11. If used, URI wiring shortcuts (`HETIDA_DESIGNER_URI_WIRING_SHORTCUTS`, e.g. for `hd://assets` and `hd://timeseries`) should be updated to the new component ids.
  - asset properties include values inherited in the asset hierarchy, both components can filter assets / signals by (inherited) properties and the timeseries component always excludes transient virtual signals.
  - clearer errors for platform requests and responses. Requests use the `EXTERNAL_REQUEST_TIMEOUT` and `HETIDA_DESIGNER_ADAPTERS_VERIFY_CERTS` settings.
  - BREAKING CHANGE for URI wirings of the timeseries component: the inputs `include_ingestion_channels` / `include_virtual_channels` are renamed to `include_ingestion_signals` / `include_virtual_signals`.
- preparations for the upgrade to plotly 7 / plotly.js 4:
  - new revision "Simple Scatter Map Plot" 1.0.1 using the MapLibre based `scattermap` instead of the Mapbox based `scattermapbox`, which is removed in plotly 7. Revision 1.0.0 is disabled, workflows using it should be updated to the new revision. The "Visualization Demo" example workflow uses the new revision.
  - plots created via `plotly_fig_to_json_dict` from `hdutils` and plots shown in experimental dashboards get `showSendToCloud` set to false in their config, unless configured explicitly. Otherwise plotly.js 4 by default shows a modebar button which uploads the plot including its data to Plotly Cloud.
  - `plotly_fig_to_json_dict` sets tickmode "auto" for overlaying axes without explicitly configured tick placement (e.g. the additional y axes of plots with multiple y axes). Otherwise plotly.js 4 by default places their ticks at the tick positions of the overlaid axis (tickmode "sync").
  - fix: the example sink component writing plots to html files in the [component adapter documentation](https://hetida.github.io/hetida-designer/integration_guide/adapter_system/builtin_adapters/component_adapter/) failed for plots with a config, like those from `plotly_fig_to_json_dict`.
- base component "Convert Series to SingleTSFrame" (1.0.0) parses a string index strictly as ISO 8601 timestamps. Other strings, e.g. `"01.08.2019 15:45"` which was silently interpreted month first (8th of January), are rejected with a ComponentInputValidationException now.
- fix: the documentation of base component "Compare Timeshifted Timeseries" (1.0.0) suggested the frequency aliases `"H"` and `"M"`, which are invalid since pandas 3, and the deprecated `"d"`. It now suggests `"h"`, `"ME"` and `"D"`, and the "Visualization Demo" example workflow uses `"D"`.
- fix: base component "Select Time Intervals" (1.0.0) triggered a pydantic warning about a model validator not returning `self`.
- "Load Pegelonline Timeseries" (0.1.0) test and release wiring use the time range "now - 15d" to "now".
- components can find out whether the value of one of their outputs is discarded during the current execution via `output_is_discarded` from `hetdesrun.runtime.context`. This is the case if the output is not linked to another operator and the workflow output it is exposed as is wired to the drop adapter (or to the plot adapter while `run_pure_plot_operators` is false), also in nested workflows. This allows components with plot and data outputs to skip creating plots that nobody gets, e.g. in scheduled executions, which always run plot operators. `plot_output_needed` from `hdutils` combines this with `run_pure_plot_operators` for plot outputs. See [Skipping Unneeded Outputs](https://hetida.github.io/hetida-designer/user_guide/component_writing/discarded_outputs/).
- operators with only plot outputs are not run if all of their outputs are discarded, e.g. wired to the drop adapter, even if `run_pure_plot_operators` is true (e.g. in scheduled executions). The operators providing their inputs are run anyway in the same order as before, and operators without outputs are always run.
- runtime/backend Python dependency upgrades

## 0.14.5

- fix frontend relative uri behaviour for monaco editor and auth to default to full uri path, not just domain.
- add niquest opentelemetry instrumentation. Niquest is used for fetching (timeseries) data from generic rest adapters.
- document the optional `default_value` attribute of source/sink filters in the [adapter REST API interface documentation](https://hetida.github.io/hetida-designer/integration_guide/adapter_system/adapter_rest_api_interface/).
- default values of filters are now shown on hovering.
- the component adapter now maps a default value of json null of an optional component input to the string `"null"` for the `default_value` of the corresponding filter, so the execution dialog prefills the filter input field with `null` instead of leaving it empty.
- fix: the virtual structure adapter raised a validation error when converting a sink with passthrough filters.
- free text filters of sources and sinks may now provide an optional `description`. The execution dialog shows it below the input field and on hovering.
- the built-in adapters and the Python demo adapter now provide `description`s for their free text filters.
- the wiring dialog now shows the `path` of the wired source or sink as hint below the browse field and repeats it in full in the field's tooltip.
- MINOR RISK BREAKING COMPONENT CODE: Python dependency upgrades
- add Apache datafusion dependency

## 0.14.4

- new data type **SINGLETSFRAME** for a single, possibly multi-dimensional timeseries. It uses the same tabular representation as MULTITSFRAME (a `timestamp` column plus arbitrarily many value columns) but has no `metric` column, since it holds exactly one metric — the metric is identified in the attached metadata via `dataset_metadata.single_metric`, like for SERIES. See the [SingleTsFrame documentation](https://hetida.github.io/hetida-designer/user_guide/data_types/singletsframes/).
  - the generic REST adapter interface gains `/singletsframe` GET and POST endpoints and the external type `singletsframe`. Existing adapters are unaffected — the new endpoints only need to be implemented if you want to offer `singletsframe` sources/sinks.
  - the Python demo adapter offers a `singletsframe` demo source and sink.
  - new base components in the category "Connectors": Pass Through (SingleTSFrame), Convert Series to SingleTSFrame, Convert SingleTSFrame to Series, Extract SingleTSFrame from MultiTSFrame, Convert SingleTSFrame to MultiTSFrame, Convert SingleTSFrame to DataFrame, Convert DataFrame to SingleTSFrame, Add/Update Attributes (SingleTSFrame), Extract Attributes (SingleTSFrame). Plus "SingleTSFrame Plot with multiple Y Axes" in the category "Visualization".
  - new metadata helper functions `get_singlets_units`, `get_singlets_names`, `get_singlets_display_names`, `get_singlets_short_display_names`, `get_singlets_measurements` and `get_singlets_metric_info` in `hetdesrun.helpers.metadata`. Since a SingleTSFrame has exactly one metric, these are keyed by value dimension only.
- fix: the execution dialog now offers the json editor for MULTITSFRAME default values of workflow inputs and attaches the time range picker validators to MULTITSFRAME inputs (previously SERIES only)
- fix: experimental dashboards were empty (no output visualizations at all) when backend and runtime run as separate services — as in the provided docker compose setups. Since 0.14.3 the backend relays the runtime's output payload as raw json bytes, which the dashboard did not read. Setups with backend and runtime in one service were not affected.
- fix: stored scheduled-execution results were missing their direct-provisioning outputs (nothing to show in the schedule result view) when backend and runtime run as separate services — same root cause as the dashboard fix above: since 0.14.3 the outputs are relayed as raw json bytes, which the persistence path did not read before storing the result in the db. Setups with backend and runtime in one service were not affected.

## 0.14.3

- refactored generic rest adapter http client handling and data fetching
- faster execution result serialization: pandas and plotly outputs are spliced into the response as the json bytes produced by their respective serializer apis using `msgspec.Raw` allowing for single pass serialization, avoiding redundant JSON parse/re-encode round-trips
- faster result relaying with separate backend and runtime services: the backend now passes the runtime's output payload through to the caller as raw json bytes — validated as well-formed JSON but not parsed into Python and re-encoded. Slight performance improvements in particular for larger Plotly ouputs.
- BREAKING CHANGE: backend response gzip compression is now **off by default** and configurable via `RESPONSE_COMPRESSION_ENABLED` (and `RESPONSE_COMPRESSION_LEVEL`, default 1). This improves response time for larger responses (in particulary large plotly plots). It is recommended to compress at your reverse proxy / ingress instead, or set `RESPONSE_COMPRESSION_ENABLED=true` if your clients are on slow links. The internal backend => runtime request now never requests compression.
- hardened execution result serialization: any failure while serializing (untrusted) component output (e.g. non-serializable objects, circular references, unencodable dict)now becomes a structured failure result instead of a 5xx, at both the runtime and the backend response boundaries

## 0.14.2

- documentation improvements
- add documentation for some environment variables
- extend hierarchy object execution context information
- upgrade demo adapter dependencies

## 0.14.1

- reintegrate the former separate npm packages `hetida-flowchart`, `ng-hetida-flowchart` and `hd-wiring` (wiring dialog) from the hetida-flowchart repository directly into the frontend source tree (`frontend/src/libs/`), removing them as external dependencies
- ANY outputs of a specified structure can now be used to render images, pdfs, arbitrary html or offer file downloads. In particular HTML rendering allows to employ html/javascript based plotting libraries like µplot or Apache ECharts.
- allow component import and hetdesrun usage in components during unit testing
- replace python-jose with joserfc for JWT verification. BREAKING CHANGE: if an expected audience (`HD_AUTH_AUDIENCE`, default `account`) or issuer (`HD_AUTH_ISSUER`) is configured, the respective claim must now be present in tokens and match — tokens lacking the claim are rejected. Set `HD_AUTH_AUDIENCE` to an empty string to disable audience checking.
- more secure and precise auth configuration
- sql adpater config BREAKING CHANGE: requires explicit flag to allow arbitrary sql query sources from now on, default being not to allow them. Table allowlist is now enforced at read/write
- BREAKING CHANGE: async execution endpoint callback urls must now be pre-configured via `HD_ALLOWED_CALLBACK_URL_PATTERNS`
- introduce JWT algorithm pinning via `HD_AUTH_ALLOWED_ALGORITHMS` and fix exp claim being now required as intended
- BREAKING CHANGE: tighten model object loading path handling to avoid path traversals. This may affect existing stored objects with very unusual object names or tag names.
- add explicit worker timeout configuration for pure uvicorn setup
- performance improvements (DB queries, adapters, trafo loading)
- many smaller fixes

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

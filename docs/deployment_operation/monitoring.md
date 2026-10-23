## Monitoring and Observability

hetida designer supports [opentelemetry](https://opentelemetry.io/) observability / monitoring via [logfire](https://github.com/pydantic/logfire) against custom backends.

To activate it, set the environment variable `HD_OTEL_VIA_LOGFIRE_ACTIVE` to `true` for  backend and runtime containers. This will among others instrument httpx, asgi, and logging. Furthermore several custom spans are provided for the transformation excecution process.

You can then use [opentelemtry environment variables](https://opentelemetry.io/docs/specs/otel/configuration/sdk-environment-variables/) like `OTEL_EXPORTER_OTLP_ENDPOINT` to configure the otel collector / backend to which spans, metrics and logs will be sent. We recommend to also set at least  `OTEL_SERVICE_NAME` to `hetida-designer-backend` or `hetida-designer-runtime`. As an example the docker-compose-dev setup has telemetry activated and comes with a Grafana Stack Single Container service.

The export is configured by logfire only: FastAPI's own automatic export configuration (`FASTAPI_OTEL_AUTO_CONFIGURE`) is deactivated if `HD_OTEL_VIA_LOGFIRE_ACTIVE` is `true`, since it would send every span a second time.

### Exceptions

Exceptions are recorded as span events named `exception` with the standard OpenTelemetry attributes `exception.type`, `exception.message` and `exception.stacktrace`: on the span they escape from, and for logs with a traceback (e.g. about errors during an execution) on the log span.

Additionally, every recorded exception gets attributes describing its root cause, i.e. the innermost exception of the chain shown in the traceback (`raise ... from ...` or raised during handling of another exception). For example errors in component code are recorded as `UnexpectedComponentException` with the generic message "Unexpected error from user code.", while the actual error is its root cause. For exceptions without such a chain, these attributes describe the exception itself.

| Attribute | Description |
| --- | --- |
| `hetida_designer.exception.root_cause.type` | fully qualified exception type, like `exception.type` |
| `hetida_designer.exception.root_cause.message` | exception message |
| `hetida_designer.exception.root_cause.code.file.path` | file where it was raised. For component code `CODE OF COMPONENT <name> (<version tag>) UUID <id>` |
| `hetida_designer.exception.root_cause.code.function.name` | fully qualified name of the function where it was raised |
| `hetida_designer.exception.root_cause.code.line.number` | line number where it was raised |

These attributes can be used in queries, e.g. in TraceQL of Grafana Tempo: `{ event.hetida_designer.exception.root_cause.type = "ValueError" }`.

### Tracebacks cut off in Grafana Tempo

[Grafana Tempo](https://grafana.com/docs/tempo/latest/configuration/#distributor) truncates attribute values longer than 2048 bytes by default. This cuts off the tracebacks of exceptions recorded in spans (`exception.stacktrace`), and with them their most relevant part, the end. The root cause attributes described above are short enough not to be affected and the complete traceback is contained in the log output (see below). Raise the limit via `max_attribute_bytes` in the `distributor` section of the Tempo configuration, e.g. to 16384.

### Linking logs and traces

If telemetry is activated, the JSON log output contains the trace context of the span active during logging in the fields `trace_id`, `span_id` and `trace_flags`, as specified by [OpenTelemetry for JSON logs](https://opentelemetry.io/docs/specs/otel/compatibility/logging_trace_context/). The log span created by logfire for the log message is a child of this span.

If you collect the log output, e.g. with Grafana Loki, you can link logs and traces via the trace id. For Grafana see [Trace to logs](https://grafana.com/docs/grafana/latest/datasources/tempo/configure-tempo-data-source/configure-trace-to-logs/). Like all fields, e.g. `exception` containing the traceback, they can be renamed via the environment variable `LOG_FIELDS_TO_RENAME`, a JSON object mapping field names to new names (replacing the default mapping).

!!! note "Importan Note"
    logfire [handles log messages as spans of duration 0](https://github.com/pydantic/logfire/issues/1118#issuecomment-2939297738) and will not send them as classical logs!
## Monitoring and Observability

hetida designer supports [opentelemetry](https://opentelemetry.io/) observability / monitoring via [logfire](https://github.com/pydantic/logfire) against custom backends.

To activate it, set the environment variable `HD_OTEL_VIA_LOGFIRE_ACTIVE` to `true` for  backend and runtime containers. This will among others instrument httpx, asgi, and logging. Furthermore several custom spans are provided for the transformation excecution process.

You can then use [opentelemtry environment variables](https://opentelemetry.io/docs/specs/otel/configuration/sdk-environment-variables/) like `OTEL_EXPORTER_OTLP_ENDPOINT` to configure the otel collector / backend to which spans, metrics and logs will be sent. We recommend to also set at least  `OTEL_SERVICE_NAME` to `hetida-designer-backend` or `hetida-designer-runtime`. As an example the docker-compose-dev setup has telemetry activated and comes with a Grafana Stack Single Container service.

The export is configured by logfire only: FastAPI's own automatic export configuration (`FASTAPI_OTEL_AUTO_CONFIGURE`) is deactivated if `HD_OTEL_VIA_LOGFIRE_ACTIVE` is `true`, since it would send every span a second time.

### Tracebacks cut off in Grafana Tempo

[Grafana Tempo](https://grafana.com/docs/tempo/latest/configuration/#distributor) truncates attribute values longer than 2048 bytes by default. This cuts off the tracebacks of exceptions recorded in spans (`exception.stacktrace`), and with them their most relevant part, the end. Raise the limit via `max_attribute_bytes` in the `distributor` section of the Tempo configuration, e.g. to 16384.

!!! note "Importan Note"
    logfire [handles log messages as spans of duration 0](https://github.com/pydantic/logfire/issues/1118#issuecomment-2939297738) and will not send them as classical logs!
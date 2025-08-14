The designer now supports opentelemetry. In detail, wen the environment variable `OTEL_EXPORTER_OTLP_ENDPOINT` and `OTEL_EXPORTER_OTLP_PROTOCOL` are specified, then the runtime and backend starts with auto-instrumented opentelemetry.

Per default the service name of both containers is *hetida_designer*. Please overwrite the environment variable `OTEL_SERVICE_NAME` to specifiy the service in more detail.

Too see other possible environment variables please refer to opentelemetry [documentation](https://opentelemetry-python.readthedocs.io/en/latest/sdk/environment_variables.html).

## Opentelemetry support

hetida designer supports opentelemetry observability / monitoring via [logfire](https://github.com/pydantic/logfire) against custom backends.

To activate it, set the environment variable `HD_OTEL_VIA_LOGFIRE_ACTIVE` to `true` for  backend and runtime containers. This will instrument http, asgi, custom spans for execution and also instrument logging. Furthermore several custom spans are provided for the transformation excecution process.

You can then use [opentelemtry environment variables](https://opentelemetry.io/docs/specs/otel/configuration/sdk-environment-variables/) like `OTEL_EXPORTER_OTLP_ENDPOINT` to configure the otel collector / backend to which spans, metrics and logs will be sent. We recommend to also set at least  `OTEL_SERVICE_NAME` to `hetida-designer-backend` or `hetida-designer-runtime`. As an example the docker-compose-dev setup has telemtry activated and comes with a Grafana Stack Single Container service.

**Important Note**: logfire [handles log messages as spans of duration 0](https://github.com/pydantic/logfire/issues/1118#issuecomment-2939297738) and will not send them as classical logs!
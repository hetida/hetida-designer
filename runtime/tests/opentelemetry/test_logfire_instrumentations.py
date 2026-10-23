import os
from collections import Counter
from collections.abc import Generator, Sequence
from unittest import mock

import logfire
import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from logfire.testing import CaptureLogfire
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExportResult
from sqlalchemy.future.engine import Engine

from hetdesrun.trafoutils.trafo_collection import TrafoCollection
from hetdesrun.webservice.application import init_app


@pytest.fixture(scope="function")  # noqa: PT003
def activate_logfire() -> Generator:
    with mock.patch(
        "hetdesrun.webservice.config.runtime_config.otel_via_logfire_active", new=True
    ) as _fixture:
        yield _fixture


@pytest.fixture(scope="function")  # noqa: PT003
def distributed_tracing_via_env(monkeypatch: pytest.MonkeyPatch) -> None:
    # capfire calls logfire.configure after init_app did, thereby resetting the
    # distributed_tracing=True set there to logfire's default (extract, but warn).
    # Without the argument, logfire.configure falls back to this environment variable.
    monkeypatch.setenv("LOGFIRE_DISTRIBUTED_TRACING", "true")


@pytest.fixture(scope="function")  # noqa: PT003
def deactivate_auth() -> Generator:
    with mock.patch("hetdesrun.webservice.config.runtime_config.auth", new=False) as _fixture:
        yield _fixture


@pytest.fixture(scope="function")  # noqa: PT003
def app_without_auth_with_logfire(
    deactivate_auth: Generator, activate_logfire: Generator
) -> FastAPI:
    return init_app()


@pytest_asyncio.fixture(scope="function")
async def async_test_client_with_logfire(app_without_auth_with_logfire: FastAPI) -> AsyncClient:
    async with LifespanManager(app_without_auth_with_logfire) as manager:
        return AsyncClient(transport=ASGITransport(app=manager.app), base_url="http://test")


@pytest.mark.asyncio
async def test_logfire_activation(
    mocked_clean_test_db_session,
    async_test_client,
    async_test_client_with_logfire,
    distributed_tracing_via_env,
    capfire: CaptureLogfire,
):

    with TrafoCollection(save_to_db=True) as tc:
        pt_string = tc.add_from_json_file(
            os.path.join(
                "transformations",
                "components",
                "connectors",
                "pass-through-string_100_2b1b474f-ddf5-1f4d-fec4-17ef9122112b.json",
            )
        )

    # first without logfire activated via our config option.
    # Note that logfire.testing will actually
    # call logfire.configure against its test exporters, so there will be spans!
    # but there won't be spans from the extra instrumentations we configure
    # if logfire is active, so we can measure a difference.

    exporter = capfire.exporter
    exporter.clear()

    async with async_test_client as client:
        resp = await client.post(
            "/api/transformations/execute",
            json={
                "id": str(pt_string.id),
                "wiring": {
                    "input_wirings": [
                        {
                            "adapter_id": "direct_provisioning",
                            "workflow_input_name": "input",
                            "filters": {"value": "TEST"},
                        }
                    ],
                },
            },
        )
    assert resp.status_code == 200
    num_spans_without = len(exporter.exported_spans_as_dict())

    # now with logfire, using the ordinary async_client

    exporter = capfire.exporter
    exporter.clear()

    async with async_test_client_with_logfire as client:
        resp = await client.post(
            "/api/transformations/execute",
            json={
                "id": str(pt_string.id),
                "wiring": {
                    "input_wirings": [
                        {
                            "adapter_id": "direct_provisioning",
                            "workflow_input_name": "input",
                            "filters": {"value": "TEST"},
                        }
                    ],
                },
            },
        )
    assert resp.status_code == 200

    assert len(exporter.exported_spans_as_dict()) > num_spans_without
    assert len(exporter.exported_spans_as_dict()) > 5


@pytest.fixture(scope="function")  # noqa: PT003
def otlp_export_via_env(monkeypatch: pytest.MonkeyPatch) -> Generator[Counter[int]]:
    """Configure OTLP trace export via env and count exports per span id instead of sending"""
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://127.0.0.1:9")  # never contacted
    monkeypatch.setenv("OTEL_METRICS_EXPORTER", "none")
    monkeypatch.setenv("OTEL_LOGS_EXPORTER", "none")

    exports_per_span_id: Counter[int] = Counter()

    def count_export(self: OTLPSpanExporter, spans: Sequence[ReadableSpan]) -> SpanExportResult:  # noqa: ARG001
        for span in spans:
            assert span.context is not None
            exports_per_span_id[span.context.span_id] += 1
        return SpanExportResult.SUCCESS

    monkeypatch.setattr(OTLPSpanExporter, "export", count_export)

    yield exports_per_span_id

    # Do not leave an OTLP exporter configured for subsequent tests
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    logfire.configure(send_to_logfire=False, console=False)


@pytest.mark.asyncio
async def test_logfire_spans_are_exported_only_once(
    monkeypatch: pytest.MonkeyPatch,
    deactivate_auth: Generator,
    activate_logfire: Generator,
    otlp_export_via_env: Counter[int],
) -> None:
    # FastAPI's automatic OTLP export configuration would add a second exporter
    # to the tracer provider configured by logfire. It is opt-in via this env var,
    # in fastapi 0.142.x it was the default.
    monkeypatch.setenv("FASTAPI_OTEL_AUTO_CONFIGURE", "true")

    app = init_app()
    async with (
        LifespanManager(app) as manager,
        AsyncClient(transport=ASGITransport(app=manager.app), base_url="http://test") as client,
    ):
        resp = await client.get("/api/info")
    assert resp.status_code == 200

    logfire.force_flush()

    assert len(otlp_export_via_env) > 0
    assert set(otlp_export_via_env.values()) == {1}


@pytest.fixture(scope="function")  # noqa: PT003
def app_with_logfire_instrumenting_test_db(
    test_db_engine: Engine, deactivate_auth: Generator, activate_logfire: Generator
) -> Generator[FastAPI]:
    """App with logfire activated, which instruments the test db engine

    The SQLAlchemy instrumentation is global and applied only once, to the engine passed
    first. So it is removed before and after, independent of other tests calling init_app.
    """
    if SQLAlchemyInstrumentor().is_instrumented_by_opentelemetry:
        SQLAlchemyInstrumentor().uninstrument()

    with mock.patch(
        "hetdesrun.persistence.db_engine_and_session.get_db_engine", return_value=test_db_engine
    ):
        yield init_app()

    if SQLAlchemyInstrumentor().is_instrumented_by_opentelemetry:
        SQLAlchemyInstrumentor().uninstrument()


@pytest.mark.asyncio
async def test_logfire_db_queries_produce_spans(
    mocked_clean_test_db_session,
    app_with_logfire_instrumenting_test_db: FastAPI,
    distributed_tracing_via_env: None,
    capfire: CaptureLogfire,
) -> None:
    capfire.exporter.clear()

    async with (
        LifespanManager(app_with_logfire_instrumenting_test_db) as manager,
        AsyncClient(transport=ASGITransport(app=manager.app), base_url="http://test") as client,
    ):
        resp = await client.get("/api/transformations")
    assert resp.status_code == 200

    spans = capfire.exporter.exported_spans_as_dict()
    db_spans = [span for span in spans if "db.statement" in span["attributes"]]

    # opentelemetry-instrumentation-sqlalchemy refuses to instrument sqlalchemy versions
    # it does not declare support for, unless its dependency check is skipped.
    assert len(db_spans) > 0
    assert any(
        "transformation_revisions" in span["attributes"]["db.statement"] for span in db_spans
    )
    request_trace_ids = {
        span["context"]["trace_id"]
        for span in spans
        if span["name"].startswith("GET /api/transformations")
    }
    assert len(request_trace_ids) == 1
    assert {span["context"]["trace_id"] for span in db_spans} == request_trace_ids

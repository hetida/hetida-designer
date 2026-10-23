import json
import logging
import os
import sys
from collections.abc import Generator, Sequence
from unittest import mock

import logfire
import pytest
from httpx import AsyncClient
from logfire.testing import TestExporter
from opentelemetry import trace
from opentelemetry.sdk.trace import Event, ReadableSpan
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.trace import StatusCode

from hetdesrun import get_formatter
from hetdesrun.runtime import runtime_logger
from hetdesrun.runtime.logging import FieldRenamer
from hetdesrun.trafoutils.trafo_collection import TrafoCollection
from hetdesrun.webservice.application import init_app
from hetdesrun.webservice.telemetry import (
    add_root_cause_to_exception_event,
    get_root_cause,
    root_cause_attributes,
)

ROOT_CAUSE = "hetida_designer.exception.root_cause."


@pytest.fixture(scope="function")  # noqa: PT003
def span_exporter() -> Generator[TestExporter]:
    """Like logfire's capfire fixture, but configured like the app

    capfire calls logfire.configure without the exception callback.
    """
    exporter = TestExporter()
    logfire.configure(
        send_to_logfire=False,
        console=False,
        distributed_tracing=True,
        additional_span_processors=[SimpleSpanProcessor(exporter)],
        advanced=logfire.AdvancedOptions(exception_callback=add_root_cause_to_exception_event),
    )
    yield exporter
    logfire.configure(send_to_logfire=False, console=False)


def exception_events(spans: Sequence[ReadableSpan]) -> list[Event]:
    return [event for span in spans for event in span.events if event.name == "exception"]


def raise_value_error() -> None:
    raise ValueError("actual problem")


RAISE_VALUE_ERROR_LINE = raise_value_error.__code__.co_firstlineno + 1


class CustomError(Exception):
    pass


def raise_wrapped_value_error() -> None:
    try:
        raise_value_error()
    except ValueError as exc:
        raise RuntimeError("generic message") from exc


def raise_during_handling() -> None:
    try:
        raise_value_error()
    except ValueError:
        raise KeyError("during handling")  # noqa: B904


def raise_with_suppressed_context() -> None:
    try:
        raise_value_error()
    except ValueError:
        raise KeyError("context suppressed") from None


def test_root_cause_follows_cause_and_context() -> None:
    with pytest.raises(RuntimeError) as exc_info:
        raise_wrapped_value_error()
    assert str(get_root_cause(exc_info.value)) == "actual problem"

    with pytest.raises(KeyError) as key_error_info:
        raise_during_handling()
    assert str(get_root_cause(key_error_info.value)) == "actual problem"

    # Python does not show suppressed contexts in tracebacks either
    with pytest.raises(KeyError) as key_error_info:
        raise_with_suppressed_context()
    assert get_root_cause(key_error_info.value) is key_error_info.value

    exception_without_chain = ValueError("no chain")
    assert get_root_cause(exception_without_chain) is exception_without_chain

    exception_in_cycle = ValueError("cycle")
    other_exception = KeyError("other")
    exception_in_cycle.__cause__ = other_exception
    other_exception.__cause__ = exception_in_cycle
    assert get_root_cause(exception_in_cycle) is other_exception


def test_root_cause_attributes() -> None:
    with pytest.raises(RuntimeError) as exc_info:
        raise_wrapped_value_error()

    assert root_cause_attributes(exc_info.value) == {
        ROOT_CAUSE + "type": "ValueError",
        ROOT_CAUSE + "message": "actual problem",
        ROOT_CAUSE + "code.file.path": __file__,
        ROOT_CAUSE + "code.function.name": f"{__name__}.raise_value_error",
        ROOT_CAUSE + "code.line.number": RAISE_VALUE_ERROR_LINE,
    }

    # type names like exception.type of the OpenTelemetry SDK, no location if never raised
    assert root_cause_attributes(CustomError("not raised")) == {
        ROOT_CAUSE + "type": f"{__name__}.CustomError",
        ROOT_CAUSE + "message": "not raised",
    }


def test_logged_exception_is_recorded_as_exception_event(span_exporter: TestExporter) -> None:
    try:
        raise_wrapped_value_error()
    except RuntimeError:
        runtime_logger.info("Component Error during workflow execution", exc_info=True)

    [log_span] = span_exporter.exported_spans
    assert log_span.name == "Component Error during workflow execution"
    # Formerly the traceback was a non-standard attribute of the log span
    assert "exception" not in (log_span.attributes or {})

    [event] = exception_events([log_span])
    attributes = event.attributes or {}
    assert attributes["exception.type"] == "RuntimeError"
    assert attributes["exception.message"] == "generic message"
    assert "ValueError: actual problem" in str(attributes["exception.stacktrace"])
    assert attributes[ROOT_CAUSE + "type"] == "ValueError"
    assert attributes[ROOT_CAUSE + "message"] == "actual problem"
    assert attributes[ROOT_CAUSE + "code.function.name"] == f"{__name__}.raise_value_error"
    assert attributes[ROOT_CAUSE + "code.line.number"] == RAISE_VALUE_ERROR_LINE
    assert log_span.status.status_code is StatusCode.UNSET


def test_logged_error_sets_span_status(span_exporter: TestExporter) -> None:
    try:
        raise_wrapped_value_error()
    except RuntimeError:
        runtime_logger.exception("Unexpected error")

    [log_span] = span_exporter.exported_spans
    assert log_span.status.status_code is StatusCode.ERROR
    assert log_span.status.description == "RuntimeError: generic message"
    assert len(exception_events([log_span])) == 1


def test_exception_escaping_span_has_root_cause_attributes(span_exporter: TestExporter) -> None:
    with pytest.raises(RuntimeError), logfire.span("failing"):
        raise_wrapped_value_error()

    [event] = exception_events(span_exporter.exported_spans)
    attributes = event.attributes or {}
    assert attributes["exception.type"] == "RuntimeError"
    assert attributes[ROOT_CAUSE + "type"] == "ValueError"


def format_log_record(message: str, exc_info: bool = False) -> dict:
    record = logging.LogRecord(
        name="test_logger",
        level=logging.WARNING,
        pathname=__file__,
        lineno=1,
        msg=message,
        args=(),
        exc_info=sys.exc_info() if exc_info else None,
    )
    return json.loads(get_formatter().format(record))


def test_json_logs_contain_trace_context_and_full_traceback(span_exporter: TestExporter) -> None:
    assert "trace_id" not in format_log_record("outside of spans")

    with logfire.span("active span"):
        span_context = trace.get_current_span().get_span_context()
        try:
            raise_wrapped_value_error()
        except RuntimeError:
            log = format_log_record("logged with exception", exc_info=True)

    assert log["trace_id"] == f"{span_context.trace_id:032x}"
    assert log["span_id"] == f"{span_context.span_id:016x}"
    assert log["trace_flags"] == "01"
    assert log["exception"].startswith("Traceback (most recent call last):")
    assert "ValueError: actual problem" in log["exception"]
    assert log["exception"].endswith("RuntimeError: generic message")

    # The log span created by logfire is in the same trace as the active span
    log_span = next(
        span for span in span_exporter.exported_spans if span.name == "logged with exception"
    )
    assert log_span.context is not None
    assert log_span.context.trace_id == span_context.trace_id
    # and neither gets the trace context fields nor the formatted traceback as attributes
    assert {"trace_id", "span_id", "trace_flags", "exception"}.isdisjoint(log_span.attributes or {})


def test_trace_context_and_exception_fields_can_be_renamed(span_exporter: TestExporter) -> None:
    with (
        mock.patch.object(
            FieldRenamer, "_FIELD_MAP", {"trace_id": "trace.id", "exception": "error.stack_trace"}
        ),
        logfire.span("active span"),
    ):
        try:
            raise_value_error()
        except ValueError:
            log = format_log_record("logged with exception", exc_info=True)

    assert "trace_id" not in log
    assert "exception" not in log
    assert len(log["trace.id"]) == 32
    assert log["error.stack_trace"].endswith("ValueError: actual problem")


def test_init_app_configures_exception_callback(activate_logfire: Generator) -> None:
    with mock.patch("logfire.configure", wraps=logfire.configure) as configure:
        init_app()
    logfire.configure(send_to_logfire=False, console=False)

    advanced_options = configure.call_args.kwargs["advanced"]
    assert advanced_options.exception_callback is add_root_cause_to_exception_event


@pytest.mark.asyncio
async def test_component_error_root_cause_is_recorded(
    mocked_clean_test_db_session,
    async_test_client_with_logfire: AsyncClient,
    span_exporter: TestExporter,
) -> None:
    with TrafoCollection(save_to_db=True) as tc:
        raising_component = tc.add_from_py_file(
            os.path.join("tests", "data", "components", "raise_value_error.py")
        )

    async with async_test_client_with_logfire as client:
        resp = await client.post(
            "/api/transformations/execute",
            json={
                "id": str(raising_component.id),
                "wiring": {
                    "input_wirings": [
                        {
                            "adapter_id": "direct_provisioning",
                            "workflow_input_name": "msg",
                            "filters": {"value": "error from component code"},
                        }
                    ],
                },
            },
        )
    assert resp.status_code == 200
    assert resp.json()["error"]["type"] == "ValueError"

    log_span = next(
        span
        for span in span_exporter.exported_spans
        if span.name == "Component Error during workflow execution"
    )
    [event] = exception_events([log_span])
    attributes = event.attributes or {}

    # the recorded exception is the generic wrapper ...
    assert attributes["exception.type"] == (
        "hetdesrun.runtime.exceptions.UnexpectedComponentException"
    )
    assert attributes["exception.message"] == "Unexpected error from user code."
    # ... and the root cause the actual error in the component code
    assert attributes[ROOT_CAUSE + "type"] == "ValueError"
    assert attributes[ROOT_CAUSE + "message"] == "error from component code"
    assert str(attributes[ROOT_CAUSE + "code.file.path"]).startswith(
        "CODE OF COMPONENT Raise Value Error (0.1.0) UUID "
    )
    assert str(attributes[ROOT_CAUSE + "code.function.name"]).endswith(".main")
    assert isinstance(attributes[ROOT_CAUSE + "code.line.number"], int)

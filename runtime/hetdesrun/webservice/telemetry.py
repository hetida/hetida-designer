"""Additions to the OpenTelemetry support via logfire (HD_OTEL_VIA_LOGFIRE_ACTIVE)

Recorded exceptions are span events with the standard attributes exception.type,
exception.message and exception.stacktrace. Backends like Grafana Tempo truncate long
attribute values, cutting off the end of the stacktrace. Hence some details are recorded
as additional attributes, which are short enough to be kept completely and can be queried.
"""

from logfire.types import ExceptionCallbackHelper
from opentelemetry.util.types import AttributeValue

ROOT_CAUSE_ATTRIBUTE_PREFIX = "hetida_designer.exception.root_cause."


def exception_type_name(exception: BaseException) -> str:
    """Fully qualified type name, as in exception.type set by the OpenTelemetry SDK"""
    module = type(exception).__module__
    qualname = type(exception).__qualname__
    return f"{module}.{qualname}" if module and module != "builtins" else qualname


def get_root_cause(exception: BaseException) -> BaseException:
    """Innermost exception of the chain shown in the traceback

    Follows the cause (raise ... from ...) or else the context (raised during
    handling of another exception) like Python does when printing a traceback.
    The exception itself is returned if it has neither.
    """
    seen = {id(exception)}
    current = exception
    while True:
        next_exception = (
            current.__cause__
            if current.__cause__ is not None
            else (None if current.__suppress_context__ else current.__context__)
        )
        if next_exception is None or id(next_exception) in seen:
            return current
        seen.add(id(next_exception))
        current = next_exception


def root_cause_attributes(exception: BaseException) -> dict[str, AttributeValue]:
    """Attributes describing the root cause of an exception

    Wrapping exceptions like the UnexpectedComponentException raised from errors in
    component code carry a generic message, while the actual error is their cause. The
    part of the stacktrace about the cause is often cut off by backends truncating long
    attributes.

    The location of the root cause is its innermost frame, i.e. where it was raised,
    described by the standard code.* attributes.
    """
    root_cause = get_root_cause(exception)
    attributes: dict[str, AttributeValue] = {
        ROOT_CAUSE_ATTRIBUTE_PREFIX + "type": exception_type_name(root_cause),
        ROOT_CAUSE_ATTRIBUTE_PREFIX + "message": str(root_cause),
    }

    traceback = root_cause.__traceback__
    if traceback is None:  # never raised
        return attributes
    while traceback.tb_next is not None:
        traceback = traceback.tb_next

    code = traceback.tb_frame.f_code
    module_name = traceback.tb_frame.f_globals.get("__name__")
    attributes[ROOT_CAUSE_ATTRIBUTE_PREFIX + "code.file.path"] = code.co_filename
    attributes[ROOT_CAUSE_ATTRIBUTE_PREFIX + "code.function.name"] = (
        f"{module_name}.{code.co_qualname}" if isinstance(module_name, str) else code.co_qualname
    )
    if traceback.tb_lineno is not None:
        attributes[ROOT_CAUSE_ATTRIBUTE_PREFIX + "code.line.number"] = traceback.tb_lineno
    return attributes


def add_root_cause_to_exception_event(helper: ExceptionCallbackHelper) -> None:
    """Exception callback for logfire, called whenever an exception is recorded on a span

    Errors raised here are caught and logged by logfire, the exception is recorded anyway.
    Defined at module level, so that logfire can pass it on to ProcessPoolExecutor workers.
    """
    helper.event_attributes.update(root_cause_attributes(helper.exception))

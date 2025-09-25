# noqa: A005
import contextvars
import datetime
import json
import logging
from collections import deque
from typing import Any, Literal, TypedDict
from uuid import UUID

import numpy as np
from pydantic import BaseModel, Field

from hetdesrun.models.code import CodeModule
from hetdesrun.utils import Type
from hetdesrun.webservice.config import get_config


class SimplifiedLogRecord(BaseModel):
    timestamp: datetime.datetime = Field(..., description="log timestamp (UTC)")
    log_level: str = Field(..., description="Log level as string")
    lineno: int = Field(..., description="line number in component code module")
    message: str = Field(..., description="Simple Formatted message")
    tr_id: UUID | None = Field(None, description="Transformation id")
    tr_name: str | None = Field(None, description="Transformation name")
    tr_tag: str | None = Field(None, description="Transformation version tag")
    tr_type: Type | None = Field(None, description="Type of transformation.")
    operator_hierarchical_name: str | None = None
    operator_hierarchical_id: str | None = None


class CustomAttributeProcessor:
    """Processor that extracts custom attributes from the stdlib log record"""

    _STANDARD_LOG_RECORD_ATTRS = {
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
        "message",
        "exc_info",
        "exc_text",
        "stack_info",
        "getMessage",
        "taskName",
        "_record",
    }

    def __call__(self, logger: logging.Logger, method_name: str, event_dict: dict) -> dict:  # noqa: ARG002
        if record := event_dict.get("_record"):
            for key, value in record.__dict__.items():
                if key not in self._STANDARD_LOG_RECORD_ATTRS and not key.startswith("_"):
                    event_dict[key] = value
        return event_dict


class FieldRenamer:
    """Renames configured field names in the logs to corresponding aliases."""

    _FIELD_MAP = get_config().log_fields_to_rename

    def __call__(self, logger: logging.Logger, method_name: str, event_dict: dict) -> dict:  # noqa: ARG002
        for orig_name, new_name in self._FIELD_MAP.items():
            if orig_name in event_dict:
                event_dict[new_name] = event_dict.pop(orig_name)
        return event_dict


ExecContextDict = TypedDict(  # noqa: UP013
    "ExecContextDict",
    {
        "current_code_modules": list[CodeModule],
        "current_components": list[str],
        "gathered_component_code_logs": deque[logging.LogRecord],
    },
)

_WF_EXEC_LOGGING_CONTEXT_VAR: contextvars.ContextVar[ExecContextDict] = contextvars.ContextVar(
    "workflow_execution_logging_context"
)

_JOB_ID_LOGGING_CONTEXT_VAR: contextvars.ContextVar[dict] = contextvars.ContextVar(
    "job_id_logging_context"
)


class MinimallyMoreCapableJsonEncoder(json.JSONEncoder):
    """Additionally handles datetimes and UUIDs

    Usage:
        json.dumps(object_to_serialize, cls=MinimallyMoreCapableJsonEncoder)

    """

    def default(self, obj: Any) -> Any:
        if isinstance(obj, UUID):
            # if the obj is uuid, we simply return the value of uuid
            return obj.hex

        if isinstance(obj, datetime.datetime):
            return obj.isoformat()

        if isinstance(obj, np.ndarray):
            return obj.tolist()

        return json.JSONEncoder.default(self, obj)


def _get_execution_context() -> ExecContextDict:
    try:
        return _WF_EXEC_LOGGING_CONTEXT_VAR.get()
    except LookupError:
        _WF_EXEC_LOGGING_CONTEXT_VAR.set(
            {
                "current_code_modules": [],
                "current_components": [],
                "gathered_component_code_logs": deque(
                    maxlen=get_config().user_component_code_logs_max_len
                ),
            }
        )
        return _WF_EXEC_LOGGING_CONTEXT_VAR.get()


class ExecutionContextFilter(logging.Filter):
    """Filter to enrich log records with execution environment information"""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.currently_executed_transformation_id = None
        self.currently_executed_transformation_name = None
        self.currently_executed_transformation_tag = None
        self.currently_executed_transformation_type = None
        self.currently_executed_operator_hierarchical_id = None
        self.currently_executed_operator_hierarchical_name = None
        self.currently_executed_job_id = None
        self.code_modules = None
        self.components = None
        super().__init__(*args, **kwargs)

    def bind_context(self, **kwargs: Any) -> None:
        _get_execution_context().update(kwargs)  # type: ignore

    def unbind_context(self, *args: str) -> None:
        """Remove entries with provided keys from context"""
        ctx_dict = _get_execution_context()
        for key in args:
            ctx_dict.pop(key, None)  # type: ignore

    def clear_context(self, keys: list[str] | None = None) -> None:
        if keys is None:
            # reset / empty everything
            _WF_EXEC_LOGGING_CONTEXT_VAR.set(
                {
                    "current_code_modules": [],
                    "current_components": [],
                    "gathered_component_code_logs": deque(
                        maxlen=get_config().user_component_code_logs_max_len
                    ),
                }
            )
        else:
            context_dict = _WF_EXEC_LOGGING_CONTEXT_VAR.get()
            for key in keys:
                if key in context_dict:
                    del context_dict[key]  # type: ignore

    def get_value(self, key: str) -> Any:
        context_dict = _get_execution_context()
        return context_dict.get(key, None)

    def filter(self, record: logging.LogRecord) -> Literal[True]:  # noqa: A003
        context_dict = _get_execution_context()

        record.currently_executed_transformation_id = context_dict.get(  # type: ignore
            "currently_executed_transformation_id", None
        )
        record.currently_executed_transformation_name = context_dict.get(  # type: ignore
            "currently_executed_transformation_name", None
        )
        record.currently_executed_transformation_tag = context_dict.get(  # type: ignore
            "currently_executed_transformation_tag", None
        )
        record.currently_executed_transformation_type = context_dict.get(  # type: ignore
            "currently_executed_transformation_type", None
        )
        record.currently_executed_operator_hierarchical_id = context_dict.get(  # type: ignore
            "currently_executed_operator_hierarchical_id", None
        )
        record.currently_executed_operator_hierarchical_name = context_dict.get(  # type: ignore
            "currently_executed_operator_hierarchical_name", None
        )
        record.currently_executed_job_id = context_dict.get(  # type: ignore
            "currently_executed_job_id", None
        )

        # UUID to str since some opentelemetry frameworks cannot serialize UUID
        record.currently_executed_job_id = (  # type: ignore
            str(record.currently_executed_job_id) if record.currently_executed_job_id else None  # type: ignore
        )
        return True


execution_context_filter = ExecutionContextFilter()


class ComponentCodeLogHandler(logging.Handler):
    """Gathering of user component code logs

    A logging handler that appends to a list in the key "gathered_component_code_logs"
    in the execution context.

    This handler is assumed to be applied to the logger at base_module_path.

    The gathered logs will be send back in execution response objects.
    """

    def ensure_list_in_context(self) -> None:
        exec_context = _get_execution_context()

        # initialize log record list if necessary:
        if "gathered_component_code_logs" not in exec_context:
            exec_context["gathered_component_code_logs"] = deque(
                maxlen=get_config().user_component_code_logs_max_len
            )

    def emit(self, record: logging.LogRecord) -> None:
        """Append log to execution context"""

        self.ensure_list_in_context()
        exec_context = _get_execution_context()
        exec_context["gathered_component_code_logs"].append(record)

    def clear(self) -> None:
        """Clear all stored records."""

        self.ensure_list_in_context()

        exec_context = _get_execution_context()
        exec_context["gathered_component_code_logs"].clear()

    def get_records(self) -> deque[logging.LogRecord]:
        """Get all stored records."""

        self.ensure_list_in_context()
        exec_context = _get_execution_context()

        return exec_context["gathered_component_code_logs"]


def _get_job_id_context() -> dict[str, str | None | UUID]:
    try:
        return _JOB_ID_LOGGING_CONTEXT_VAR.get()
    except LookupError:
        _JOB_ID_LOGGING_CONTEXT_VAR.set({})
        return _JOB_ID_LOGGING_CONTEXT_VAR.get()


class JobIdContextFilter(logging.Filter):
    """Filter to enrich log records with execution environment information"""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.currently_executed_job_id = None
        super().__init__(*args, **kwargs)

    def bind_context(self, **kwargs: Any) -> None:
        _get_job_id_context().update(kwargs)

    def unbind_context(self, *args: str) -> None:
        """Remove entries with provided keys from context"""
        ctx_dict = _get_job_id_context()
        for key in args:
            ctx_dict.pop(key, None)

    def clear_context(self) -> None:
        _JOB_ID_LOGGING_CONTEXT_VAR.set({})

    def get_value(self, key: str) -> str | None | UUID:
        context_dict = _get_job_id_context()
        return context_dict.get(key, None)

    def filter(self, record: logging.LogRecord) -> Literal[True]:  # noqa: A003
        context_dict = _get_job_id_context()

        record.currently_executed_job_id = context_dict.get(  # type: ignore
            "currently_executed_job_id", None
        )
        # UUID to str since some opentelemetry frameworks cannot serialize UUID
        record.currently_executed_job_id = (  # type: ignore
            str(record.currently_executed_job_id) if record.currently_executed_job_id else None  # type: ignore
        )
        return True


job_id_context_filter = JobIdContextFilter()


def logrecord_to_simplified_log_record(record: logging.LogRecord) -> SimplifiedLogRecord:
    dt_created = datetime.datetime.fromtimestamp(record.created, tz=datetime.timezone.utc)

    log_level = record.levelname or str(record.levelno)
    line_no = record.lineno

    # applies formatting args:
    message = record.getMessage() if hasattr(record, "getMessage") else str(record.msg)

    tr_id = (
        UUID(record.currently_executed_transformation_id)
        if hasattr(record, "currently_executed_transformation_id")
        else None
    )
    tr_name = (
        record.currently_executed_transformation_name
        if hasattr(record, "currently_executed_transformation_name")
        else None
    )
    tr_tag = (
        record.currently_executed_transformation_tag
        if hasattr(record, "currently_executed_transformation_tag")
        else None
    )

    tr_type = (
        record.currently_executed_transformation_type
        if hasattr(record, "currently_executed_transformation_type")
        else None
    )

    operator_hierarchical_name = (
        record.currently_executed_operator_hierarchical_name
        if hasattr(record, "currently_executed_operator_hierarchical_name")
        else None
    )
    operator_hierarchical_id = (
        record.currently_executed_operator_hierarchical_id
        if hasattr(record, "currently_executed_operator_hierarchical_id")
        else None
    )

    return SimplifiedLogRecord(
        timestamp=dt_created,
        log_level=log_level,
        lineno=line_no,
        message=message,
        tr_id=tr_id,
        tr_name=tr_name,
        tr_tag=tr_tag,
        tr_type=tr_type,
        operator_hierarchical_name=operator_hierarchical_name,
        operator_hierarchical_id=operator_hierarchical_id,
    )

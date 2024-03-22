import contextvars
import datetime
import json
import logging
from typing import Any, Literal
from uuid import UUID

import numpy as np

_WF_EXEC_LOGGING_CONTEXT_VAR: contextvars.ContextVar[dict] = contextvars.ContextVar(
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


def _get_execution_context() -> dict[str, str | None]:
    try:
        return _WF_EXEC_LOGGING_CONTEXT_VAR.get()
    except LookupError:
        _WF_EXEC_LOGGING_CONTEXT_VAR.set({})
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
        super().__init__(*args, **kwargs)

    def bind_context(self, **kwargs: Any) -> None:
        _get_execution_context().update(kwargs)

    def unbind_context(self, *args: str) -> None:
        """Remove entries with provided keys from context"""
        ctx_dict = _get_execution_context()
        for key in args:
            ctx_dict.pop(key, None)

    def clear_context(self) -> None:
        _WF_EXEC_LOGGING_CONTEXT_VAR.set({})

    def get_value(self, key: str) -> str | None:
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
        return True


execution_context_filter = ExecutionContextFilter()


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
        _WF_EXEC_LOGGING_CONTEXT_VAR.set({})

    def get_value(self, key: str) -> str | None | UUID:
        context_dict = _get_job_id_context()
        return context_dict.get(key, None)

    def filter(self, record: logging.LogRecord) -> Literal[True]:  # noqa: A003
        context_dict = _get_job_id_context()

        record.currently_executed_job_id = context_dict.get(  # type: ignore
            "currently_executed_job_id", None
        )
        return True


job_id_context_filter = JobIdContextFilter()

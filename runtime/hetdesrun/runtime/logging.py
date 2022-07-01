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


class MinimallyMoreCapableJsonEncoder(json.JSONEncoder):
    """Additionally handles datetimes and UUIDs

    Usage:
        json.dumps(object_to_serialize, cls=MinimallyMoreCapableJsonEncoder)

    """

    def default(self, obj: Any) -> Any:  # pylint: disable=arguments-renamed
        if isinstance(obj, UUID):
            # if the obj is uuid, we simply return the value of uuid
            return obj.hex

        if isinstance(obj, datetime.datetime):
            return obj.isoformat()

        if isinstance(obj, np.ndarray):
            return obj.tolist()

        return json.JSONEncoder.default(self, obj)


def _get_context() -> dict:
    try:
        return _WF_EXEC_LOGGING_CONTEXT_VAR.get()
    except LookupError:
        _WF_EXEC_LOGGING_CONTEXT_VAR.set({})
        return _WF_EXEC_LOGGING_CONTEXT_VAR.get()


class ExecutionContextFilter(logging.Filter):
    """Filter to enrich log records with execution environment information"""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.currently_executed_node_instance = None
        self.currently_executed_component = None
        super().__init__(*args, **kwargs)

    def bind_context(self, **kwargs: Any) -> None:  # pylint: disable=no-self-use
        _get_context().update(kwargs)

    def unbind_context(self, *args: str) -> None:  # pylint: disable=no-self-use
        """Remove entries with provided keys from context"""
        ctx_dict = _get_context()
        for key in args:
            ctx_dict.pop(key, None)

    def clear_context(self) -> None:  # pylint: disable=no-self-use
        _WF_EXEC_LOGGING_CONTEXT_VAR.set({})

    def filter(self, record: logging.LogRecord) -> Literal[True]:
        context_dict = _get_context()

        record.currently_executed_instance_id = context_dict.get(  # type: ignore
            "currently_executed_instance_id", None
        )
        record.currently_executed_component_id = context_dict.get(  # type: ignore
            "currently_executed_component_id", None
        )
        record.currently_executed_component_node_name = context_dict.get(  # type: ignore
            "currently_executed_component_node_name", None
        )
        record.job_id = context_dict.get("job_id", None)  # type: ignore
        return True


execution_context_filter = ExecutionContextFilter()

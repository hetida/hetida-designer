import contextvars
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from pydantic import BaseModel, Field, field_validator

from hdutils import PlotTargetSettings


class ExecutionContext(BaseModel):
    currently_executed_transformation_id: str
    currently_executed_transformation_name: str
    currently_executed_transformation_tag: str
    currently_executed_transformation_type: str
    currently_executed_operator_hierarchical_id: str
    currently_executed_operator_hierarchical_name: str


class HierarchyObject(BaseModel):
    type: str | None = None
    id: str | None = None
    node_id: str | None = None
    parent_node_id: str | None = None
    hierarchy_display_path: str | None = None
    name: str | None = None
    tenant_id: str | None = None
    tenant_name: str | None = None


class TimeInterval(BaseModel):
    timestampFrom: str | None = None
    timestampTo: str | None = None


class RuntimeExecutionContext(BaseModel):
    """Context that is available during execution in the runtime

    May contain general information needed by components from the invoking
    execution request, especially as fallback or default if no direct / explicit
    information is available via inputs / filters etc.
    """

    plot_target_settings: PlotTargetSettings = Field(default_factory=PlotTargetSettings)

    hierarchy_object: HierarchyObject = Field(
        default_factory=HierarchyObject,
        description="Additional information on a hierarchy from which a trafo is executed",
    )

    global_time_interval: TimeInterval = Field(
        default_factory=TimeInterval,
        description=(
            "A global time interval that should be assumed if explicit time interval"
            " information is missing"
        ),
    )

    @field_validator(
        "plot_target_settings", "hierarchy_object", "global_time_interval", mode="before"
    )
    @classmethod
    def handle_null_fields(cls, v: Any) -> Any:
        """Allow to initialize explicitely with null/None

        Fields should not be optional / nullable typed and always be proper objects,
        but the case that null / None is provided should just call the default_factory
        and provide the default values.
        """
        if v is None:
            return {}  # will be passed to default_factory
        return v


_RUNTIME_EXECUTION_CONTEXT_VAR: contextvars.ContextVar[RuntimeExecutionContext] = (
    contextvars.ContextVar("runtime_execution_context")
)


def get_runtime_exec_context() -> RuntimeExecutionContext:
    try:
        return _RUNTIME_EXECUTION_CONTEXT_VAR.get()
    except LookupError:
        _RUNTIME_EXECUTION_CONTEXT_VAR.set(RuntimeExecutionContext())
        return _RUNTIME_EXECUTION_CONTEXT_VAR.get()


def set_runtime_exec_context(runtime_exec_context: RuntimeExecutionContext) -> None:
    _RUNTIME_EXECUTION_CONTEXT_VAR.set(runtime_exec_context)


def get_hierarchy_object_info() -> HierarchyObject:
    runtime_context = get_runtime_exec_context()
    return runtime_context.hierarchy_object


def get_global_time_interval_info() -> TimeInterval:
    runtime_context = get_runtime_exec_context()
    return runtime_context.global_time_interval


_DISCARDED_OUTPUTS_CONTEXT_VAR: contextvars.ContextVar[frozenset[str]] = contextvars.ContextVar(
    "discarded_outputs", default=frozenset()
)


@contextmanager
def discarded_outputs_context(discarded_outputs: frozenset[str]) -> Generator[None]:
    """Provide the discarded outputs of the currently executed component"""
    token = _DISCARDED_OUTPUTS_CONTEXT_VAR.set(discarded_outputs)
    try:
        yield
    finally:
        _DISCARDED_OUTPUTS_CONTEXT_VAR.reset(token)


def output_is_discarded(output_name: str) -> bool:
    """Whether the value of an output of the currently executed component is discarded

    An output is discarded if its value is not used anywhere in the current execution: It is
    not linked to an operator input and every workflow output it is exposed as is wired to the
    drop adapter or, if pure plot operators are not run, to the plot adapter.

    Components can use this to skip expensive computations for discarded outputs, e.g. plots,
    and return a placeholder like {} or None instead.

    Outside of a workflow execution in the runtime, e.g. in unit tests of components,
    no output is discarded.
    """
    return output_name in _DISCARDED_OUTPUTS_CONTEXT_VAR.get()

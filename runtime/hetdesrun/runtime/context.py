import contextvars

from pydantic import BaseModel, Field

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


class TimeInterval(BaseModel):
    timestampFrom: str | None = None
    timestampTo: str | None = None


class RuntimeExecutionContext(BaseModel):
    """Context that is available during execution in the runtime

    May contain general information needed by components from the invoking
    execution request.
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

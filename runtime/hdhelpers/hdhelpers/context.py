import contextvars

from pydantic import BaseModel, Field

from hdhelpers.plot_target_settings import PlotTargetSettings


class ExecutionContext(BaseModel):
    currently_executed_transformation_id: str
    currently_executed_transformation_name: str
    currently_executed_transformation_tag: str
    currently_executed_transformation_type: str
    currently_executed_operator_hierarchical_id: str
    currently_executed_operator_hierarchical_name: str


class RuntimeExecutionContext(BaseModel):
    """Context that is available during execution in the runtime

    May contain general information needed by components from the invoking
    execution request.
    """

    plot_target_settings: PlotTargetSettings = Field(default_factory=PlotTargetSettings)


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

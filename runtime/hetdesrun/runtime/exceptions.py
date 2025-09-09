from typing import Any

from hetdesrun.runtime.context import ExecutionContext


class RuntimeExecutionError(Exception):
    """Highest Level Exception for Runtime Execution"""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.currently_executed_transformation_id: str = "UNKNOWN"
        self.currently_executed_transformation_name: str = "UNKNOWN"
        self.currently_executed_transformation_tag: str = "UNKNOWN"
        self.currently_executed_transformation_type: str = "UNKNOWN"
        self.currently_executed_hierarchical_operator_id: str = "UNKNOWN"
        self.currently_executed_hierarchical_operator_name: str = "UNKNOWN"
        self.currently_executed_job_id: str = "UNKNOWN"
        super().__init__(*args, **kwargs)

    def set_context(
        self, context: ExecutionContext, job_id: str = "UNKNOWN"
    ) -> "RuntimeExecutionError":
        self.currently_executed_transformation_id = context.currently_executed_transformation_id
        self.currently_executed_transformation_name = context.currently_executed_transformation_name
        self.currently_executed_transformation_tag = context.currently_executed_transformation_tag
        self.currently_executed_transformation_type = context.currently_executed_transformation_type
        self.currently_executed_hierarchical_operator_id = (
            context.currently_executed_operator_hierarchical_id
        )
        self.currently_executed_hierarchical_operator_name = (
            context.currently_executed_operator_hierarchical_name
        )
        self.currently_executed_job_id = job_id
        return self


class DAGProcessingError(RuntimeExecutionError):
    """Failure of DAG processing

    Should be raised if for example the graph has cycles.
    """


class ComponentException(RuntimeExecutionError):
    """Exception to re-raise exceptions with error code raised in the component code."""

    __is_hetida_designer_exception__ = True

    def __init__(
        self,
        *args: Any,
        error_code: int | str = "",
        extra_information: dict | None = None,
        **kwargs: Any,
    ) -> None:
        if not isinstance(error_code, int | str):
            raise ValueError("The ComponentException.error_code must be int or string!")
        self.error_code = error_code
        self.extra_information = extra_information
        super().__init__(*args, **kwargs)


class ComponentInputValidationException(ComponentException):
    """In code input validation failures"""

    def __init__(
        self,
        *args: Any,
        invalid_component_inputs: list[str],
        error_code: int | str = "",
        **kwargs: Any,
    ) -> None:
        super().__init__(
            *args,
            error_code=error_code,
            extra_information={"invalid_component_inputs": invalid_component_inputs},
            **kwargs,
        )


class UnexpectedComponentException(RuntimeExecutionError):
    """Exception to be re-raised in case of uncaught exceptions during component execution."""


class MissingOutputDataError(RuntimeExecutionError):
    """Exception in case of missing output data from other component"""


class WorkflowOutputValidationError(RuntimeExecutionError):
    """Workflow Output validation failed"""


class WorkflowInputDataValidationError(RuntimeExecutionError):
    """Workflow Input validation failed"""


class CircularDependency(DAGProcessingError):
    """During execution a circular dependency was detected"""


class MissingOutputException(RuntimeExecutionError):
    """During execution a referenced output is missing on another node's result"""


class MissingInputSource(RuntimeExecutionError):
    """During execution a required input is missing on the currently executed node"""

from hetdesrun.runtime.context import ExecutionContext


class RuntimeExecutionError(Exception):
    """Highest Level Exception for Runtime Execution"""

    def __init__(self, *args, **kwargs):  # type: ignore
        self.currently_executed_transformation_id = None
        self.currently_executed_transformation_name = None
        self.currently_executed_transformation_type = None
        self.currently_executed_hierarchical_operator_id = None
        self.currently_executed_hierarchical_operator_name = None
        self.currently_executed_job_id = None
        super().__init__(*args, **kwargs)

    def set_context(
        self,
        context: ExecutionContext,
    ) -> "RuntimeExecutionError":
        self.currently_executed_transformation_id = (
            context.currently_executed_transformation_id
        )
        self.currently_executed_transformation_name = (
            context.currently_executed_transformation_name
        )
        self.currently_executed_transformation_type = (
            context.currently_executed_transformation_type
        )
        self.currently_executed_hierarchical_operator_id = (
            context.currently_executed_operator_hierarchical_id
        )
        self.currently_executed_hierarchical_operator_name = (
            context.currently_executed_operator_hierarchical_name
        )
        self.currently_executed_job_id = context.currently_executed_job_id
        return self


class DAGProcessingError(RuntimeExecutionError):
    """Failure of DAG processing

    Should be raised if for example the graph has cycles.
    """


class UncaughtComponentException(RuntimeExecutionError):
    """Exception to be re-raised in case of uncaught exceptions during component execution."""


class MissingOutputDataError(RuntimeExecutionError):
    """Exception in case of missing output data from other component"""


class ComponentDataValidationError(RuntimeExecutionError):
    """Input or Output validation failures"""


class WorkflowOutputValidationError(RuntimeExecutionError):
    """Workflow Output validation failed"""


class WorkflowInputDataValidationError(RuntimeExecutionError):
    """Workflow Output validation failed"""


class CircularDependency(DAGProcessingError):
    """During execution a circular dependency was detected"""


class MissingOutputException(MissingOutputDataError):
    """During execution a referenced output is missing on another node's result"""


class MissingInputSource(RuntimeExecutionError):
    """During execution a required input is missing on the currently executed node"""

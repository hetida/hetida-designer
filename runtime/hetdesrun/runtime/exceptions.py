class RuntimeExecutionError(Exception):
    """Highest Level Exception for Runtime Execution"""

    def __init__(self, *args, **kwargs):  # type: ignore
        self.currently_executed_node_instance = None
        self.currently_executed_component = None
        super().__init__(*args, **kwargs)

    def set_context(
        self, node_instance_id: str, operator_name: str
    ) -> "RuntimeExecutionError":
        self.currently_executed_node_instance = node_instance_id
        self.currently_executed_component = operator_name
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

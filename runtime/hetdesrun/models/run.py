"""Models for runtime execution endpoint"""


import datetime
import traceback
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, root_validator, validator

from hetdesrun.datatypes import AdvancedTypesOutputSerializationConfig
from hetdesrun.models.base import Result
from hetdesrun.models.code import CodeModule, NonEmptyValidStr, ShortNonEmptyValidStr
from hetdesrun.models.component import ComponentRevision
from hetdesrun.models.wiring import OutputWiring, WorkflowWiring
from hetdesrun.models.workflow import WorkflowNode
from hetdesrun.runtime.exceptions import ComponentException, RuntimeExecutionError
from hetdesrun.utils import Type, check_explicit_utc

HIERARCHY_SEPARATOR = "\\"


class ExecutionEngine(Enum):
    # Currently only built-in execution engine
    Plain = "plain"


class PerformanceMeasuredStep(BaseModel):
    name: str
    start: datetime.datetime | None = None
    end: datetime.datetime | None = None
    duration: datetime.timedelta | None = None

    @classmethod
    def create_and_begin(cls, name: str) -> "PerformanceMeasuredStep":
        new_step = cls(name=name)
        new_step.begin()
        return new_step

    @validator("start")
    def start_utc_datetime(cls, start):  # type: ignore
        if not check_explicit_utc(start):
            raise ValueError("start datetime for measurement must be explicit utc")
        return start

    @validator("end")
    def end_utc_datetime(cls, end):  # type: ignore
        if not check_explicit_utc(end):
            raise ValueError("end datetime for measurement must be explicit utc")
        return end

    def begin(self) -> None:
        self.start = datetime.datetime.now(datetime.timezone.utc)

    def stop(self) -> None:
        if self.start is None:
            raise ValueError(
                f"Cannot stop measurement {self.name} if it was not started before!"
            )

        self.end = datetime.datetime.now(datetime.timezone.utc)
        self.duration = self.end - self.start


class AllMeasuredSteps(BaseModel):
    internal_full: PerformanceMeasuredStep | None = None
    prepare_execution_input: PerformanceMeasuredStep | None = None
    run_execution_input: PerformanceMeasuredStep | None = None
    runtime_service_handling: PerformanceMeasuredStep | None = None
    pure_execution: PerformanceMeasuredStep | None = None
    load_data: PerformanceMeasuredStep | None = None
    send_data: PerformanceMeasuredStep | None = None


class ConfigurationInput(BaseModel):
    """Options changing how a workflow will be executed"""

    name: str | None = None
    engine: ExecutionEngine = Field(
        ExecutionEngine.Plain,
        description="one of "
        + ", ".join(['"' + x.value + '"' for x in list(ExecutionEngine)]),
        example=ExecutionEngine.Plain,
    )
    run_pure_plot_operators: bool = Field(
        True,
        description=(
            "Whether operators marked as Plotting component should be actually run. "
            "If False their (then only) PlotlyJson Outputs will instead be set directly "
            "to empty dictionaries."
        ),
    )
    return_individual_node_results: bool = False


class WorkflowExecutionInput(BaseModel):
    code_modules: list[CodeModule] = Field(
        ..., description="The code modules which are used/referenced by the components."
    )
    components: list[ComponentRevision] = Field(
        ...,
        title="Used components",
        description="List of References to all used elementary components",
    )
    workflow: WorkflowNode = Field(
        ...,
        title="Workflow Root Node",
        description="A Workflow with all its components and sub workflows",
    )
    configuration: ConfigurationInput = Field(
        ..., description="Configuration for the open ends of a workflow"
    )

    workflow_wiring: WorkflowWiring = Field(
        ..., description=("Note that also workflow_wiring can provide inputs directly.")
    )

    job_id: UUID = Field(default_factory=uuid4)

    @validator("components")
    def components_unique(
        cls, components: list[ComponentRevision]
    ) -> list[ComponentRevision]:
        if len({c.uuid for c in components}) != len(components):
            raise ValueError("Components not unique!")
        return components

    @validator("code_modules")
    def code_modules_unique(cls, code_modules: list[CodeModule]) -> list[CodeModule]:
        if len({c.uuid for c in code_modules}) != len(code_modules):
            raise ValueError("Code Modules not unique!")
        return code_modules

    @root_validator(skip_on_failure=True)
    def check_wiring_complete(cls, values: dict) -> dict:
        """Every (non-constant) Workflow input/output must be wired

        Checks whether there is a wiring for every non-constant workflow input
        and for every workflow output.
        """

        try:
            wiring: WorkflowWiring = values["workflow_wiring"]
            workflow: WorkflowNode = values["workflow"]
        except KeyError as e:
            raise ValueError(
                "Cannot check if wiring is complete if "
                "one of the attributes 'wiring' or 'workflow' is missing!"
            ) from e

        # Check that every Workflow Input is wired:
        wired_input_names = {
            inp_wiring.workflow_input_name for inp_wiring in wiring.input_wirings
        }
        dynamic_required_wf_inputs = [
            wfi
            for wfi in workflow.inputs
            if wfi.constant is False and wfi.default is False
        ]
        for wf_input in dynamic_required_wf_inputs:
            if not wf_input.name in wired_input_names:
                raise ValueError(
                    f"Wiring Incomplete: Workflow Input {wf_input.name} has no wiring!"
                )

        dynamic_optional_wf_inputs = [
            wfi
            for wfi in workflow.inputs
            if wfi.constant is False and wfi.default is True
        ]
        if len(wired_input_names) > len(dynamic_required_wf_inputs) + len(
            dynamic_optional_wf_inputs
        ):
            raise ValueError("Too many input wirings provided!")

        wired_output_names = {
            outp_wiring.workflow_output_name for outp_wiring in wiring.output_wirings
        }

        for wf_output in workflow.outputs:
            if not wf_output.name in wired_output_names:
                # Automatically add missing output wirings (make them direct provisioning outputs)
                wiring.output_wirings.append(
                    OutputWiring(
                        workflow_output_name=wf_output.name,
                        adapter_id=1,
                    )
                )

        if len(wired_output_names) > len(workflow.outputs):
            raise ValueError("Too many output wirings provided!")

        return values

    Config = AdvancedTypesOutputSerializationConfig  # enable Serialization of some advanced types


class TransformationInfo(BaseModel):
    id: str  # noqa: A003
    name: NonEmptyValidStr
    tag: ShortNonEmptyValidStr
    type: Type  # noqa: A003


class HierarchyInWorkflow(BaseModel):
    by_name: list[NonEmptyValidStr]
    by_id: list[UUID]

    @classmethod
    def from_hierarchy_strings(
        cls, hierarchical_name_string: str, hierarchical_id_string: str
    ) -> "HierarchyInWorkflow":
        if (
            hierarchical_name_string.count(HIERARCHY_SEPARATOR) < 2
            or hierarchical_id_string.count(HIERARCHY_SEPARATOR) < 2
        ):
            raise ValueError(
                f'The number of "{HIERARCHY_SEPARATOR}" occurences in '
                f'hierarchical name string "{hierarchical_name_string}" or '
                f'hierarchical id string "{hierarchical_id_string}" is < 2 and thus too small!'
            )
        return HierarchyInWorkflow(
            by_name=hierarchical_name_string.split(HIERARCHY_SEPARATOR)[1:-1],
            by_id=[
                UUID(operator_id)
                for operator_id in hierarchical_id_string.split(HIERARCHY_SEPARATOR)[
                    1:-1
                ]
            ],
        )


class OperatorInfo(BaseModel):
    transformation_info: TransformationInfo
    hierarchy_in_workflow: HierarchyInWorkflow

    @classmethod
    def from_runtime_execution_error(
        cls, error: RuntimeExecutionError
    ) -> "OperatorInfo":
        return OperatorInfo(
            transformation_info=TransformationInfo(
                id=error.currently_executed_transformation_id,
                name=error.currently_executed_transformation_name,
                tag=error.currently_executed_transformation_tag,
                type=error.currently_executed_transformation_type,
            ),
            hierarchy_in_workflow=HierarchyInWorkflow.from_hierarchy_strings(
                hierarchical_name_string=error.currently_executed_hierarchical_operator_name,
                hierarchical_id_string=error.currently_executed_hierarchical_operator_id,
            ),
        )


class Trace(BaseModel):
    file_name: str
    function_name: str
    line_number: int
    line_of_code: str


class ProcessStage(str, Enum):
    """ "Stages of the execution process."""

    TRANSFORMING_TRANSFORMATION_TO_RUNTIME_OBJECT = (
        "TRANSFORMING_TRANSFORMATION_TO_RUNTIME_OBJECT"
    )
    PARSING_CONSTANT_AND_DEFAULT_INPUT_DATA = "PARSING_CONSTANT_AND_DEFAULT_INPUT_DATA"
    LOADING_DATA_FROM_INPUT_WIRING = "LOADING_DATA_FROM_INPUT_WIRING"
    PARSING_LOADED_INPUT_DATA = "PARSING_LOADED_INPUT_DATA"
    EXECUTING_COMPONENT_CODE = "EXECUTING_COMPONENT_CODE"
    SENDING_DATA_TO_OUTPUT_WIRING = "SENDING_DATA_TO_OUTPUT_WIRING"
    ENCODING_RESULTS_TO_JSON = "ENCODING_RESULTS_TO_JSON"


class WorkflowExecutionError(BaseModel):
    type: str  # noqa: A003
    message: str
    error_code: int | str | None = None
    process_stage: ProcessStage | None = None
    operator_info: OperatorInfo | None = None


def traces_from_exception(exception: Exception) -> list[Trace]:
    traces = []
    tb = exception.__traceback__
    while tb is not None:
        traces.append(
            Trace(
                file_name=tb.tb_frame.f_code.co_filename,
                function_name=tb.tb_frame.f_code.co_name,
                line_number=tb.tb_lineno,
                line_of_code="",
            )
        )
        tb = tb.tb_next
    return traces


class WorkflowExecutionInfo(BaseModel):
    error: WorkflowExecutionError | None = Field(None, description="error string")
    output_results_by_output_name: dict[str, Any] = Field(
        ...,
        description="Results at the workflow outputs as a dictionary by name of workflow output",
    )
    traceback: str | None = Field(None, description="traceback")
    traces: list[Trace] | None = Field(None, description="traceback as formatted list")
    job_id: UUID

    measured_steps: AllMeasuredSteps = AllMeasuredSteps()

    @classmethod
    def from_exception(
        cls, exception: Exception, process_stage: ProcessStage, job_id: UUID
    ) -> "WorkflowExecutionInfo":
        return WorkflowExecutionInfo(
            error=WorkflowExecutionError(
                type=type(exception).__name__,
                message=str(exception),
                error_code=exception.error_code
                if isinstance(exception, ComponentException)
                else None,
                process_stage=process_stage,
                operator_info=OperatorInfo.from_runtime_execution_error(exception)
                if isinstance(exception, RuntimeExecutionError)
                else None,
            ),
            traceback=traceback.format_exc(),
            traces=traces_from_exception(exception),
            output_results_by_output_name={},
            job_id=job_id,
        )

    Config = AdvancedTypesOutputSerializationConfig  # enable Serialization of some advanced types


class WorkflowExecutionResult(WorkflowExecutionInfo):
    result: Result = Field(
        ...,
        description="one of " + ", ".join(['"' + x.value + '"' for x in list(Result)]),
        example=Result.OK,
    )
    node_results: str | None = Field(
        None,
        description=(
            "Individual results of all executed nodes as concatenated str."
            " This uses str() on the Python objects which may be an abbreviated representation"
            " (e.g. Pandas objects). Will only be used if the corresponding configuration flag is"
            " set to true."
        ),
    )

    @classmethod
    def from_exception(
        cls,
        exception: Exception,
        process_stage: ProcessStage,
        job_id: UUID,
        node_results: str | None = None,
    ) -> "WorkflowExecutionResult":
        return WorkflowExecutionResult(
            **super().from_exception(exception, process_stage, job_id).dict(),
            result="failure",
            node_results=node_results,
        )

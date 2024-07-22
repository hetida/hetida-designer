"""Models for runtime execution endpoint"""

import datetime
import traceback as tb
from enum import Enum, StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, root_validator, validator

from hetdesrun.datatypes import AdvancedTypesOutputSerializationConfig
from hetdesrun.models.base import Result
from hetdesrun.models.code import CodeModule, NonEmptyValidStr, ShortNonEmptyValidStr
from hetdesrun.models.component import ComponentRevision
from hetdesrun.models.repr_reference import ReproducibilityReference
from hetdesrun.models.wiring import OutputWiring, WorkflowWiring
from hetdesrun.models.workflow import WorkflowNode
from hetdesrun.reference_context import (
    get_deepcopy_of_reproducibility_reference_context,
)
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
            raise ValueError(f"Cannot stop measurement {self.name} if it was not started before!")

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
        description="one of " + ", ".join(['"' + x.value + '"' for x in list(ExecutionEngine)]),
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
    trafo_id: UUID = Field(
        ...,
        description=(
            "The uuid of the original (root) transformation revision that is to be "
            "executed. Note that this does not have to be equal to the highest level WorkflowNode "
            " id in the workflow field, since for example components get wrapped. This is primarily"
            " used for logging and providing context information."
        ),
    )

    @validator("components")
    def components_unique(cls, components: list[ComponentRevision]) -> list[ComponentRevision]:
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
        """Every (non-constant) required Workflow input/output must be wired

        Checks whether there is a wiring for every non-constant required workflow input
        and for every workflow output and whether there is a non-constant workflow input for each
        input wiring and a workflow output for each output wiring.
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
        wired_input_names = {inp_wiring.workflow_input_name for inp_wiring in wiring.input_wirings}
        dynamic_required_wf_input_names = [
            wfi.name for wfi in workflow.inputs if wfi.constant is False and wfi.default is False
        ]
        for wf_input_name in dynamic_required_wf_input_names:
            if not wf_input_name in wired_input_names:
                raise ValueError(
                    f"Wiring Incomplete: Workflow Input '{wf_input_name}' has no wiring!"
                )

        dynamic_optional_wf_input_names = [
            wfi.name for wfi in workflow.inputs if wfi.constant is False and wfi.default is True
        ]
        for wired_input_name in wired_input_names:
            if (
                wired_input_name
                not in dynamic_required_wf_input_names + dynamic_optional_wf_input_names
            ):
                raise ValueError(
                    f"Wiring does not match: There is no workflow input '{wired_input_name}'!"
                )

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

        wf_output_names = [wfo.name for wfo in workflow.outputs]
        for wired_output_name in wired_output_names:
            if wired_output_name not in wf_output_names:
                raise ValueError(
                    f"Wiring does not match: There is no workflow output '{wired_output_name}'!"
                )

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
                for operator_id in hierarchical_id_string.split(HIERARCHY_SEPARATOR)[1:-1]
            ],
        )


class OperatorInfo(BaseModel):
    transformation_info: TransformationInfo
    hierarchy_in_workflow: HierarchyInWorkflow

    @classmethod
    def from_runtime_execution_error(cls, error: RuntimeExecutionError) -> "OperatorInfo":
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


class ErrorLocation(BaseModel):
    file: str
    function_name: str
    line_number: int


class ProcessStage(StrEnum):
    """ "Stages of the execution process."""

    PARSING_WORKFLOW = "PARSING_WORKFLOW"
    LOADING_DATA_FROM_ADAPTERS = "LOADING_DATA_FROM_ADAPTERS"
    PARSING_LOADED_DATA = "PARSING_LOADED_DATA"
    EXECUTING_COMPONENT_CODE = "EXECUTING_COMPONENT_CODE"
    SENDING_DATA_TO_ADAPTERS = "SENDING_DATA_TO_ADAPTERS"
    ENCODING_RESULTS_TO_JSON = "ENCODING_RESULTS_TO_JSON"


class WorkflowExecutionError(BaseModel):
    type: str  # noqa: A003
    error_code: int | str | None = None
    message: str
    extra_information: dict | None = None
    process_stage: ProcessStage | None = None
    operator_info: OperatorInfo | None = None
    location: ErrorLocation


def get_location_of_exception(exception: Exception | BaseException) -> ErrorLocation:
    last_trace = tb.extract_tb(exception.__traceback__)[-1]
    return ErrorLocation(
        file=(last_trace.filename if last_trace.filename != "<string>" else "COMPONENT CODE"),
        function_name=last_trace.name,
        line_number=last_trace.lineno,
    )


class WorkflowExecutionInfo(BaseModel):
    error: WorkflowExecutionError | None = Field(None, description="error string")
    output_results_by_output_name: dict[str, Any] = Field(
        ...,
        description="Results at the workflow outputs as a dictionary by name of workflow output",
    )
    traceback: str | None = Field(None, description="traceback")
    job_id: UUID

    measured_steps: AllMeasuredSteps = AllMeasuredSteps()

    @classmethod
    def from_exception(
        cls,
        exception: Exception,
        process_stage: ProcessStage,
        job_id: UUID,
        cause: BaseException | None,
    ) -> "WorkflowExecutionInfo":
        return WorkflowExecutionInfo(
            error=WorkflowExecutionError(
                type=(type(exception).__name__ if cause is None else type(cause).__name__),
                message=str(exception) if cause is None else str(cause),
                extra_information=(
                    exception.extra_information
                    if isinstance(exception, ComponentException)
                    else None
                ),
                error_code=(
                    exception.error_code if isinstance(exception, ComponentException) else None
                ),
                process_stage=process_stage,
                operator_info=(
                    OperatorInfo.from_runtime_execution_error(exception)
                    if isinstance(exception, RuntimeExecutionError)
                    else None
                ),
                location=(
                    get_location_of_exception(exception)
                    if cause is None
                    else get_location_of_exception(cause)
                ),
            ),
            traceback=tb.format_exc(),
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
    resolved_reproducibility_references: ReproducibilityReference = Field(
        default_factory=get_deepcopy_of_reproducibility_reference_context,
        description="Resolved references to information needed to reproduce an execution result."
        "The provided data can be used to replace data that would usually be produced at runtime.",
    )

    @classmethod
    def from_exception(
        cls,
        exception: Exception,
        process_stage: ProcessStage,
        job_id: UUID,
        cause: BaseException | None = None,
        node_results: str | None = None,
    ) -> "WorkflowExecutionResult":
        # Access the current context to retrieve resolved reproducibility references
        repr_reference = get_deepcopy_of_reproducibility_reference_context()

        return WorkflowExecutionResult(
            **super().from_exception(exception, process_stage, job_id, cause).dict(),
            result="failure",
            node_results=node_results,
            resolved_reproducibility_references=repr_reference,
        )

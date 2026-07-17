"""Models for runtime execution endpoint"""

import datetime
import resource
import traceback as tb
from collections import deque
from enum import Enum, StrEnum
from types import TracebackType
from typing import Any, Self
from uuid import UUID, uuid4

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SerializationInfo,
    ValidationInfo,
    field_serializer,
    field_validator,
    model_validator,
)

from hdutils import (
    DataType,
    data_type_map,
    parse_obj_as_type,
    serializer_funcs_by_type,
)
from hetdesrun.models.base import Result
from hetdesrun.models.code import CodeModule, NonEmptyValidStr, ShortNonEmptyValidStr
from hetdesrun.models.component import ComponentRevision
from hetdesrun.models.repr_reference import ReproducibilityReference
from hetdesrun.models.wiring import OutputWiring, WorkflowWiring
from hetdesrun.models.workflow import WorkflowNode
from hetdesrun.reference_context import (
    get_deepcopy_of_reproducibility_reference_context,
)
from hetdesrun.runtime.context import RuntimeExecutionContext
from hetdesrun.runtime.exceptions import ComponentException, RuntimeExecutionError
from hetdesrun.runtime.logging import SimplifiedLogRecord
from hetdesrun.utils import Type, check_explicit_utc
from hetdesrun.webservice.config import get_config

HIERARCHY_SEPARATOR = "\\"


class ExecutionEngine(Enum):
    # Currently only built-in execution engine
    Plain = "plain"


class PerformanceMeasuredStep(BaseModel):
    name: str
    start: datetime.datetime | None = None
    end: datetime.datetime | None = None
    duration: datetime.timedelta | None = None

    model_config = ConfigDict(ser_json_timedelta="float")  # seconds

    @classmethod
    def create_and_begin(cls, name: str) -> PerformanceMeasuredStep:
        new_step = cls(name=name)
        new_step.begin()
        return new_step

    @field_validator("start")
    @classmethod
    def start_utc_datetime(cls, start):  # type: ignore
        if start is not None and not check_explicit_utc(start):
            raise ValueError("start datetime for measurement must be explicit utc")
        return start

    @field_validator("end")
    @classmethod
    def end_utc_datetime(cls, end):  # type: ignore
        if end is not None and not check_explicit_utc(end):
            raise ValueError("end datetime for measurement must be explicit utc")
        return end

    def begin(self) -> None:
        self.start = datetime.datetime.now(datetime.timezone.utc)

    def stop(self, end: datetime.datetime | None = None) -> None:
        if self.start is None:
            raise ValueError(f"Cannot stop measurement {self.name} if it was not started before!")

        self.end = datetime.datetime.now(datetime.timezone.utc) if end is None else end
        self.duration = self.end - self.start

    def __enter__(self) -> Self:
        self.begin()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.stop()


class RuntimeMemoryInfo(BaseModel):
    kb_at_runtime_start: int
    kb_at_runtime_end: int
    kb_diff_end_minus_start: int

    @classmethod
    def complete_now(cls, kb_at_start: int) -> RuntimeMemoryInfo:
        memory_at_runtime_service_end_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        memory_diff_runtime_service_end_minus_start_kb = (
            memory_at_runtime_service_end_kb - kb_at_start
        )
        return cls(
            kb_at_runtime_start=kb_at_start,
            kb_at_runtime_end=memory_at_runtime_service_end_kb,
            kb_diff_end_minus_start=memory_diff_runtime_service_end_minus_start_kb,
        )


class AllMeasuredSteps(BaseModel):
    internal_full: PerformanceMeasuredStep = PerformanceMeasuredStep(name="internal_full")
    prepare_execution_input: PerformanceMeasuredStep = PerformanceMeasuredStep(
        name="prepare_execution_input"
    )
    run_execution_input: PerformanceMeasuredStep = PerformanceMeasuredStep(
        name="run_execution_input"
    )
    runtime_service_handling: PerformanceMeasuredStep = PerformanceMeasuredStep(
        name="RUNTIME_SERVICE"
    )
    pure_execution: PerformanceMeasuredStep = PerformanceMeasuredStep(
        name="EXECUTING_COMPONENT_CODE"
    )
    load_data: PerformanceMeasuredStep = PerformanceMeasuredStep(name="LOADING_DATA_FROM_ADAPTERS")
    send_data: PerformanceMeasuredStep = PerformanceMeasuredStep(name="SENDING_DATA_TO_ADAPTERS")
    runtime_request_response_parsing: PerformanceMeasuredStep = PerformanceMeasuredStep(
        name="runtime_request_response_parsing"
    )

    pure_runtime_request: PerformanceMeasuredStep = PerformanceMeasuredStep(
        name="pure_runtime_request"
    )
    start_and_wf_parsing: PerformanceMeasuredStep = PerformanceMeasuredStep(
        name="RUNTIME_SERVICE_PURE_WF_PARSING"
    )
    pure_wf_parsing: PerformanceMeasuredStep = PerformanceMeasuredStep(name="pure_wf_parsing")
    constant_providing_and_preps: PerformanceMeasuredStep = PerformanceMeasuredStep(
        name="constant_providing_and_preps"
    )
    backend_calling_runtime_request_start: PerformanceMeasuredStep = PerformanceMeasuredStep(
        name="backend_calling_runtime_request_start"
    )
    runtime_sending_response_start: PerformanceMeasuredStep = PerformanceMeasuredStep(
        name="runtime_sending_response_start"
    )

    loaded_data_info: dict[str, dict[str, Any]] = {}
    result_data_info: dict[str, dict[str, Any]] = {}
    runtime_memory_info: RuntimeMemoryInfo | None = None


class ConfigurationInput(BaseModel):
    """Options changing how a workflow will be executed"""

    name: str | None = None
    engine: ExecutionEngine = Field(
        ExecutionEngine.Plain,
        description="one of " + ", ".join(['"' + x.value + '"' for x in list(ExecutionEngine)]),
        examples=[ExecutionEngine.Plain],
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

    runtime_execution_context: RuntimeExecutionContext = Field(
        default_factory=RuntimeExecutionContext,
        description="General settings to influence aspects of workflow/component execution",
    )

    reproducibility_reference: ReproducibilityReference = Field(
        default_factory=ReproducibilityReference
    )

    @field_validator("components")
    @classmethod
    def components_unique(cls, components: list[ComponentRevision]) -> list[ComponentRevision]:
        if len({c.uuid for c in components}) != len(components):
            raise ValueError("Components not unique!")
        return components

    @field_validator("code_modules")
    @classmethod
    def code_modules_unique(cls, code_modules: list[CodeModule]) -> list[CodeModule]:
        if len({c.uuid for c in code_modules}) != len(code_modules):
            raise ValueError("Code Modules not unique!")
        return code_modules

    @model_validator(mode="after")
    def check_wiring_complete(self) -> Self:
        """Every (non-constant) required Workflow input/output must be wired

        Checks whether there is a wiring for every non-constant required workflow input
        and for every workflow output and whether there is a non-constant workflow input for each
        input wiring and a workflow output for each output wiring.
        """

        wiring: WorkflowWiring = self.workflow_wiring
        workflow: WorkflowNode = self.workflow

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

        return self


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
    ) -> HierarchyInWorkflow:
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
    def from_runtime_execution_error(cls, error: RuntimeExecutionError) -> OperatorInfo:
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
    """Stages of the execution process."""

    PARSING_WORKFLOW = "PARSING_WORKFLOW"
    LOADING_DATA_FROM_ADAPTERS = "LOADING_DATA_FROM_ADAPTERS"
    PARSE_AND_PROVIDE_DATA_AS_CONSTANTS = "PARSE_AND_PROVIDE_DATA_AS_CONSTANTS"
    PARSING_LOADED_DATA = "PARSING_LOADED_DATA"
    EXECUTING_COMPONENT_CODE = "EXECUTING_COMPONENT_CODE"
    ENSURE_RESULT_PARSABLE_AND_SERIALIZABLE = "ENSURE_RESULT_PARSABLE_AND_SERIALIZABLE"
    SENDING_DATA_TO_ADAPTERS = "SENDING_DATA_TO_ADAPTERS"
    ENCODING_RESULTS_TO_JSON = "ENCODING_RESULTS_TO_JSON"
    SERIALIZING_EXEC_RESULT = "SERIALIZING_EXEC_RESULT"
    UNKNOWN = "UNKNOWN"


class WorkflowExecutionError(BaseModel):
    type: str  # noqa: A003
    error_code: int | str | None = None
    message: str
    extra_information: dict | None = None
    process_stage: ProcessStage | None = None
    operator_info: OperatorInfo | None = None
    location: ErrorLocation


def get_location_of_exception(exception: Exception | BaseException) -> ErrorLocation:
    try:
        last_trace = tb.extract_tb(exception.__traceback__)[-1]
    except IndexError:
        return ErrorLocation(file="__UNKNOWN__", function_name="__UNKNOWN__", line_number=-1)
    return ErrorLocation(
        file=last_trace.filename,
        function_name=last_trace.name,
        line_number=last_trace.lineno,
    )


def to_correct_obj_by_datatype(obj: Any, data_type: DataType) -> Any:
    if obj is None:
        return None
    if data_type is None or data_type is DataType.Any:
        return obj

    return parse_obj_as_type(obj, data_type_map[data_type])


class WorkflowExecutionInfo(BaseModel):
    error: WorkflowExecutionError | None = Field(None, description="error string")
    output_types_by_output_name: dict[str, DataType | None] = Field(
        ..., description="types corresponding to results in output_results_by_output_name"
    )
    output_results_by_output_name: dict[str, Any] = Field(
        ...,
        description="Results at the workflow outputs as a dictionary by name of workflow output",
    )

    traceback: str | None = Field(None, description="traceback")
    job_id: UUID
    tr_tag: str
    tr_name: str
    tr_id: UUID

    measured_steps: AllMeasuredSteps = AllMeasuredSteps()

    @classmethod
    def from_exception(
        cls,
        exception: Exception,
        process_stage: ProcessStage,
        job_id: UUID,
        tr_name: str,
        tr_tag: str,
        tr_id: UUID,
        cause: BaseException | None = None,
        measured_steps: AllMeasuredSteps | None = None,
        mem_info: RuntimeMemoryInfo | None = None,
    ) -> WorkflowExecutionInfo:
        if measured_steps is not None and mem_info is not None:
            measured_steps.runtime_memory_info = mem_info
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
            output_types_by_output_name={},
            job_id=job_id,
            tr_name=tr_name,
            tr_tag=tr_tag,
            tr_id=tr_id,
            measured_steps=measured_steps if measured_steps is not None else AllMeasuredSteps(),
        )

    @field_serializer("output_results_by_output_name")
    def serialize_output_result_dict(
        self, output_results_by_output_name: dict[str, Any], info: SerializationInfo
    ) -> dict[str, Any]:
        """Correctly serialize the direct provisioning outputs

        For example Pandas objects should be serialized together with their metadata in
        .attrs field.

        For cases where we know that the content output_results_by_output_name already went
        through this process and is represented as a correct json-serializable dict-like object,
        a serialization context dict can be set containing
        "naive_result_serialization": True

        In this case the complete output_results_by_output_name is taken as is.
        """
        naive_result_serialization = False
        if isinstance(info.context, dict):
            naive_result_serialization = info.context.get("naive_result_serialization", False)

        if naive_result_serialization:
            # return as is
            return output_results_by_output_name

        output_datatypes_by_output_name = self.output_types_by_output_name

        return {
            outp_name: serializer_funcs_by_type.get(
                data_type_map[output_datatypes_by_output_name[outp_name]], lambda x: x
            )(obj)
            for outp_name, obj in output_results_by_output_name.items()
        }

    @field_validator("output_results_by_output_name")
    @classmethod
    def correct_objects_according_to_output_types(
        cls, output_results_by_output_name: dict[str, Any], info: ValidationInfo
    ) -> dict[str, Any]:
        """Parse direct_provisioning output results

        E.g. Pandas objects are parsed from their json representation including metadata.

        To leave the dict-like json data as-is it is possible to set a validation context
        dictionary with key "result_validation": False.

        This is helpful when the result data should not be processed internally but only
        passed through as is the case when the backend responds the results it got from
        an external runtime service. This
        * avoids an unnecessary serialization / deserialization step
        * ensures that Pandas automatic parsing does not lead to unexpected results / i.e.
          changing the json representation the runtime provided of the object due to
          e.g. automatic datetime inference for index or values.
        """
        result_validation = True
        if isinstance(info.context, dict):
            result_validation = info.context.get("result_validation", True)

        if result_validation:
            output_types_by_output_name = info.data.get("output_types_by_output_name")
            if output_types_by_output_name is None:
                raise ValueError(
                    "Missing output_types_by_output_name, "
                    "cannot validate output_results_by_output_name"
                )

            # Validate; We have a datatype for each output result:
            for outp_name in output_results_by_output_name:
                if not outp_name in output_types_by_output_name:
                    raise ValueError(
                        f"Output with name {outp_name} has no entry in output_types_by_output_name"
                    )
            correct_objects = {
                outp_name: to_correct_obj_by_datatype(obj, output_types_by_output_name[outp_name])
                for outp_name, obj in output_results_by_output_name.items()
            }

            return correct_objects
        return output_results_by_output_name


class WorkflowExecutionResult(WorkflowExecutionInfo):
    result: Result = Field(
        ...,
        description="one of " + ", ".join(['"' + x.value + '"' for x in list(Result)]),  # type: ignore
        examples=[Result.OK],
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

    gathered_component_code_logs: deque[SimplifiedLogRecord] = deque(
        maxlen=get_config().user_component_code_logs_max_len
    )

    @classmethod
    def from_exception(
        cls,
        exception: Exception,
        process_stage: ProcessStage,
        job_id: UUID,
        tr_name: str,
        tr_tag: str,
        tr_id: UUID,
        cause: BaseException | None = None,
        measured_steps: AllMeasuredSteps | None = None,
        mem_info: RuntimeMemoryInfo | None = None,
        node_results: str | None = None,
    ) -> WorkflowExecutionResult:
        # Access the current context to retrieve resolved reproducibility references
        repr_reference = get_deepcopy_of_reproducibility_reference_context()

        wf_exec_info = super().from_exception(
            exception,
            process_stage,
            job_id,
            tr_name=tr_name,
            tr_tag=tr_tag,
            tr_id=tr_id,
            cause=cause,
            measured_steps=measured_steps,
            mem_info=mem_info,
        )

        return WorkflowExecutionResult(
            **wf_exec_info.model_dump(),
            result="failure",
            node_results=node_results,
            resolved_reproducibility_references=repr_reference,
        )


class UnitTestPayload(BaseModel):
    component_code: str
    code_modules: list[CodeModule] = Field(
        default=[],
        description=(
            "Code modules of all components (transitively) imported via import_comp"
            " by the component code under test."
        ),
    )
    components: list[ComponentRevision] = Field(
        default=[],
        description=(
            "Component revisions of all components (transitively) imported via import_comp"
            " by the component code under test."
        ),
    )


class UnitTestResults(BaseModel):
    pytest_stdout_str: str
    pytest_stderr_str: str

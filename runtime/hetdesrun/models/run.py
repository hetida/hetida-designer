"""Models for runtime execution endpoint"""


import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import Field  # pylint: disable=no-name-in-module
from pydantic import BaseModel, root_validator, validator

from hetdesrun.datatypes import AdvancedTypesOutputSerializationConfig
from hetdesrun.models.base import Result
from hetdesrun.models.code import CodeModule
from hetdesrun.models.component import ComponentRevision
from hetdesrun.models.wiring import OutputWiring, WorkflowWiring
from hetdesrun.models.workflow import WorkflowNode
from hetdesrun.utils import check_explicit_utc


class ExecutionEngine(Enum):
    # Currently only built-in execution engine
    Plain = "plain"


class PerformanceMeasuredStep(BaseModel):
    name: str
    start: Optional[datetime.datetime] = None
    end: Optional[datetime.datetime] = None
    duration: Optional[datetime.timedelta] = None

    @classmethod
    def create_and_begin(cls, name: str) -> "PerformanceMeasuredStep":
        new_step = cls(name=name)
        new_step.begin()
        return new_step

    # pylint: disable=no-self-argument
    @validator("start")
    def start_utc_datetime(cls, start):  # type: ignore
        if not check_explicit_utc(start):
            return ValueError("start datetime for measurement must be explicit utc")
        return start

    # pylint: disable=no-self-argument
    @validator("end")
    def end_utc_datetime(cls, end):  # type: ignore
        if not check_explicit_utc(end):
            return ValueError("end datetime for measurement must be explicit utc")
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
    internal_full: Optional[PerformanceMeasuredStep] = None
    prepare_execution_input: Optional[PerformanceMeasuredStep] = None
    run_execution_input: Optional[PerformanceMeasuredStep] = None
    runtime_service_handling: Optional[PerformanceMeasuredStep] = None
    pure_execution: Optional[PerformanceMeasuredStep] = None
    load_data: Optional[PerformanceMeasuredStep] = None
    send_data: Optional[PerformanceMeasuredStep] = None


class ConfigurationInput(BaseModel):
    """Options changing how a workflow will be executed"""

    name: Optional[str] = None
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
    code_modules: List[CodeModule] = Field(
        ..., description="The code modules which are used/referenced by the components."
    )
    components: List[ComponentRevision] = Field(
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

    # pylint: disable=no-self-argument
    @validator("components")
    def components_unique(
        cls, components: List[ComponentRevision]
    ) -> List[ComponentRevision]:
        if len(set(c.uuid for c in components)) != len(components):
            raise ValueError("Components not unique!")
        return components

    # pylint: disable=no-self-argument
    @validator("code_modules")
    def code_modules_unique(cls, code_modules: List[CodeModule]) -> List[CodeModule]:
        if len(set(c.uuid for c in code_modules)) != len(code_modules):
            raise ValueError("Code Modules not unique!")
        return code_modules

    # pylint: disable=no-self-argument
    @root_validator(skip_on_failure=True)
    def check_wiring_type_matches_and_complete(cls, values: dict) -> dict:
        """Every (non-constant) Workflow input/output must be wired

        Checks whether there is a wiring for every non-constant workflow input
        and for every workflow output.
        """

        try:
            wiring = values["workflow_wiring"]
            workflow = values["workflow"]
        except KeyError as e:
            raise ValueError(
                "Cannot check if wiring is complete if "
                "one of the attributes 'wiring' or 'workflow' is missing!"
            ) from e

        # Check that every Workflow Input is wired:
        wired_input_names = set(
            (inp_wiring.workflow_input_name for inp_wiring in wiring.input_wirings)
        )

        non_constant_wf_inputs = [wfi for wfi in workflow.inputs if not wfi.constant]
        for wf_input in non_constant_wf_inputs:
            if not wf_input.name in wired_input_names:
                raise ValueError(
                    f"Wiring Incomplete: Workflow Input {wf_input.name} has no wiring!"
                )
            matched_input_wiring = [
                input_wiring
                for input_wiring in wiring.input_wirings
                if input_wiring.name == wf_input.name
            ][0]
            if wf_input.type != matched_input_wiring.type:
                raise ValueError(
                    f"The type '{matched_input_wiring.type}' of "
                    f"the input wiring '{matched_input_wiring.name}' "
                    f"does not match the type '{wf_input.type}' "
                    f"of the corresponding workflow input '{wf_input.name}'!"
                )

        if len(wired_input_names) > len(non_constant_wf_inputs):
            raise ValueError("Too many input wirings provided!")

        wired_output_names = set(
            (outp_wiring.workflow_output_name for outp_wiring in wiring.output_wirings)
        )

        for wf_output in workflow.outputs:
            if not wf_output.name in wired_output_names:
                # Automatically add missing output wirings (make them direct provisioning outputs)
                wiring.output_wirings.append(
                    OutputWiring(
                        workflow_output_name=wf_output.name,
                        adapter_id=1,
                        type=wf_output.type,
                    )
                )

            matched_output_wiring = [
                output_wiring
                for output_wiring in wiring.output_wirings
                if output_wiring.name == wf_output.name
            ][0]
            if wf_output.type != matched_output_wiring.type:
                raise ValueError(
                    f"The type '{matched_output_wiring.type}' of "
                    f"the input wiring '{matched_output_wiring.name}' "
                    f"does not match the type '{wf_output.type}' "
                    f"of the corresponding workflow input '{wf_output.name}'!"
                )

        if len(wired_output_names) > len(workflow.outputs):
            raise ValueError("Too many output wirings provided!")

        return values

    Config = AdvancedTypesOutputSerializationConfig  # enable Serialization of some advanced types


class WorkflowExecutionResult(BaseModel):
    result: Result = Field(
        ...,
        description="one of " + ", ".join(['"' + x.value + '"' for x in list(Result)]),
        example=Result.OK,
    )

    output_results_by_output_name: Dict[str, Any] = Field(
        ...,
        description="Results at the workflow outputs as a dictionary by name of workflow output",
    )
    node_results: Optional[str] = Field(
        None,
        description=(
            "Individual results of all executed nodes as concatenated str."
            " This uses str() on the Python objects which may be an abbreviated representation"
            " (e.g. Pandas objects). Will only be used if the corresponding configuration flag is"
            " set to true."
        ),
    )
    error: Optional[str] = Field(None, description="error string")
    traceback: Optional[str] = Field(None, description="traceback")
    job_id: UUID

    measured_steps: AllMeasuredSteps = AllMeasuredSteps()

    Config = AdvancedTypesOutputSerializationConfig  # enable Serialization of some advanced types

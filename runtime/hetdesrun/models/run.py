"""Models for runtime execution endpoint"""


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


class ExecutionEngine(Enum):
    # Currently only built-in execution engine
    Plain = "plain"


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

    # pylint: disable=no-self-argument,no-self-use
    @validator("components")
    def components_unique(
        cls, components: List[ComponentRevision]
    ) -> List[ComponentRevision]:
        if len(set(c.uuid for c in components)) != len(components):
            raise ValueError("Components not unique!")
        return components

    # pylint: disable=no-self-argument,no-self-use
    @validator("code_modules")
    def code_modules_unique(cls, code_modules: List[CodeModule]) -> List[CodeModule]:
        if len(set(c.uuid for c in code_modules)) != len(code_modules):
            raise ValueError("Code Modules not unique!")
        return code_modules

    # pylint: disable=no-self-argument,no-self-use
    @root_validator(skip_on_failure=True)
    def check_wiring_complete(cls, values):  # type: ignore
        """Every (non-constant) Workflow input/output must be wired

        Checks whether there is a wiring for every non-constant workflow input
        and for every workflow output.
        """

        wiring: WorkflowWiring = values.get("workflow_wiring")
        workflow: WorkflowNode = values.get("workflow")

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

        if len(wired_input_names) > len(non_constant_wf_inputs):
            raise ValueError("Too many input wirings provided!")

        wired_output_names = set(
            (outp_wiring.workflow_output_name for outp_wiring in wiring.output_wirings)
        )

        for wf_output in workflow.outputs:
            if not wf_output.name in wired_output_names:
                wiring.output_wirings.append(
                    OutputWiring(
                        workflow_output_name=wf_output.name,
                        adapter_id=1,
                    )
                )
        # Automatically add missing wirings for outputs (make them direct provisioning outputs)

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
    Config = AdvancedTypesOutputSerializationConfig  # enable Serialization of some advanced types

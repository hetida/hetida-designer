from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator

from hetdesrun.models.repr_reference import ReproducibilityReference
from hetdesrun.models.wiring import WorkflowWiring
from hetdesrun.reference_context import (
    get_deepcopy_of_reproducibility_reference_context,
)
from hetdesrun.runtime.context import RuntimeExecutionContext


class ExecByIdBase(BaseModel):
    id: UUID  # noqa: A003
    wiring: WorkflowWiring | None = Field(
        None,
        description="The wiring to be used. "
        "If no wiring is provided the stored test wiring will be used.",
    )
    resolved_reproducibility_references: ReproducibilityReference = Field(
        default_factory=get_deepcopy_of_reproducibility_reference_context,
        description="Resolved references to information needed to reproduce an execution result."
        "The provided data can be used to replace data that would usually be produced at runtime.",
    )
    run_pure_plot_operators: bool = Field(
        False, description="Whether pure plot components should be run."
    )
    runtime_execution_context: RuntimeExecutionContext = Field(
        default_factory=RuntimeExecutionContext,
        description=(
            "Settings provided by the execution request that may influence"
            " execution and can be accessed in component code."
        ),
    )

    @field_validator("runtime_execution_context", mode="before")
    @classmethod
    def handle_null_fields(cls, v: Any) -> Any:
        """Allow to initialize explicitely with null/None

        Fields should not be optional / nullable typed and always be proper objects,
        but the case that null / None is provided should just call the default_factory
        and provide the default values.
        """
        if v is None:
            return {}  # will be passed to default_factory
        return v


class ExecByIdInput(ExecByIdBase):
    job_id: UUID = Field(
        default_factory=uuid4,
        description=(
            "Id to identify an individual execution job, will be generated if it is not provided."
        ),
    )


class ExecLatestByGroupIdInput(BaseModel):
    """Payload for execute-latest kafka endpoint

    WARNING: Even when this input is not changed, the execution response might change if a new
    latest transformation revision exists.

    WARNING: The inputs and outputs may be different for different revisions. In such a case,
    executing the last revision with the same input as before will not work, but will result in
    errors.

    The latest transformation will be determined by the released_timestamp of the released revisions
    of the revision group which are stored in the database.

    This transformation will be loaded from the DB and executed with the wiring sent with this
    payload.
    """

    revision_group_id: UUID
    wiring: WorkflowWiring
    resolved_reproducibility_references: ReproducibilityReference = Field(
        default_factory=get_deepcopy_of_reproducibility_reference_context,
        description="Resolved references to information needed to reproduce an execution result."
        "The provided data can be used to replace data that would usually be produced at runtime.",
    )
    run_pure_plot_operators: bool = Field(
        False, description="Whether pure plot components should be run."
    )
    job_id: UUID = Field(
        default_factory=uuid4,
        description="Optional job id, that can be used to track an execution job.",
    )
    runtime_execution_context: RuntimeExecutionContext = Field(
        default_factory=RuntimeExecutionContext,
        description=(
            "Settings provided by the execution request that may influence"
            " execution and can be accessed in component code."
        ),
    )

    @field_validator("runtime_execution_context", mode="before")
    @classmethod
    def handle_null_fields(cls, v: Any) -> Any:
        """Allow to initialize explicitely with null/None

        Fields should not be optional / nullable typed and always be proper objects,
        but the case that null / None is provided should just call the default_factory
        and provide the default values.
        """
        if v is None:
            return {}  # will be passed to default_factory
        return v

    def to_exec_by_id(self, id: UUID) -> ExecByIdInput:  # noqa: A002
        return ExecByIdInput(
            id=id,
            wiring=self.wiring,
            run_pure_plot_operators=self.run_pure_plot_operators,
            job_id=self.job_id,
            runtime_execution_context=self.runtime_execution_context,
            resolved_reproducibility_references=self.resolved_reproducibility_references,
        )

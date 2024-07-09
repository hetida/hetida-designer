from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from hetdesrun.models.repr_reference import ReproducibilityReference
from hetdesrun.models.wiring import WorkflowWiring
from hetdesrun.reference_context import (
    get_deepcopy_of_reproducibility_reference_context,
)


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


class ExecByIdInput(ExecByIdBase):
    job_id: UUID = Field(
        default_factory=uuid4,
        description=(
            "Id to identify an individual execution job, "
            "will be generated if it is not provided."
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
    run_pure_plot_operators: bool = Field(
        False, description="Whether pure plot components should be run."
    )
    job_id: UUID = Field(
        default_factory=uuid4,
        description="Optional job id, that can be used to track an execution job.",
    )

    def to_exec_by_id(self, id: UUID) -> ExecByIdInput:  # noqa: A002
        return ExecByIdInput(
            id=id,
            wiring=self.wiring,
            run_pure_plot_operators=self.run_pure_plot_operators,
            job_id=self.job_id,
        )

from typing import Any, Self
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, model_validator

from hetdesrun.models.repr_reference import ReproducibilityReference
from hetdesrun.models.revision_selection import RevisionSelection, validate_revision_selection
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


class ExecByRevisionGroupIdInput(BaseModel):
    """Common payload for executing a revision selected from a revision group

    WARNING: Even when this input is not changed, the execution response might change if
    another revision is selected, e.g. because a new revision was released.

    WARNING: The inputs and outputs may be different for different revisions. In such a case,
    executing another revision with the same input as before will not work, but will result in
    errors.

    The selected transformation revision will be loaded from the DB and executed with the wiring
    sent with this payload.
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
    include_deprecated: bool = Field(
        False,
        description="Whether deprecated (DISABLED) revisions may be selected for execution.",
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


class ExecLatestByGroupIdInput(ExecByRevisionGroupIdInput):
    """Payload for executing the latest revision of a revision group

    WARNING: Even when this input is not changed, the execution response might change if a new
    latest transformation revision exists.

    WARNING: The inputs and outputs may be different for different revisions. In such a case,
    executing the latest revision with the same input as before will not work, but will result in
    errors.

    The latest transformation will be determined by the released_timestamp of the released revisions
    of the revision group which are stored in the database.

    This transformation will be loaded from the DB and executed with the wiring sent with this
    payload.
    """

    @model_validator(mode="before")
    @classmethod
    def no_drafts(cls, data: Any) -> Any:
        """Reject include_drafts instead of silently ignoring it"""
        if isinstance(data, dict) and data.get("include_drafts", False):
            validate_revision_selection(RevisionSelection.LATEST, include_drafts=True)
        return data


class ExecHighestByGroupIdInput(ExecByRevisionGroupIdInput):
    """Payload for executing the highest revision of a revision group

    WARNING: Even when this input is not changed, the execution response might change if a new
    highest transformation revision exists.

    WARNING: The inputs and outputs may be different for different revisions. In such a case,
    executing the highest revision with the same input as before will not work, but will result
    in errors.

    The highest transformation will be determined by semantic versioning of the version tags of the
    released revisions of the revision group which are stored in the database. Revisions whose
    version tag is not a semantic version are ignored.

    This transformation will be loaded from the DB and executed with the wiring sent with this
    payload.
    """

    include_drafts: bool = Field(
        False,
        description="Whether DRAFT revisions may be selected for execution.",
    )


class ExecByRevisionGroupIdKafkaInput(ExecHighestByGroupIdInput):
    """Payload of Kafka messages for executing the latest / highest revision of a revision group

    See ExecLatestByGroupIdInput and ExecHighestByGroupIdInput.
    """

    by: RevisionSelection = Field(
        RevisionSelection.LATEST,
        description=(
            "Whether to execute the latest revision (by release timestamp) or the highest"
            " revision (by semantic versioning of the version tags). Drafts can only be included"
            " for the highest revision."
        ),
    )

    @model_validator(mode="after")
    def drafts_only_for_highest(self) -> Self:
        validate_revision_selection(self.by, self.include_drafts)
        return self

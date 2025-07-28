# noqa: A005
from typing import Self
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator

from hetdesrun.models.code import NonEmptyValidStr, ShortNonEmptyValidStr
from hetdesrun.persistence.models.io import OperatorInput, OperatorOutput, Position
from hetdesrun.utils import State, Type


class Operator(BaseModel):
    """Represents components or workflows within a workflow.

    Contains all information about the transformation revision needed for display in the workflow as
    well as the id, so that the transformation itself can be loaded if more information is needed.

    Note: Only released transformation revisions can be used as operators in a workflow.
    """

    id: UUID = Field(default_factory=uuid4)  # noqa: A003
    revision_group_id: UUID = Field(default_factory=uuid4)
    name: NonEmptyValidStr
    type: Type  # noqa: A003
    state: State
    version_tag: ShortNonEmptyValidStr
    transformation_id: UUID
    inputs: list[OperatorInput]
    outputs: list[OperatorOutput]
    position: Position

    @model_validator(mode="after")
    def is_not_draft(self) -> Self:
        state = self.state
        type_ = self.type

        if state is State.DRAFT and type_ is not Type.COMPONENT:
            operator_id = self.id

            raise ValueError(
                f"Only released components/workflows or draft components"
                " can be dragged into a workflow! "
                f"Operator with id {operator_id} of type {type_}"
                f" has state {state} "
            )
        return self

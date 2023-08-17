from uuid import UUID, uuid4

from pydantic import BaseModel, Field, root_validator

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

    @root_validator()
    def is_not_draft(cls, values: dict) -> dict:
        try:
            state = values["state"]
        except KeyError as e:
            raise ValueError(
                "Cannot validate that operator is not DRAFT if the attribute 'state' is missing!"
            ) from e
        if state == State.DRAFT:
            try:
                operator_id = values["id"]
                type_ = values["type"]
            except KeyError as e:
                raise ValueError(
                    "Cannot provide information for which operator validation has failed "
                    "if any of the attributes 'id', 'type' is missing!"
                ) from e
            raise ValueError(
                f"Only released components/workflows can be dragged into a workflow! "
                f"Operator with id {operator_id} of type {type_}"
                f" has state {state} "
            )
        return values

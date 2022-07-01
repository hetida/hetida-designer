from typing import List
from uuid import UUID, uuid4

# pylint: disable=no-name-in-module
from pydantic import BaseModel, Field, root_validator

from hetdesrun.models.code import NonEmptyValidStr, ShortNonEmptyValidStr

from hetdesrun.utils import State, Type

from hetdesrun.persistence.models.io import Position, Connector


class Operator(BaseModel):
    """Represents components or workflows within a workflow.

    Contains all information about the transformation revision needed for display in the workflow as
    well as the id, so that the transformation itself can be loaded if more information is needed.

    Note: Only released transformation revisions can be used as operators in a workflow.
    """

    id: UUID = Field(default_factory=uuid4)
    revision_group_id: UUID = Field(default_factory=uuid4)
    name: NonEmptyValidStr
    type: Type
    state: State
    version_tag: ShortNonEmptyValidStr
    transformation_id: UUID
    inputs: List[Connector]
    outputs: List[Connector]
    position: Position

    # pylint: disable=no-self-argument,no-self-use
    @root_validator()
    def is_not_draft(cls, values: dict) -> dict:
        if values["state"] == State.DRAFT:
            raise ValueError(
                f"Only released components/workflows can be dragged into a workflow! "
                f'Operator with id {values["id"]} of type {values["type"]}'
                f' has state {values["state"]} '
            )
        return values

# noqa: A005
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from hetdesrun.models.code import NonEmptyValidStr, ShortNonEmptyValidStr
from hetdesrun.persistence.models.io import OperatorInput, OperatorOutput, Position
from hetdesrun.utils import State, Type


class Operator(BaseModel):
    """Represents components or workflows within a workflow.

    Contains all information about the transformation revision needed for display in the workflow as
    well as the id, so that the transformation itself can be loaded if more information is needed.
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

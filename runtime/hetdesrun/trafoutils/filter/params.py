from uuid import UUID

from pydantic import BaseModel, Field

from hetdesrun.models.code import NonEmptyValidStr, ValidStr
from hetdesrun.utils import State, Type


class FilterParams(BaseModel):
    type: Type | None = Field(  # noqa: A003
        None, description="Filter for specified type"
    )
    state: State | None = Field(None, description="Filter for specified state")
    category: ValidStr | None = Field(None, description="Filter for specified category")
    categories: list[ValidStr] | None = Field(
        None, description="Filter for several specified categories"
    )
    category_prefix: str | None = Field(
        None,
        description="Category prefix that must be matched exactly (case-sensitive).",
    )
    revision_group_id: UUID | None = Field(
        None, description="Filter for specified revision group id"
    )
    ids: list[UUID] | None = Field(None, description="Filter for specified list of ids")
    names: list[NonEmptyValidStr] | None = Field(
        None, description="Filter for specified list of names"
    )
    include_deprecated: bool = Field(
        True,
        description=(
            "Set to False to omit transformation revisions with state DISABLED "
            "this will not affect included dependent transformation revisions"
        ),
    )
    include_dependencies: bool = Field(
        False,
        description=(
            "Set to True to additionally get those transformation revisions "
            "that the selected ones depend on"
        ),
    )
    unused: bool = Field(
        False,
        description=(
            "Set to True to obtain only those transformation revisions that are "
            "not contained in workflows that do not have the state DISABLED."
        ),
    )

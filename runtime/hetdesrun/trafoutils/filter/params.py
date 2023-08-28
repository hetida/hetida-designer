from uuid import UUID

from pydantic import BaseModel, Field

from hetdesrun.models.code import NonEmptyValidStr, ValidStr
from hetdesrun.utils import State, Type


class FilterParams(BaseModel):
    type: Type | None = Field(  # noqa: A003
        None, description="Filter for specified types."
    )
    state: State | None = Field(None, description="Filter for specified state.")
    categories: list[ValidStr] | None = Field(
        None, alias="category", description="Filter for specified list of categories."
    )
    category_prefix: ValidStr | None = Field(
        None,
        description="Category prefix that must be matched exactly (case-sensitive).",
    )
    revision_group_id: UUID | None = Field(
        None, description="Filter for specified revision group ids."
    )
    ids: list[UUID] | None = Field(
        None, alias="id", description="Filter for specified list of ids."
    )
    names: list[NonEmptyValidStr] | None = Field(
        None, alias="name", description="Filter for specified list of names."
    )
    include_deprecated: bool = Field(
        True,
        description=(
            "Set to False to omit transformation revisions with state DISABLED "
            "this will not affect included dependent transformation revisions."
        ),
    )
    include_dependencies: bool = Field(
        False,
        description=(
            "Set to True to additionally get those transformation revisions "
            "that the selected ones depend on."
        ),
    )
    unused: bool = Field(
        False,
        description=(
            "Set to True to obtain only those transformation revisions that are "
            "not contained in workflows that do not have the state DISABLED."
        ),
    )

    class Config:
        allow_population_by_field_name = True

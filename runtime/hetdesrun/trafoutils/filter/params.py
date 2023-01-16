from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from hetdesrun.models.code import NonEmptyValidStr, ValidStr
from hetdesrun.utils import State, Type


class FilterParams(BaseModel):
    # pylint: disable=too-many-instance-attributes
    type: Optional[Type] = Field(None, description="Filter for specified type")
    state: Optional[State] = Field(None, description="Filter for specified state")
    category: Optional[ValidStr] = Field(
        None, description="Filter for specified category"
    )
    categories: Optional[List[ValidStr]] = Field(
        None, description="Filter for several specified categories"
    )
    category_prefix: Optional[str] = Field(
        None,
        description="Category prefix that must be matched exactly (case-sensitive).",
    )
    revision_group_id: Optional[UUID] = Field(
        None, description="Filter for specified revision group id"
    )
    ids: Optional[List[UUID]] = Field(
        None, description="Filter for specified list of ids"
    )
    names: Optional[List[NonEmptyValidStr]] = Field(
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

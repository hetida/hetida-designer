"""Filter classes for adapter data selection"""

from typing import Optional
from pydantic import BaseModel, Field  # pylint: disable=no-name-in-module


class FilteredSource(BaseModel):
    source_id: Optional[str] = Field(None, alias="source_id")
    filters: dict = Field({}, description="actual set filters", example={})


class FilteredSink(BaseModel):
    sink_id: Optional[str] = Field(None, alias="sink_id")
    filters: dict = Field({}, description="actual set filters", example={})

"""Filter classes for adapter data selection"""

from typing import Literal, Optional

from pydantic import BaseModel, Field  # pylint: disable=no-name-in-module


class FilteredSource(BaseModel):
    ref_id: Optional[str] = None
    ref_id_type: Optional[Literal["SOURCE", "SINK", "THINGNODE"]] = None
    ref_key: Optional[str] = None
    type: Optional[str] = None

    filters: dict = Field({}, description="actual set filters", example={})


class FilteredSink(BaseModel):
    ref_id: Optional[str] = None
    ref_id_type: Optional[Literal["SOURCE", "SINK", "THINGNODE"]] = None
    ref_key: Optional[str] = None
    type: Optional[str] = None

    filters: dict = Field({}, description="actual set filters", example={})

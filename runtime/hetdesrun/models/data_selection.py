"""Source and sink classes for adapter data selection"""

from typing import Literal

from pydantic import BaseModel, Field


class FilteredSource(BaseModel):
    ref_id: str | None = None
    ref_id_type: Literal["SOURCE", "SINK", "THINGNODE"] | None = None
    ref_key: str | None = None
    type: str | None = None  # noqa: A003

    filters: dict[str, str] = Field({}, description="actually set filters", example={})


class FilteredSink(BaseModel):
    ref_id: str | None = None
    ref_id_type: Literal["SOURCE", "SINK", "THINGNODE"] | None = None
    ref_key: str | None = None
    type: str | None = None  # noqa: A003

    filters: dict[str, str] = Field({}, description="actually set filters", example={})

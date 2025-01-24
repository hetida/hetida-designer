"""Source and sink classes for adapter data selection"""

from typing import Any, Literal

from pydantic import BaseModel, Field


class FilteredSource(BaseModel):
    ref_id: str | None = None
    ref_id_type: Literal["SOURCE", "SINK", "THINGNODE"] | None = None
    ref_key: str | None = None
    type: str | None = None  # noqa: A003

    # we must allow Any as filter value here, since InputWirings for Component Adapter
    # sinks need to get the actual value as Python object isntead of a str in order
    # to avoid unnecessary serializing/deserializing between trafo output and
    # component adapter sink execution.
    filters: dict[str, str | Any] = Field({}, description="actually set filters", example={})


class FilteredSink(BaseModel):
    ref_id: str | None = None
    ref_id_type: Literal["SOURCE", "SINK", "THINGNODE"] | None = None
    ref_key: str | None = None
    type: str | None = None  # noqa: A003

    filters: dict[str, str] = Field({}, description="actually set filters", example={})

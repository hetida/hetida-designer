"""(Pydantic) Models for ingoing / outgoing data"""

from typing import Literal, Protocol


class FilteredSource(Protocol):
    """Support for type annotation of custom adapter runtime implementations"""

    ref_id: str | None
    ref_id_type: Literal["SOURCE", "SINK", "THINGNODE"] | None
    ref_key: str | None
    type: str | None  # noqa: A003
    filters: dict


class FilteredSink(Protocol):
    """Support for type annotation of custom adapter runtime implementations"""

    ref_id: str | None
    ref_id_type: Literal["SOURCE", "SINK", "THINGNODE"] | None
    ref_key: str | None
    type: str | None  # noqa: A003
    filters: dict

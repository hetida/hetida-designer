"""(Pydantic) Models for ingoing / outgoing data"""

from typing import Literal, Optional, Protocol


class FilteredSource(Protocol):
    """Support for type annotation of custom adapter runtime implementations"""

    ref_id: Optional[str]
    ref_id_type: Optional[Literal["SOURCE", "SINK", "THINGNODE"]]
    ref_key: Optional[str]
    type: Optional[str]
    filters: dict


class FilteredSink(Protocol):
    """Support for type annotation of custom adapter runtime implementations"""

    ref_id: Optional[str]
    ref_id_type: Optional[Literal["SOURCE", "SINK", "THINGNODE"]]
    ref_key: Optional[str]
    type: Optional[str]
    filters: dict

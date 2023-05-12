"""(Pydantic) Models for ingoing / outgoing data"""
import re
from typing import Any, Literal, Protocol

from pydantic import ConstrainedStr

RESERVED_FILTER_KEY = ["from", "to", "id"]


class FilterKey(ConstrainedStr):
    min_length = 1
    regex = re.compile(r"^[a-zA-Z]\w+$", flags=re.ASCII)


class FilteredSource(Protocol):
    """Support for type annotation of custom adapter runtime implementations"""

    ref_id: str | None
    ref_id_type: Literal["SOURCE", "SINK", "THINGNODE"] | None
    ref_key: str | None
    type: str | None  # noqa: A003
    filters: dict[FilterKey, Any]


class FilteredSink(Protocol):
    """Support for type annotation of custom adapter runtime implementations"""

    ref_id: str | None
    ref_id_type: Literal["SOURCE", "SINK", "THINGNODE"] | None
    ref_key: str | None
    type: str | None  # noqa: A003
    filters: dict[FilterKey, Any]

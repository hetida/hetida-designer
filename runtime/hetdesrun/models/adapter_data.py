from enum import StrEnum


class RefIdType(StrEnum):
    """Reference Id type as required for some adapters (notably generic rest adapter)"""

    SOURCE = "SOURCE"
    SINK = "SINK"
    THINGNODE = "THINGNODE"

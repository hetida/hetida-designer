from enum import Enum


class RefIdType(str, Enum):
    """Reference Id type as required for some adapters (notably generic rest adapter)"""

    SOURCE = "SOURCE"
    SINK = "SINK"
    THINGNODE = "THINGNODE"


class DataType(str, Enum):
    INT = "int"
    FLOAT = "float"
    STRING = "string"
    BOOLEAN = "boolean"
    ANY = "any"

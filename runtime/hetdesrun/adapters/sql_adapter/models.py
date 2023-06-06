from typing import Literal
from enum import Enum

from pydantic import BaseModel, Field, validator

from hetdesrun.adapters.generic_rest.external_types import ExternalType
from hetdesrun.adapters.sql_adapter.utils import get_configured_dbs_by_key
from hetdesrun.adapters.sql_adapter.config import SQLAdapterDBConfig


class WriteTableMode(str, Enum):
    APPEND = "APPEND"
    REPLACE = "REPLACE"

    @classmethod
    def from_table_type_str(
        cls, table_type: Literal["append_table", "replace_table"]
    ) -> "WriteTableMode":
        if table_type == "append_table":
            return cls.APPEND

        if table_type == "replace_table":
            return cls.REPLACE

    """
    def to_table_type_str(self):
        if self is WriteTableMode.APPEND:
            return "append_table"

        if self is WriteTableMode.REPLACE:
            return "replace_table"

        raise TypeError("Unhandled WriteTableMode")
    """


class WriteTable(BaseModel):
    db_key: str
    write_mode: WriteTableMode
    table_name: str

    @validator("db_key")
    def db_key_is_configured(cls, v):
        if v not in get_configured_dbs_by_key():
            return ValueError(
                f"DB key {v} is not configured in sql adapter configuration"
            )
        return v

    @classmethod
    def from_sink_id(cls, id: str):
        """Create WriteTable from sink id

        Raises pydantic ValidationError if id is somehow invalid.
        """
        params: dict = {}
        id_split = sink_id.split("/", 2)

        params["db_key"] = id_split[0]
        if len(id_split) > 1:
            params["write_mode"] = WriteTableMode.from_table_type_str(id_split[1])

        if len(id_split) > 2:
            params["table_name"] = id_split[2]

        return cls(**params)

    @property
    def sink_id(self) -> str:
        return (
            self.db_key
            + "/"
            + self.write_mode.to_table_type_str()
            + "/"
            + self.table_name
        )

    @property
    def db_config(self):
        return get_configured_dbs_by_key(self.db_key)


class InfoResponse(BaseModel):
    id: str  # noqa: A003
    name: str
    version: str


class StructureThingNode(BaseModel):
    id: str  # noqa: A003
    parentId: str | None = None
    name: str
    description: str


class SQLAdapterStructureSource(BaseModel):
    id: str  # noqa: A003
    thingNodeId: str
    name: str
    type: ExternalType = ExternalType.DATAFRAME  # noqa: A003
    visible: Literal[True] = True
    path: str = Field(..., description="Display path used in Designer Frontend")
    metadataKey: str | None = None
    filters: dict[str, dict] | None = {}


class SQLAdapterStructureSink(BaseModel):
    id: str  # noqa: A003
    thingNodeId: str
    name: str
    type: ExternalType = ExternalType.DATAFRAME  # noqa: A003
    visible: Literal[True] = True
    path: str = Field(..., description="Display path used in Designer Frontend")
    metadataKey: str | None = None
    filters: dict[str, dict] | None = {}


class MultipleSourcesResponse(BaseModel):
    resultCount: int
    sources: list[SQLAdapterStructureSource]


class MultipleSinksResponse(BaseModel):
    resultCount: int
    sinks: list[SQLAdapterStructureSink]


class StructureResponse(BaseModel):
    id: str  # noqa: A003
    name: str
    thingNodes: list[StructureThingNode]
    sources: list[SQLAdapterStructureSource]
    sinks: list[object]
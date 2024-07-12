from enum import Enum
from typing import Literal, cast

from pydantic import BaseModel, Field, validator

from hetdesrun.adapters.generic_rest.external_types import ExternalType
from hetdesrun.adapters.sql_adapter.config import SQLAdapterDBConfig
from hetdesrun.adapters.sql_adapter.utils import get_configured_dbs_by_key


class WriteTableMode(str, Enum):
    APPEND = "APPEND"
    REPLACE = "REPLACE"
    TIMSERIES_APPEND = "TIMESERIES_APPEND"

    @classmethod
    def from_table_type_str(
        cls, table_type: Literal["append_table", "replace_table", "appendable_ts_table"]
    ) -> "WriteTableMode":
        if table_type == "append_table":
            return cls.APPEND

        if table_type == "replace_table":
            return cls.REPLACE

        if table_type == "appendable_ts_table":  # noqa: RET503
            return cls.TIMSERIES_APPEND


def to_table_type_str(
    write_table_mode: WriteTableMode,
) -> Literal["append_table", "replace_table", "appendable_ts_table"]:
    if write_table_mode is WriteTableMode.APPEND:
        return "append_table"

    if write_table_mode is WriteTableMode.REPLACE:
        return "replace_table"

    if write_table_mode is WriteTableMode.TIMSERIES_APPEND:
        return "appendable_ts_table"

    raise TypeError("Unhandled WriteTableMode")


def to_if_exists_pandas_str(write_table_mode: WriteTableMode) -> str:
    if (
        write_table_mode is WriteTableMode.APPEND
        or write_table_mode is WriteTableMode.TIMSERIES_APPEND
    ):
        return "append"

    if write_table_mode is WriteTableMode.REPLACE:
        return "replace"

    raise TypeError("Unhandled WriteTableMode")


class WriteTable(BaseModel):
    db_key: str
    write_mode: WriteTableMode
    table_name: str

    @validator("db_key")
    def db_key_is_configured(cls, v: str) -> str:
        if v not in get_configured_dbs_by_key():
            raise ValueError(f"DB key {v} is not configured in sql adapter configuration")
        return v

    @classmethod
    def from_sink_id(cls, sink_id: str) -> "WriteTable":
        """Create WriteTable from sink id

        Raises pydantic ValidationError if id is somehow invalid.
        """
        params: dict = {}
        id_split = sink_id.split("/", 2)

        params["db_key"] = id_split[0]
        if len(id_split) > 1:
            write_mode_str: Literal["append_table", "replace_table", "appendable_ts_table"] = cast(
                Literal["append_table", "replace_table", "appendable_ts_table"],
                id_split[1],
            )
            params["write_mode"] = WriteTableMode.from_table_type_str(write_mode_str)

        if len(id_split) > 2:
            params["table_name"] = id_split[2]

        return cls(**params)

    @property
    def sink_id(self) -> str:
        return self.db_key + "/" + to_table_type_str(self.write_mode) + "/" + self.table_name

    @property
    def db_config(self) -> SQLAdapterDBConfig:
        return get_configured_dbs_by_key()[self.db_key]

    @property
    def pandas_if_exists_mode(self) -> str:
        return to_if_exists_pandas_str(self.write_mode)


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
    sinks: list[SQLAdapterStructureSink]

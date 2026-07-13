import functools

import pandas as pd
from pydantic import BaseModel, ConfigDict

from hetdesrun.adapters.sql_adapter.config import (
    SQLAdapterDBConfig,
    get_sql_adapter_config,
)
from hetdesrun.datatypes import PydanticMultiTimeseriesPandasDataFrame


class CorrectMultiTSFrame(BaseModel):
    multi_ts_frame: PydanticMultiTimeseriesPandasDataFrame

    model_config = ConfigDict(arbitrary_types_allowed=True)


def to_url_representation(path: str) -> str:
    """Convert path to a representation that can be used in urls/queries"""
    return path.replace("_", "-_-").replace("/", "__")


def from_url_representation(url_rep: str) -> str:
    """Reconvert url representation of path to actual path"""
    return url_rep.replace("__", "/").replace("-_-", "_")


@functools.cache
def get_configured_dbs_by_key() -> dict[str, SQLAdapterDBConfig]:
    return {
        configured_db.key: configured_db for configured_db in get_sql_adapter_config().sql_databases
    }


def is_allowed_dataframe_source_table(table_name: str, db_config: SQLAdapterDBConfig) -> bool:
    """Whether a table may be read as an ordinary dataframe source.

    Restricted by configuration: it must be in explicit_source_tables (if set), must not
    be ignored and must not be a timeseries table. This must be enforced at read time and
    not only when listing the offered sources.
    """
    return (
        (db_config.explicit_source_tables is None or table_name in db_config.explicit_source_tables)
        and table_name not in db_config.ignore_tables
        and table_name not in db_config.timeseries_tables
    )


def validate_multits_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Raises pydantic validation error if frame is not okay"""

    validated_multi_ts_frame = CorrectMultiTSFrame(multi_ts_frame=df).multi_ts_frame

    return validated_multi_ts_frame

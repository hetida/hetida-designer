import functools

import pandas as pd
from pydantic import BaseModel

from hetdesrun.adapters.sql_adapter.config import (
    SQLAdapterDBConfig,
    get_sql_adapter_config,
)
from hetdesrun.datatypes import PydanticMultiTimeseriesPandasDataFrame


class CorrectMultiTSFrame(BaseModel):
    multi_ts_frame: PydanticMultiTimeseriesPandasDataFrame


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


def validate_multits_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Raises pydantic validation error if frame is not okay"""

    validated_multi_ts_frame = CorrectMultiTSFrame(multi_ts_frame=df).multi_ts_frame

    return validated_multi_ts_frame

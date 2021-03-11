from typing import Any

import pandas as pd


def load_parquet(path: str, **kwargs: Any) -> pd.DataFrame:
    return pd.read_parquet(path, **kwargs)


def write_parquet(df: pd.DataFrame, path: str, **kwargs: Any) -> None:
    df.to_parquet(path, **kwargs)

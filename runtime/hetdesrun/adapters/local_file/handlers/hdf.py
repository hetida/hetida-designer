from typing import Any

import pandas as pd


def load_hdf(path: str, **kwargs: Any) -> pd.DataFrame:
    return pd.read_hdf(path, **kwargs)


def write_hdf(df: pd.DataFrame, path: str, **kwargs: Any) -> None:
    if "key" not in kwargs:
        kwargs["key"] = "default"
    df.to_hdf(path, **kwargs)

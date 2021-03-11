from typing import Any

import pandas as pd


def load_excel(path: str, **kwargs: Any) -> pd.DataFrame:
    return pd.read_excel(path, **kwargs)


def write_excel(df: pd.DataFrame, path: str, **kwargs: Any) -> None:
    df.to_excel(path, **kwargs)

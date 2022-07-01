import asyncio
from typing import Dict

import pandas as pd

from hetdesrun.adapters.generic_rest.load_framelike import load_framelike_data
from hetdesrun.models.data_selection import FilteredSource


async def load_single_dataframe_from_adapter(
    filtered_source: FilteredSource, adapter_key: str
) -> pd.DataFrame:
    return await load_framelike_data(
        [filtered_source],
        additional_params=[],
        adapter_key=adapter_key,
        endpoint="dataframe",
    )


async def load_dataframes_from_adapter(
    data_to_load: Dict[str, FilteredSource], adapter_key: str
) -> Dict[str, pd.DataFrame]:
    loaded_frames = await asyncio.gather(
        *[
            load_single_dataframe_from_adapter(filtered_source, adapter_key)
            for filtered_source in data_to_load.values()
        ]
    )
    return dict(zip(data_to_load.keys(), loaded_frames))
